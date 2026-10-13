# requirement-catalog Specification

## Purpose

Provide a deterministic catalog of explicitly identified requirements from local
OpenSpec documents, preserving their source locations and exposing invalid input.

## Requirements

### Requirement: [ST-CAT-001] Select a bounded specification input

SpecTrace SHALL accept one Markdown file or recursively discover files named
`spec.md` beneath one directory. It SHALL skip hidden directories and symbolic
links encountered during traversal, reject a symbolic-link input root, and sort
discovered paths lexicographically. It SHALL read only the selected input tree.

#### Scenario: Select the canonical specification tree

- **WHEN** the spec input is `openspec/specs` containing `accounts/spec.md`,
  `billing/spec.md`, and `notes.md`
- **THEN** only the two `spec.md` files are selected in path order
- **AND** sibling `openspec/changes` and archive directories are not visited

#### Scenario: Select a single document

- **WHEN** the spec input is a regular file named `requirements.md`
- **THEN** only that UTF-8 Markdown document is read

#### Scenario: Avoid hidden files and linked trees

- **WHEN** a selected directory contains `.drafts/spec.md` or a symlink to another
  specification file or directory
- **THEN** those entries are excluded
- **AND** explicitly selecting a symlink as the input root is an input error

### Requirement: [ST-CAT-002] Recognize the supported OpenSpec document profile

SpecTrace SHALL extract unindented `### Requirement:` blocks within
`## Requirements` or `## ADDED Requirements` sections. It SHALL ignore headings
inside fenced code blocks or HTML comments. It SHALL reject MODIFIED, REMOVED, or
RENAMED delta sections and requirement headings outside the supported sections;
it SHALL NOT apply change deltas to a baseline.

#### Scenario: Read a canonical specification

- **WHEN** a document has `## Purpose`, `## Requirements`, and identified
  requirement blocks with `#### Scenario:` subsections
- **THEN** each requirement is extracted once and scenarios remain part of its body

#### Scenario: Read this proposed change explicitly

- **WHEN** the selected input is `openspec/changes/bootstrap-spectrace/specs`
  and all delta operations are `## ADDED Requirements`
- **THEN** its requirements are cataloged independently of canonical specs

#### Scenario: Ignore examples

- **WHEN** a fake requirement heading appears in a backtick or tilde fenced code
  block, including a fence with a language tag, or within `<!-- ... -->`
- **THEN** it creates no requirement and does not split a real requirement block

#### Scenario: Reject a delta requiring baseline resolution

- **WHEN** a selected document contains an unfenced `## MODIFIED Requirements`,
  `## REMOVED Requirements`, or `## RENAMED Requirements` section
- **THEN** processing fails with its source path and section line
- **AND** the diagnostic directs the user to use canonical specs or an ADDED-only tree

#### Scenario: Reject a misplaced requirement

- **WHEN** a real `### Requirement:` heading occurs outside `## Requirements` or
  `## ADDED Requirements`
- **THEN** processing reports its location as an unsupported document structure

### Requirement: [ST-CAT-003] Require explicit stable identifiers

Every extracted heading SHALL have the form `### Requirement: [ID] Title`, with
a nonempty title and an ID matching `[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+`. IDs SHALL be
case-sensitive opaque strings. SpecTrace SHALL NOT generate IDs from titles,
paths, positions, scenario names, or requirement text.

#### Scenario: Extract a valid heading

- **WHEN** a document contains `### Requirement: [REQ-AUTH-001] Reject invalid passwords`
- **THEN** its ID is `REQ-AUTH-001` and its title is `Reject invalid passwords`

#### Scenario: Reject absent or malformed identifiers

- **WHEN** a requirement heading omits `[ID]`, has an empty title, or contains
  `[req-auth-001]`, `[REQ_001]`, or `[REQ 001]`
- **THEN** an input error identifies the source path and heading line
- **AND** no substitute identifier is created

#### Scenario: Retain identity when a title changes

- **WHEN** a requirement's title changes but its explicit ID does not
- **THEN** references to that ID still resolve to the same catalog entry

### Requirement: [ST-CAT-004] Preserve requirement content and source locations

Each catalog entry SHALL retain its ID, title, Markdown body, source path, and
one-based heading line. The body SHALL extend to the next real heading at level
one, two, or three, or end of file, and retain scenario subsections. Leading and
trailing blank lines SHALL be removed and line endings normalized to LF. Empty
bodies SHALL be input errors.

#### Scenario: Preserve a multiline requirement

- **WHEN** a CRLF document contains a requirement description, a scenario, and then
  the next requirement
- **THEN** the first body contains its description and scenario with LF line endings
- **AND** it excludes the next requirement and surrounding blank lines
- **AND** its source line is the original heading's one-based line

#### Scenario: Reject an empty requirement

- **WHEN** an identified requirement heading is immediately followed by another
  level-three heading with only whitespace between them
- **THEN** the empty requirement produces a source-located input error

### Requirement: [ST-CAT-005] Reject ambiguous and unusable catalogs

SpecTrace SHALL reject duplicate IDs across the selected documents, even when
their titles or bodies match. It SHALL also reject a missing or unreadable root,
an unsupported root file extension, unreadable selected files, invalid UTF-8,
unterminated code fences or HTML comments, no selected spec files, or a final
catalog containing zero requirements. Invalid input SHALL NOT yield a success report.

#### Scenario: Reject duplicate requirement identity

- **WHEN** `REQ-AUTH-001` appears twice in one document or in two selected documents
- **THEN** an error names the ID and both source locations
- **AND** neither occurrence overwrites the other

#### Scenario: Distinguish an empty catalog from successful traceability

- **WHEN** the input directory is empty or its documents contain no requirement blocks
- **THEN** processing fails instead of reporting zero missing requirements as success

#### Scenario: Report unreadable or malformed source

- **WHEN** a selected file cannot be read or decoded as UTF-8, or has an unclosed
  fence or HTML comment
- **THEN** an input diagnostic names the path and an available line or byte location
- **AND** no partial traceability report is emitted
