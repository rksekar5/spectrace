# Design

## Context

See `proposal.md` for motivation and `specs/*/spec.md` for the behavioral contract.
The checkout was empty: there is no existing package, test suite, CLI, or data to
migrate. Python 3.12, pytest, Ruff, and build tools are already prepared in the
cloud environment. OpenSpec 1.14.1 has been initialized with the `spec-driven`
schema and six generated Codex skills under `.agents/skills`.

This document proposes an implementation; it does not authorize or contain one.
All implementation tasks remain unchecked until explicit user approval. This
planning change stays active and is not archived or synced into canonical specs
before the approved implementation and verification are complete.

## Goals / Non-Goals

**Goals:**

- Make every report association explainable by one explicit ID and a literal
  marker at a known source location.
- Separate parsing, mapping, and rendering so each failure can be tested without
  invoking the full CLI.
- Keep runtime dependencies and deployment small: a local standard-library Python
  application, with deterministic output and no execution of inspected code.

**Non-Goals:**

- Running pytest, measuring code coverage, proving requirement satisfaction, or
  interpreting test outcomes.
- Reproducing arbitrary pytest collection hooks, plugin behavior, aliases,
  inherited tests, dynamically generated tests, or individual parameter cases.
- Resolving OpenSpec MODIFIED/REMOVED/RENAMED deltas against a baseline; tracing
  scenario-level IDs; assigning or rewriting requirement IDs.
- Full CommonMark parsing, Markdown rendering, multiple simultaneous spec/test
  roots, repository-wide automatic discovery, or a persistent index.
- Network services, databases, frontend, external APIs, or LLM integration.

## Decisions

### 1. Use a small explicit annotation profile

Requirement headings use `### Requirement: [REQ-AUTH-001] Reject invalid passwords`.
The identifier is part of OpenSpec's ordinary requirement name, so its validators
and archive workflow can preserve it without a custom schema. IDs are globally
unique within the selected catalog and match `[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+`.

Test definitions use the literal decorator
`@pytest.mark.requirements("REQ-AUTH-001", "REQ-AUTH-002")`. The project's eventual
pytest configuration will register `requirements(*ids)` as a custom marker, so
real tests can use it under pytest's strict-marker mode. Tests in other projects
must register the marker in their own pytest configuration when executing pytest;
SpecTrace itself does not require registration or pytest at runtime.

Alternatives considered: comment annotations are difficult to bind unambiguously
to a definition; title-derived IDs break on edits; aliases and computed markers
require name or expression resolution. These are excluded from the first version.
IDs, marker spelling, and the discovery profile are explicit review assumptions,
not claims that unannotated OpenSpec documents already contain stable IDs.

### 2. Use static, independent parsing stages

The proposed pipeline is:

```text
spec root -> file discovery -> Markdown reader -> requirement catalog --+
                                                                       |
test root -> file discovery -> Python AST reader -> test references ----+
                                                                       v
                                                       resolve links and gaps
                                                                       |
                                                                       v
                                                      render Markdown -> CLI
```

Potential package boundaries, to be created only after approval:

| Module | Responsibility |
| --- | --- |
| `cli` | argparse interface, orchestration, diagnostics, exit status, output destination |
| `discovery` | bounded traversal, exclusions, sorting, root-relative source paths |
| `requirements` | OpenSpec document profile, IDs, block content, duplicates |
| `pytest_refs` | AST discovery, marker validation, test identities and locations |
| `mapping` | many-to-many joins, unknown references, gap and count calculation |
| `report` | deterministic Markdown rendering and cell escaping |
| `models` | small immutable records shared between stages |

Use `pathlib`/`os`, `re`, `ast`, `tokenize`, `dataclasses`, `argparse`, and
`importlib.metadata` from Python 3.12. Python test files are opened with
`tokenize.open` to honor encoding declarations. Use the Python 3.12 AST grammar;
newer syntax is an input error until explicitly supported. No module importing,
pytest collection, subprocess execution of input, or plugin loading is needed.

Alternative: asking pytest to collect would support more dynamic behavior, but it
executes user code and requires the inspected project's dependencies. It would
break the offline, static-analysis boundary and is not selected.

### 3. Parse a documented OpenSpec Markdown subset

