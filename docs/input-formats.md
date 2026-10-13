# Input formats

## Requirements

Select a UTF-8 Markdown file or a directory recursively containing files named
`spec.md`. The default directory is `openspec/specs`; pending changes and archives
are not automatically combined with it. To analyze an ADDED-only change or
archive instead, select its `specs` directory explicitly.

Canonical files use `## Requirements`; ADDED-only change files use
`## ADDED Requirements`. MODIFIED, REMOVED, and RENAMED sections are rejected
because SpecTrace does not resolve deltas against a baseline.

```markdown
## Requirements

### Requirement: [REQ-AUTH-001] Reject invalid passwords

The application SHALL reject invalid passwords.

#### Scenario: Invalid password

- **WHEN** a password is invalid
- **THEN** authentication is rejected
```

IDs are explicit, case-sensitive strings matching
`[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+`. They must be unique across the selected catalog.
Changing a title does not change its ID. Missing/invalid IDs, empty titles or
bodies, duplicate IDs, and zero requirements are errors.

Only unindented ATX headings are structural. Backtick/tilde fences (at least three
characters, up to three leading spaces, optional info string) and HTML comments
hide example headings. Closing fences need the same character, at least the
opening length, and only trailing whitespace. Unclosed fences/comments are errors.
Requirement bodies retain scenarios and end at the next real level-one through
level-three heading. Surrounding blank lines are removed; line endings become LF.

Traversal skips hidden directories and symbolic links. An explicitly selected
symlink root, missing/unreadable input, unsupported filename, or invalid encoding
is an error. Paths in reports are relative to the selected directory, or the
basename for a selected file, and source line numbers start at one.

## Pytest references

Select a regular `test_*.py`/`*_test.py` file or a directory containing such files.
Supported definitions are module-level `test_*` functions and direct `test_*`
methods in top-level `Test*` classes without `__init__` or `__new__`. Async
definitions are supported; fixture functions using direct `pytest.fixture`
decorators are excluded. An existing empty test tree is valid; a missing one is not.

```python
import pytest


@pytest.mark.requirements("REQ-AUTH-001")
def test_invalid_password():
    # Replace this illustrative body with the actual behavior assertion.
    pass
```

Markers must directly decorate supported tests and supply one or more literal
string IDs as positional arguments. Repeated IDs are deduplicated. Dynamic
arguments, keywords, and recognized markers on classes, helpers, module-level
`pytestmark`, or individual `pytest.param` cases are errors. Names, comments,
docstrings, assertion text, arbitrary strings, and aliases never establish links.
Use the exact spelling `pytest.mark.requirements`; aliases such as `pt.mark` and
bare `requirements` are unsupported.

To run marked tests with pytest, register the marker in that project's pytest
configuration, for example:

```toml
[tool.pytest.ini_options]
markers = ["requirements(*ids): explicit requirement references"]
addopts = "--strict-markers"
```

SpecTrace does not run pytest, import inspected sources, load `conftest.py`, or
load plugins. It honors Python source-encoding declarations and uses Python 3.12
syntax. Invalid encoding/syntax and duplicate static identifiers are errors.

Each parametrized, skipped, or xfail test remains one static definition. Inherited
or conditional/nested tests, custom discovery, `__test__` overrides, aliases, and
import rebinding are not resolved. IDs resemble pytest node IDs but are relative
to the chosen root, have no parameter suffixes, and do not prove runtime collection.
