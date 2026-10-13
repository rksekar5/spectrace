# Traceability Report

## Purpose

Turn explicit requirement-to-test references into a reviewable Markdown report
with reliable gap detection, deterministic output, and useful command exit codes.

## ADDED Requirements

### Requirement: [ST-RPT-001] Resolve many-to-many explicit links

SpecTrace SHALL map each catalog ID to all distinct supported test identifiers
that explicitly reference it. ID comparison SHALL be exact. Requirements with no
resolved reference SHALL be labeled `UNLINKED`; requirements with at least one
SHALL be labeled `LINKED`. It SHALL NOT infer links from similarity or source names.

#### Scenario: Build a many-to-many map

- **WHEN** `test_a` references `REQ-A` and `REQ-B`, `test_b` references `REQ-A`,
  and the catalog also contains `REQ-C`
- **THEN** `REQ-A` maps to both tests, `REQ-B` maps only to `test_a`, and `REQ-C`
  is `UNLINKED`
- **AND** there are three distinct resolved links

#### Scenario: Test discovery does not imply traceability

- **WHEN** supported tests exist but none has an accepted requirement marker
- **THEN** all catalog requirements are `UNLINKED` and the resolved-link count is zero

### Requirement: [ST-RPT-002] Expose unresolved references

Every distinct test-and-ID pair whose ID is absent from the catalog SHALL appear
as an unknown reference with its test source location. Unknown references SHALL
NOT create catalog entries, contribute to resolved-link counts, or disappear
silently. Valid references on the same test SHALL still resolve, and the full
report SHALL be generated with exit status 1.

#### Scenario: Mixed known and unknown IDs

- **WHEN** one test references catalog ID `REQ-A` and absent ID `REQ-TYPO`
- **THEN** the report links `REQ-A`, lists `REQ-TYPO` under unknown references,
  and exits with status 1 even without a strictness flag

#### Scenario: Deduplicate unknown references

- **WHEN** a test repeats an unknown ID in multiple accepted markers
- **THEN** its unknown test-and-ID pair is reported and counted once

### Requirement: [ST-RPT-003] Produce a complete Markdown report

The report SHALL include a title, the static-analysis limitation, summary counts,
a row for every requirement, an unlinked-requirement list, and an unknown-reference
table. Requirement rows SHALL contain ID, title, specification location, linked
test identifiers with source lines, and LINKED/UNLINKED status. Empty gap sections
SHALL explicitly say `None`.

#### Scenario: Report a known inventory

- **WHEN** three requirements map to two discovered tests with two linked
  requirements, one unlinked requirement, three resolved links, and no unknown IDs
- **THEN** the summary shows requirements 3, linked requirements 2, unlinked
  requirements 1, discovered tests 2, linked tests 2, resolved links 3, and unknown
  references 0
- **AND** all three requirements appear in the main table

#### Scenario: Make the static limitation visible

- **WHEN** any valid report is generated, including one where every requirement is linked
- **THEN** it states that links are declared source associations and do not prove
  collection, execution, passing tests, or behavioral coverage
- **AND** it does not label requirements as covered, tested, or passing

#### Scenario: Empty test input exposes all gaps

- **WHEN** a valid nonempty catalog is paired with an empty existing test directory
- **THEN** every requirement appears as `UNLINKED` and in the unlinked list
- **AND** the summary shows zero discovered tests and zero resolved links

### Requirement: [ST-RPT-004] Render reproducibly and escape source text

Report bytes SHALL be UTF-8 with LF line endings and a final newline, without
timestamps or absolute machine paths. Requirements SHALL sort by ID, linked tests
by test identifier, and unknown references by ID then test identifier. Source paths
SHALL use forward slashes relative to their selected input roots. Source text
SHALL be escaped so it cannot create Markdown columns or raw HTML.

#### Scenario: Deterministic ordering

- **WHEN** the same inputs are enumerated in a different filesystem order
- **THEN** repeated reports have identical bytes

#### Scenario: Escape a hostile title or filename

- **WHEN** a title or path contains pipes, backticks, ampersands, angle brackets,
  or embedded newlines
- **THEN** it is rendered as literal cell content without extra table columns or HTML

#### Scenario: Keep file and directory inputs portable

- **WHEN** the spec root is a directory and the test input is a single file
- **THEN** specification locations use paths relative to that directory and test
  locations use the selected file's basename, each with a one-based source line

### Requirement: [ST-RPT-005] Provide the local command interface

On Python 3.12, the installed command SHALL be
`spectrace report [--specs PATH] [--tests PATH] [--output PATH] [--fail-on-unlinked]`.
Spec and test defaults SHALL be `openspec/specs` and `tests`, resolved from the
working directory. Omitted `--output` or `--output -` SHALL write Markdown to stdout.
`--help` and `--version` SHALL work without project inputs. Runtime SHALL require
no database, frontend, external APIs, LLM, or network access.

#### Scenario: Use explicit input roots

- **WHEN** `spectrace report --specs openspec/changes/bootstrap-spectrace/specs --tests tests`
  is run on valid inputs
- **THEN** it reports only those roots and emits Markdown on stdout
- **AND** no inputs are rewritten, inspected test modules imported, or network requests made

#### Scenario: Request help without a project

- **WHEN** `spectrace --help`, `spectrace report --help`, or `spectrace --version`
  runs in an empty directory
- **THEN** it exits with status 0 and does not try to read input roots

### Requirement: [ST-RPT-006] Distinguish gaps from invalid input

The command SHALL exit 0 for a valid report with no unknown references, except
that `--fail-on-unlinked` SHALL make any unlinked requirement exit 1. Unknown
references SHALL always exit 1. Invalid arguments, invalid input, or output failure
SHALL exit 2, take precedence over gap statuses, and emit concise diagnostics on
stderr without a normal traceback or report. Statuses 0 and 1 SHALL both emit the report.

#### Scenario: Unlinked requirements are informational by default

- **WHEN** valid inputs contain unlinked requirements and no unknown references
- **THEN** the default command emits the report and exits 0
- **AND** adding `--fail-on-unlinked` emits the same report and exits 1

#### Scenario: Fully linked valid input succeeds

- **WHEN** all requirements have at least one explicit link and no unknown references exist
- **THEN** the command exits 0 with or without `--fail-on-unlinked`

#### Scenario: Invalid input prevents misleading success

- **WHEN** an input path is missing, IDs are duplicated, a selected source fails
  parsing, or an unknown CLI option is supplied
- **THEN** the command exits 2, stdout contains no report, and stderr explains the problem

### Requirement: [ST-RPT-007] Write report files without damaging inputs

With a filesystem `--output`, the command SHALL emit no report on stdout and SHALL
replace the destination only after successful analysis and complete rendering.
It SHALL reject a destination that is a selected input, directory, or symlink.
An absent parent directory or failed write SHALL exit 2. Existing destination
contents SHALL remain unchanged on analysis or write failure.

#### Scenario: Save a report that identifies gaps

- **WHEN** valid analysis yields exit status 1 and `--output traceability.md` is writable
- **THEN** the complete Markdown report is saved to that file and exit status remains 1

#### Scenario: Preserve a previous report on failure

- **WHEN** a report file already exists and parsing fails or replacement cannot complete
- **THEN** the existing report bytes remain unchanged and the command exits 2

#### Scenario: Reject overwriting a selected source

- **WHEN** `--output` resolves to any selected specification or test source path
- **THEN** the command reports an input/output collision with status 2
- **AND** the selected file remains unchanged