Scan line by line while tracking level-two sections, the active requirement, code
fences, and HTML comments. Real headings are unindented ATX headings; the supported
requirement heading syntax is case-sensitive and does not use optional trailing
closing hashes. Fences may start with up to three spaces and at least three
backticks or tildes, with an optional info string. A closing fence must use the
same character, at least the opening length, and no non-whitespace suffix. Comment
delimiters are recognized outside code fences, and fence syntax inside comments
is ignored. An unclosed fence or comment is an input error.

Only `## Requirements` and `## ADDED Requirements` admit requirement blocks.
Description and scenario Markdown stays intact in the stored body; body boundaries
follow real level-one through level-three headings. Markdown formatting inside
titles is retained as literal source text for safe report rendering. This parser
extracts requirements; OpenSpec remains the authority for full spec validation.

Default to the canonical `openspec/specs` tree. A caller can explicitly select this
change's ADDED-only spec tree. Never combine pending change trees and canonical
specs automatically: that can double-count IDs or misrepresent removals. A strict
error on other delta operations avoids implementing an incomplete overlay engine.

Alternative: a full Markdown dependency would accept more dialect features but
adds a runtime dependency without improving the deliberately narrow contract.
Reassess if real documents need a broader profile after the first release.

### 4. Model source declarations rather than runtime tests

Records will contain:

| Record | Minimum data |
| --- | --- |
| Requirement | ID, title, body, root-relative path, heading line |
| Test definition | root-relative identifier, path, definition line, set of literal IDs |
| Diagnostic | reason, path, optional line/column, related duplicate location |
| Traceability result | complete catalog, discovered tests, resolved pairs, unknown pairs |

Visit only direct module-level definitions and direct methods of supported
top-level classes. Conditional/nested definitions, custom pytest discovery,
`__test__` overrides, inherited methods, and import rebinding are not interpreted.
An `async def` declaration is discoverable without claiming that an async plugin
will collect or execute it. A class defining either `__init__` or `__new__` is
excluded. Direct `pytest.fixture` decorators exclude test-like fixture functions.

Match the exact attribute chain `pytest.mark.requirements`; recognized marker
expressions outside a valid test decorator are errors, including usage inside
parameter-case marks. Do not inspect strings for marker syntax. Aliased names are
not recognized and create no link; the report's limitation and documentation must
make the supported spelling clear. Static syntax alone does not prove that the
name `pytest` will resolve to the real pytest module at runtime.

Test identifiers resemble pytest node IDs but are explicitly static, relative to
the selected test directory, and never include parametrization suffixes. Multiple
source definitions with the same identifier are an error rather than letting the
last definition win. Marker-line locations support input diagnostics; definition
lines are used in reports. Duplicate pairs are sets, so repeated markers cannot
inflate counts.

### 5. Distinguish declared links, unresolved references, and broken input

Build a dictionary keyed by requirement ID and join literal test ID sets against
it. Count distinct requirement/test pairs. A linked test is one with at least one
resolved pair; a test with only unknown IDs is discovered but not linked. Empty
test trees are valid, while a zero-requirement catalog is an input error.

| Condition | Report | Exit |
| --- | --- | --- |
| Valid input, all IDs resolve, no unlinked requirements | Complete | 0 |
| Unlinked requirements, default mode | Complete | 0 |
| Unlinked requirements with `--fail-on-unlinked` | Complete | 1 |
| Unknown references, regardless of flag | Complete | 1 |
| Usage, discovery, decoding, syntax, catalog, marker, or output error | None | 2 |

Input validation finishes before output is opened. Fail on the first error in
sorted file traversal and source order; duplicate diagnostics name both sites.
Error messages go to stderr with no traceback for expected user mistakes. Unknown
IDs remain reportable findings, rather than preventing useful mapping of valid IDs.

Alternative: treating every unlinked requirement as an error by default would make
the first inventory unnecessarily awkward; the explicit flag supports CI gates.
Calling a linked requirement covered would be a false claim, so no coverage
percentage or pass status is included.

### 6. Render safely and commit output only on success

Use a pure renderer with stable section order: title and limitations, summary,
requirement table, unlinked list, unknown-reference table. Sort IDs and test
identifiers lexicographically, format only input-relative paths with `/`, and
never include timestamps. Convert ampersands, angle brackets, pipes, and backticks
in source text to HTML entities, and collapse embedded CR/LF to spaces before
placing them into plain Markdown cells. Do not interpolate raw source as HTML or
links; locations are literal text.

For a file destination, reject source collisions, symlink destinations, and
directories before writing. Write the complete UTF-8 report to a temporary sibling
file, then replace the destination with `os.replace`; remove the temporary file
on failure. Do not create missing parent directories. This keeps the previous
report intact on parsing, writing, or replacement failures. Input roots and source
files are never modified. Concurrent mutation of source trees during a run is
outside the first version's guarantees.

