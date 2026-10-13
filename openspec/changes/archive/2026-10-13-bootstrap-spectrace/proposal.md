# Proposal

## Why

Requirements and automated tests drift apart when their relationship exists only
in memory or naming conventions. SpecTrace will make those links explicit and
produce a reviewable Markdown inventory of requirements with and without linked
tests, without claiming that a link proves correctness or passing tests.

## What Changes

- Define a Python 3.12 command, `spectrace report`, for local OpenSpec documents
  and Python pytest sources.
- Read requirement blocks with explicit, stable identifiers from OpenSpec
  Markdown; reject missing or ambiguous identifiers instead of inventing them.
- Read literal `@pytest.mark.requirements("REQ-ID", ...)` decorators statically;
  never import tests, run pytest collection, or infer references from test names.
- Build a many-to-many mapping, list requirements without linked tests, and flag
  references to unknown identifiers.
- Specify deterministic Markdown reports and exit codes suitable for local use
  and CI, including an opt-in failure when requirements are unlinked.
- Initialize Fission AI OpenSpec with Codex skills and create this proposal,
  acceptance specifications, design, and unchecked implementation tasks.

**Approval boundary:** This change delivers planning artifacts and OpenSpec
tooling configuration only. Application code, packaging, fixtures, tests, and CI
implementation wait for explicit user approval in a later request.

## Capabilities

### New Capabilities

- `requirement-catalog`: Discover OpenSpec spec files and extract uniquely
  identified requirements with source locations and deterministic validation.
- `pytest-references`: Discover conventional pytest test definitions and extract
  only explicit literal requirement markers without executing Python code.
- `traceability-report`: Resolve references, identify unlinked requirements, and
  expose deterministic Markdown reporting and CLI failure behavior.

### Modified Capabilities

None. The repository has no existing application or canonical specifications.

## Impact

The eventual implementation will add a small `src/` Python package, console entry
point, pytest suite, Ruff configuration, and user documentation. The proposed
runtime uses only the Python standard library; pytest and Ruff are development
tools. OpenSpec is a Node-based authoring tool, not a SpecTrace runtime dependency.
No database, frontend, external API, LLM integration, or network access is needed
to run SpecTrace. Existing OpenSpec documents without stable IDs will need an
explicit ID annotation before being traced; SpecTrace will never rewrite them.

Initial review assumptions are literal requirement IDs in headings, function-level
pytest markers, a single selected spec tree per invocation, and static links at
test-definition granularity. Detailed boundaries and alternatives are in
`design.md`; these choices remain subject to specification review.
