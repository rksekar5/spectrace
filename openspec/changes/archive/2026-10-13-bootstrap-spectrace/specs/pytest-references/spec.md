# Pytest References

## Purpose

Identify explicit requirement references in conventional pytest source files
without importing, collecting, or executing the tests or their dependencies.

## ADDED Requirements

### Requirement: [ST-TST-001] Discover supported pytest definitions

SpecTrace SHALL recursively select `test_*.py` and `*_test.py` beneath one test
directory, or accept one matching regular file. It SHALL discover module-level
`test_*` functions and direct `test_*` methods of top-level `Test*` classes without
`__init__` or `__new__`. Both `def` and `async def` SHALL be recognized. Hidden
directories and symlinks SHALL be excluded as for specification discovery.

#### Scenario: Discover functions and class methods

- **WHEN** `tests/test_auth.py` defines `test_login` and `TestAuth.test_logout`
- **THEN** their test identifiers are `test_auth.py::test_login` and
  `test_auth.py::TestAuth::test_logout`, relative to the selected test root

#### Scenario: Exclude unsupported definitions

- **WHEN** a selected file includes a helper function, a nested function, an
  inherited method without a direct definition, or a class with `__init__`
- **THEN** those definitions are not included in the supported test inventory
- **AND** functions decorated directly with `pytest.fixture` or `pytest.fixture(...)`
  are excluded even if their names start with `test_`

#### Scenario: Represent a single selected file

- **WHEN** the test input is `tests/unit/test_auth.py`
- **THEN** its identifiers use `test_auth.py` as the relative file component

#### Scenario: Accept an empty existing test tree

- **WHEN** the test directory exists but has no matching files or supported definitions
- **THEN** the discovered test count is zero and all catalog requirements remain unlinked

### Requirement: [ST-TST-002] Extract only literal explicit requirement markers

SpecTrace SHALL create references only from direct
`@pytest.mark.requirements("ID", ...)` decorators on supported test definitions.
Each argument SHALL be a literal string matching the catalog ID grammar. Multiple
decorators and multiple IDs SHALL be supported, with duplicate IDs on one test
deduplicated. A test SHALL retain its source path and one-based definition line.

#### Scenario: Link one test to several requirements

- **WHEN** a supported test has `@pytest.mark.requirements("REQ-AUTH-001", "REQ-AUTH-002")`
- **THEN** it references exactly those two IDs

#### Scenario: Deduplicate repeated markers

- **WHEN** a test repeats `REQ-AUTH-001` within one marker or across two markers
- **THEN** exactly one test-to-requirement pair is recorded for that ID

#### Scenario: Preserve a marked method location

- **WHEN** a supported class method has a valid marker above its definition
- **THEN** its reference identifies the class-qualified test and the definition's line

### Requirement: [ST-TST-003] Never infer links from other source text

Test names, file names, comments, docstrings, assertion text, and arbitrary strings
SHALL NOT create links. Import aliases and marker aliases SHALL NOT be resolved.
Only the exact decorator syntax in ST-TST-002 SHALL establish a reference. Tests
without accepted markers SHALL remain in the discovered test count with zero links.

#### Scenario: Requirement-like names provide no evidence

- **WHEN** a test is named `test_REQ_AUTH_001` and mentions `REQ-AUTH-001` in a
  comment, docstring, and assertion message but has no accepted marker
- **THEN** it creates no reference to `REQ-AUTH-001`

#### Scenario: Aliased markers do not silently establish links

- **WHEN** a test uses `@pt.mark.requirements("REQ-AUTH-001")` or `@requirements("REQ-AUTH-001")`
- **THEN** those decorators create no links
- **AND** the documented supported profile explains that aliases are unsupported

### Requirement: [ST-TST-004] Reject malformed or misplaced recognized markers

A recognized `pytest.mark.requirements` decorator SHALL be a call with at least
one positional literal ID and no keywords, starred arguments, or expressions.
Recognized markers outside direct decorators on supported tests SHALL be input
errors, including module/class marks and parameter-case marks. Diagnostics SHALL
include the file, marker line, and reason; no partial report SHALL be emitted.

#### Scenario: Reject dynamic and malformed arguments

- **WHEN** a recognized marker uses a variable, an f-string, a list, `*ids`, a
  keyword argument, an integer, an empty string, or an invalid ID
- **THEN** processing fails with a source-located marker diagnostic

#### Scenario: Reject an empty or bare marker

- **WHEN** a test has `@pytest.mark.requirements()` or `@pytest.mark.requirements`
- **THEN** processing fails instead of treating the test as explicitly linked

#### Scenario: Reject unsupported scope

- **WHEN** a matching file assigns `pytestmark = pytest.mark.requirements("REQ-AUTH-001")`,
  decorates a class or helper with that marker, or puts it inside `pytest.param`
- **THEN** processing reports that requirement markers must decorate supported test definitions

### Requirement: [ST-TST-005] Keep analysis static and expose source failures

SpecTrace SHALL parse selected Python sources without importing modules, running
pytest collection, executing test bodies or decorators, or loading plugins or
`conftest.py`. It SHALL respect Python source-encoding declarations and reject
syntax errors, decoding errors, missing or unreadable inputs, and duplicate
supported test identifiers instead of returning incomplete mappings.

#### Scenario: Source side effects never execute

- **WHEN** a selected test module has an unavailable import and module-level code
  that would write a file or raise an exception, but valid Python syntax
- **THEN** its supported references are extracted without running that code
- **AND** the imported dependency does not need to be installed

#### Scenario: Report invalid Python

- **WHEN** a selected test file has a syntax error or invalid source encoding
- **THEN** an input diagnostic gives its path and the available error location
- **AND** no report is emitted

#### Scenario: Reject an ambiguous definition

- **WHEN** one selected module defines `test_login` twice, or duplicates a
  supported class-qualified method identifier
- **THEN** an input error reports both definition locations

### Requirement: [ST-TST-006] Report links at definition granularity

Parametrization SHALL NOT expand test identifiers into runtime cases. A supported
test with `parametrize`, `skip`, `skipif`, or `xfail` decorators SHALL count once;
its accepted requirement markers SHALL still establish static links. SpecTrace
SHALL NOT claim that such tests are collected, runnable, executed, or passing.

#### Scenario: Parametrized test remains one definition

- **WHEN** a test with a valid requirement marker is parametrized over ten cases
- **THEN** the report includes one linked test identifier without parameter suffixes

#### Scenario: Skipped test is a declared link only

- **WHEN** a supported test has both `pytest.mark.skip` and a valid requirement marker
- **THEN** the requirement has a static link to that test
- **AND** the report makes no claim about executed coverage or pass status