### 7. Package a minimal offline CLI after approval

Use a `src/spectrace` layout and a `spectrace` console entry point with Python
`>=3.12`. Use a standard `pyproject.toml` build configuration with setuptools and
the existing `python -m build` tool. Declare no runtime package dependencies.
Keep pytest, Ruff, and build tools in development dependencies and document a
repeatable development installation. OpenSpec's Node installation remains a
separate authoring prerequisite, not a Python package dependency.

First acceptance is on Python 3.12 in this Linux environment. Prefer portable
standard-library APIs and path handling, but additional Python/platform support
is not asserted without a test matrix. No PyPI publication is part of this change.

## Assumptions and Edge Cases

| Assumption or edge case | Decision and acceptance contract |
| --- | --- |
| Existing OpenSpec heading has no ID | Fail and request an explicit annotation; ST-CAT-003 |
| Same ID appears in two files | Fail with both locations; ST-CAT-005 |
| Pending change modifies or removes a requirement | Reject; select canonical or ADDED-only specs; ST-CAT-002 |
| Missing test root versus existing empty root | Missing is invalid; empty means all requirements unlinked; ST-TST-001/005 |
| Marker contains an unknown ID | Report it and exit 1; ST-RPT-002 |
| Test name resembles an ID | No link; ST-TST-003 |
| Dynamic marker, class/module marker, parameter-case marker | Recognized unsupported usage is an error; ST-TST-004 |
| Marker uses an alias | No link; documented unsupported syntax; ST-TST-003 |
| Parametrized, skipped, or expected-failure test | One static definition; no execution claim; ST-TST-006 |
| Python module has side effects or unavailable imports | Parse without execution; ST-TST-005 |
| Hidden directory or encountered symlink | Skip; explicitly selected symlink root is invalid; ST-CAT-001 |
| Unclosed Markdown fence/comment or invalid source encoding | Fail without a report; ST-CAT-005/ST-TST-005 |
| Title/path contains Markdown delimiters | Escape into literal cells; ST-RPT-004 |
| Output equals an input or destination update fails | Fail without damaging inputs or an old report; ST-RPT-007 |

## Risks / Trade-offs

- Narrow static discovery can omit tests collected by custom pytest behavior →
  document the exact profile and never claim equivalence to pytest collection.
- A valid marker may refer to a trivial, skipped, or incorrect test → label it a
  declared link only; behavioral adequacy still requires review and test execution.
- Real-world OpenSpec documents may lack IDs or use broader Markdown → provide
  source-located errors and examples; do not silently manufacture identity.
- Handwritten annotations can drift → unknown-ID errors and an optional gap gate
  provide actionable feedback without automatic source rewrites.
- Large repositories increase parsing time → scan only explicit roots, exclude
  hidden trees, and keep joins linear in source size plus reference count; no
  caching or concurrency is justified for this small first version.
- All behavior is currently specified rather than implemented → validation in
  this PR verifies OpenSpec artifacts only, not application functionality.

## Validation Plan

After approval, translate every acceptance scenario into unit or CLI integration
tests with explicit `requirements` markers identifying the requirements exercised.
Use temporary fixture trees for malformed Markdown, syntax errors, empty inputs,
duplicate identities, marker shapes, unknown IDs, and report output behavior.
Include a subprocess CLI test with side-effecting test source and unavailable
imports to prove inspected sources are not executed. Assert full Markdown fixture
output and repeated byte equality, exit codes, stderr/stdout separation, and
preservation of existing files on errors.

Run pytest with strict marker registration, Ruff lint and format checks, an
isolated wheel build/install, and installed-command smoke checks. Any eventual
self-trace report is evidence of explicit associations only; passing the actual
tests is a separate result. During implementation, target this change's ADDED-only
specs explicitly; canonical specs remain empty until the approved archive step.

## Migration Plan

1. Review this proposal and its specification choices; obtain explicit approval
   before applying any implementation tasks.
2. Implement and verify in a later coding request using the OpenSpec apply workflow.
3. Review the implementation before merging or archiving. Use OpenSpec archive to
   establish canonical specs only after implementation and verification are complete.
4. There is no stored application data to migrate. Before publication, rollback is
   a normal revert of the relevant commits; source documents are never rewritten
   by SpecTrace itself.
