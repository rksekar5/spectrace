# SpecTrace

SpecTrace maps OpenSpec requirements to explicit references in pytest source files.
It performs static analysis: inspected Python is never imported or executed.
Declared links do not prove test collection, execution, passing tests, or behavioral
coverage. Runtime requires Python 3.12 or newer and has no third-party dependencies,
network access, database, frontend, or AI service requirement.

## Usage

```bash
spectrace report
spectrace report --specs openspec/specs --tests tests --output traceability.md
spectrace report --specs openspec/specs --tests tests --fail-on-unlinked
```

`--specs` defaults to `openspec/specs` and `--tests` to `tests`, relative to the
working directory. Each accepts one supported file or directory. `--output -`
and omitting `--output` both write Markdown to stdout. `--help`, `report --help`,
and `--version` work without project files.

The approved canonical specifications are in `openspec/specs`. To check their
explicit links to this checkout's tests:

```bash
spectrace report --fail-on-unlinked
```

| Exit | Meaning |
| --- | --- |
| 0 | Valid report, no unknown references; unlinked requirements are informational by default |
| 1 | Unknown requirement references, or unlinked requirements with `--fail-on-unlinked`; complete report is still emitted |
| 2 | Invalid arguments/input or output failure; diagnostic on stderr, no success report |

IDs in tests must exactly match explicit IDs in specification headings. For the
supported Markdown and pytest conventions, see [input formats](docs/input-formats.md).
A report's LINKED status is an association, not evidence of behavioral coverage.

The bundled example intentionally has one unlinked requirement and a typo in a
reference, so these commands exit 1:

```bash
spectrace report --specs examples/specs --tests examples/tests
spectrace report --specs examples/specs --tests examples/tests --output traceability.md
```

Their output is the [example report](docs/example-report.md), checked by automated
tests. Report ordering is deterministic, with UTF-8/LF output and no timestamps or
absolute machine paths. File output replaces an existing report only after valid
analysis and a complete write. Source collisions, symlink/directory destinations,
and missing output parent directories are errors. Parsing or writing failure
preserves a previous report; input files are never rewritten.

## Development

From a checkout, create an isolated Python 3.12 environment and install the pinned
development tools:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
ruff check .
ruff format --check .
python -m build
```

The prepared cloud environment can instead activate
`/workspace/.venvs/spectrace/bin/activate` and run the same installation command.

Every test explicitly declares the requirement IDs it exercises through
`@pytest.mark.requirements(...)`. The marker is registered in `pyproject.toml`,
and pytest runs in strict-marker mode.

## OpenSpec workflow

The implemented and archived change is [bootstrap-spectrace](openspec/changes/archive/2026-10-13-bootstrap-spectrace/proposal.md).
Its [design](openspec/changes/archive/2026-10-13-bootstrap-spectrace/design.md) and
[tasks](openspec/changes/archive/2026-10-13-bootstrap-spectrace/tasks.md) record the approved implementation.
Use the Codex `openspec-apply-change` skill for approved implementation and
`openspec-verify-change` for verification of future changes.

OpenSpec is authoring tooling only; it is not a Python runtime dependency.
See [the workflow guide](openspec/README.md) for installation and commands.
