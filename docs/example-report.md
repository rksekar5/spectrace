# SpecTrace Traceability Report

Links are declared source associations. They do not prove collection, execution,
passing tests, or behavioral coverage. Tests are represented at definition granularity.
Paths are relative to the selected specification and test roots.

## Summary

- Requirements: 3
- Linked requirements: 2
- Unlinked requirements: 1
- Discovered tests: 2
- Linked tests: 2
- Resolved links: 3
- Unknown references: 1

## Requirements

| ID | Title | Specification | Tests (definition line) | Status |
| --- | --- | --- | --- | --- |
| REQ-A | First | demo/spec.md:3 | test&#95;demo.py::test&#95;a &#40;line 5&#41;; test&#95;demo.py::test&#95;b &#40;line 10&#41; | LINKED |
| REQ-B | Second | demo/spec.md:6 | test&#95;demo.py::test&#95;a &#40;line 5&#41; | LINKED |
| REQ-C | Third | demo/spec.md:9 | None | UNLINKED |

## Unlinked Requirements

- REQ-C: Third (demo/spec.md:9)

## Unknown References

| ID | Test | Source |
| --- | --- | --- |
| REQ-TYPO | test&#95;demo.py::test&#95;b | test&#95;demo.py:10 |
