# Tasks

**Approval gate:** These are future implementation tasks. The user has requested
specifications only and has not approved implementation. Do not start the apply
workflow, create application code or tests, or mark tasks complete until explicit
approval arrives in a later request.

## 1. Python package and development tooling

- [ ] 1.1 Create the `src/spectrace` package, standard `pyproject.toml`, Python 3.12 requirement, and console entry point with no runtime dependencies; verify editable installation and import from outside the checkout (ST-RPT-005).
- [ ] 1.2 Configure pytest strict markers with `requirements(*ids)` and Ruff for Python 3.12; verify an initial package/entry-point test runs with its explicit requirement marker and Ruff accepts the skeleton (ST-TST-002, ST-RPT-005).
- [ ] 1.3 Document the development install and approval-based OpenSpec workflow; verify the installation commands in a clean Python 3.12 environment and keep OpenSpec outside Python runtime dependencies.

## 2. Specification discovery and requirement catalog

- [ ] 2.1 Implement bounded file discovery and source-location records; verify tests for single files, nested `spec.md` trees, ignored non-spec files, hidden directories, symlinks, and missing/unreadable roots (ST-CAT-001, ST-CAT-005).
- [ ] 2.2 Implement the supported section/heading scanner and body extraction; verify canonical and ADDED-only inputs, scenario preservation, fences with info strings, HTML comments, body boundaries, CRLF normalization, and rejected unsupported delta sections (ST-CAT-002, ST-CAT-004).
- [ ] 2.3 Validate explicit IDs, titles, bodies, uniqueness, encoding, closed fences/comments, and nonempty catalogs; verify source-located diagnostics and no partial results for each invalid-input scenario (ST-CAT-003, ST-CAT-004, ST-CAT-005).
- [ ] 2.4 Document the ID grammar, supported Markdown profile, and selecting canonical versus ADDED-only specs; verify the documented samples with catalog tests and annotate those tests with the relevant ST-CAT IDs.

## 3. Static pytest source references

- [ ] 3.1 Implement source-encoding-aware AST discovery and static test identifiers; verify function/method/async discovery, single-file paths, fixture and constructor exclusions, unsupported nesting/inheritance, empty trees, and duplicate definition errors (ST-TST-001, ST-TST-005).
- [ ] 3.2 Extract and deduplicate literal function-level markers; verify multiple IDs/decorators, correct locations, and rejection of empty, dynamic, malformed, starred, keyword, module/class, helper, and parameter-case markers (ST-TST-002, ST-TST-004).
- [ ] 3.3 Add negative-reference and static-execution tests; verify names, comments, docstrings, aliases, and strings create no links, source side effects never execute, unavailable imports do not block analysis, and invalid Python/encoding fails (ST-TST-003, ST-TST-005).
- [ ] 3.4 Verify definition-level treatment of parametrized, skipped, and expected-failure tests; document the supported discovery and marker profile, including marker registration for real pytest runs, and verify documentation examples with marked tests (ST-TST-001 through ST-TST-006).

## 4. Link resolution and Markdown rendering

- [ ] 4.1 Implement many-to-many resolution and summary counts; verify deduplication, multiple tests per requirement, multiple requirements per test, tests without markers, unknown IDs, and the all-unlinked empty-test case (ST-RPT-001, ST-RPT-002, ST-RPT-003).
- [ ] 4.2 Render every required report section and source location; verify a complete expected Markdown fixture, empty gap sections, escaping, stable sorting, relative paths, LF encoding, and repeat-run byte equality (ST-RPT-003, ST-RPT-004).
- [ ] 4.3 Document an example report with linked, unlinked, and unknown entries and the static-analysis limitation; verify the example against renderer output and assert that the report never presents link counts as executed coverage (ST-RPT-002, ST-RPT-003).

## 5. CLI behavior and report persistence

- [ ] 5.1 Wire the `report` subcommand, input defaults, explicit roots, help, and version; verify subprocess tests from both project and empty directories, stdout output, and no dependency on inspected-project imports or external services (ST-RPT-005, ST-TST-005).
- [ ] 5.2 Implement exit status and stderr rules; verify default gaps, strict gaps, unknown references, all-linked success, invalid arguments/input, and status-2 precedence with no partial report (ST-RPT-006).
- [ ] 5.3 Implement complete rendering before output and atomic file replacement; verify stdout/file equivalence, `--output -`, status-1 file reports, collision/symlink/directory rejection, missing parents, simulated write/replace errors, and preservation of existing files (ST-RPT-007).
- [ ] 5.4 Document the CLI flags, exit-code table, default paths, failure diagnostics, and offline runtime; execute the documented commands against temporary examples and verify exact statuses and output destinations (ST-RPT-005 through ST-RPT-007).

## 6. Integrated acceptance and packaging

- [ ] 6.1 Run the full marked pytest suite and Ruff lint/format checks; verify every acceptance scenario has an executed test and every explicit ST-CAT/ST-TST/ST-RPT reference resolves, recording passed, failed, and skipped outcomes separately.
- [ ] 6.2 Build an sdist and wheel, install the wheel into a clean Python 3.12 environment, and verify the installed CLI on a representative many-to-many fixture with one unlinked requirement and one unknown reference; confirm expected Markdown and exit codes without runtime third-party packages.
- [ ] 6.3 Run the implemented tool against this change's ADDED-only specs and the real marked test suite, then review the report alongside actual pytest results; verify that any claimed association is explicit and that link presence is never treated as evidence of passing tests.

## Workflow follow-up

- Keep this planning change unarchived and its implementation tasks unchecked until
  the user explicitly approves implementation.
- After the later implementation is complete and reviewed, archive through the
  OpenSpec workflow to establish canonical specs and validate the archived result.
- Merging, release publication, and package publication are separate actions and
  are not part of this specification-only request.
