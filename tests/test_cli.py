import os
import subprocess
import sys
from pathlib import Path

import pytest

from spectrace.cli import main

EXECUTABLE = str(Path(sys.executable).with_name("spectrace"))
PROJECT = Path(__file__).resolve().parents[1]


def run_cli(directory, *arguments):
    return subprocess.run([EXECUTABLE, *arguments], cwd=directory, capture_output=True, check=False)


@pytest.fixture
def project(tmp_path, write_file):
    write_file(
        "openspec/specs/demo/spec.md",
        "## Requirements\n### Requirement: [REQ-A] First\nBody\n"
        "### Requirement: [REQ-B] Second\nBody\n",
    )
    write_file("tests/test_demo.py", '@pytest.mark.requirements("REQ-A")\ndef test_one(): pass\n')
    return tmp_path


@pytest.mark.requirements("ST-RPT-005", "ST-RPT-006")
@pytest.mark.parametrize("arguments", [("--help",), ("report", "--help"), ("--version",)])
def test_help_and_version_need_no_inputs(tmp_path, arguments):
    result = run_cli(tmp_path, *arguments)
    assert result.returncode == 0
    assert b"spectrace" in result.stdout
    assert result.stderr == b""


@pytest.mark.requirements("ST-RPT-005", "ST-RPT-006", "ST-RPT-001")
def test_default_and_strict_gap_exit_codes(project):
    normal = run_cli(project, "report")
    strict = run_cli(project, "report", "--fail-on-unlinked")
    assert normal.returncode == 0 and strict.returncode == 1
    assert normal.stdout == strict.stdout
    assert b"Unlinked requirements: 1" in normal.stdout
    assert normal.stderr == strict.stderr == b""


@pytest.mark.requirements("ST-RPT-005", "ST-RPT-006")
@pytest.mark.parametrize("strict", [False, True])
def test_fully_linked_succeeds(project, strict):
    (project / "tests/test_demo.py").write_text(
        '@pytest.mark.requirements("REQ-A", "REQ-B")\ndef test_one(): pass\n'
    )
    args = ("--fail-on-unlinked",) if strict else ()
    result = run_cli(project, "report", *args)
    assert result.returncode == 0
    assert b"Unlinked requirements: 0" in result.stdout
    assert b"## Unlinked Requirements\n\nNone" in result.stdout


@pytest.mark.requirements("ST-RPT-002", "ST-RPT-006")
@pytest.mark.parametrize("strict", [False, True])
def test_unknown_reference_is_reported_once_and_fails(project, strict):
    (project / "tests/test_demo.py").write_text(
        '@pytest.mark.requirements("REQ-A", "REQ-TYPO", "REQ-TYPO")\ndef test_one(): pass\n'
    )
    result = run_cli(project, "report", *(["--fail-on-unlinked"] if strict else []))
    assert result.returncode == 1
    assert b"Unknown references: 1" in result.stdout
    assert b"Resolved links: 1" in result.stdout
    assert b"REQ-TYPO" in result.stdout
    assert result.stderr == b""


@pytest.mark.requirements("ST-TST-001", "ST-RPT-003", "ST-RPT-006")
def test_empty_test_directory_exposes_all_gaps(project):
    (project / "tests/test_demo.py").unlink()
    result = run_cli(project, "report", "--fail-on-unlinked")
    assert result.returncode == 1
    assert b"Unlinked requirements: 2" in result.stdout
    assert b"Discovered tests: 0" in result.stdout
    assert result.stdout.count(b"| UNLINKED |") == 2


@pytest.mark.requirements("ST-RPT-005", "ST-RPT-006", "ST-TST-005")
@pytest.mark.parametrize(
    "arguments",
    [
        (),
        ("report", "--unknown"),
        ("report", "--specs", "missing"),
        ("report", "--tests", "missing"),
        ("report", "--out", "file"),
    ],
)
def test_usage_and_missing_inputs_fail_without_report(project, arguments):
    result = run_cli(project, *arguments)
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr and b"Traceback" not in result.stderr


@pytest.mark.requirements("ST-RPT-006", "ST-RPT-007", "ST-CAT-005", "ST-TST-004", "ST-TST-005")
@pytest.mark.parametrize(
    "relative,content",
    [
        (
            "openspec/specs/demo/spec.md",
            "## Requirements\n### Requirement: [REQ-A] First\nBody\n"
            "### Requirement: [REQ-A] Duplicate\nBody\n",
        ),
        ("tests/test_demo.py", "def test_broken(:\n"),
        ("tests/test_demo.py", "@pytest.mark.requirements(dynamic)\ndef test_one(): pass\n"),
        ("openspec/specs/demo/spec.md", "## Requirements\nNo requirements\n"),
    ],
)
def test_invalid_source_has_precedence_and_preserves_previous_report(project, relative, content):
    old = project / "report.md"
    old.write_bytes(b"previous report")
    (project / relative).write_text(content)
    for output in [(), ("--output", "report.md")]:
        result = run_cli(project, "report", "--fail-on-unlinked", *output)
        assert result.returncode == 2
        assert result.stdout == b""
        assert result.stderr and b"Traceback" not in result.stderr
    assert old.read_bytes() == b"previous report"


@pytest.mark.requirements("ST-RPT-004", "ST-RPT-005", "ST-RPT-007")
def test_stdout_file_and_explicit_dash_are_identical(project):
    stdout = run_cli(project, "report")
    dash = run_cli(project, "report", "--output", "-")
    file = run_cli(project, "report", "--output", "report.md")
    assert stdout.returncode == dash.returncode == file.returncode == 0
    assert stdout.stdout == dash.stdout == (project / "report.md").read_bytes()
    assert file.stdout == file.stderr == b""
    assert stdout.stdout.endswith(b"\n") and b"\r" not in stdout.stdout


@pytest.mark.requirements("ST-RPT-007")
def test_gap_report_is_saved_with_status_one(project):
    result = run_cli(project, "report", "--output", "report.md", "--fail-on-unlinked")
    assert result.returncode == 1
    assert b"Unlinked requirements: 1" in (project / "report.md").read_bytes()
    assert result.stdout == result.stderr == b""


@pytest.mark.requirements("ST-RPT-007")
@pytest.mark.parametrize(
    "output", ["openspec/specs/demo/spec.md", "tests/test_demo.py", "tests", "absent/report.md"]
)
def test_reject_input_collision_directory_and_missing_parent(project, output):
    snapshots = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
    result = run_cli(project, "report", "--output", output)
    assert result.returncode == 2 and result.stdout == b""
    assert result.stderr and b"Traceback" not in result.stderr
    assert all(path.read_bytes() == contents for path, contents in snapshots.items())


@pytest.mark.requirements("ST-RPT-007")
@pytest.mark.parametrize("dangling", [False, True])
def test_reject_symlink_destination(project, dangling):
    target = project / "target"
    if not dangling:
        target.write_bytes(b"keep")
    (project / "report.md").symlink_to(target)
    result = run_cli(project, "report", "--output", "report.md")
    assert result.returncode == 2 and result.stdout == b""
    assert b"symlink" in result.stderr
    assert (not target.exists()) if dangling else target.read_bytes() == b"keep"


@pytest.mark.requirements("ST-RPT-007", "ST-RPT-006")
@pytest.mark.parametrize("operation", ["write", "replace"])
def test_failed_write_or_replace_preserves_old_report(project, monkeypatch, capsys, operation):
    import tempfile

    destination = project / "report.md"
    destination.write_bytes(b"old report")
    monkeypatch.chdir(project)
    if operation == "replace":

        def denied(*args):
            raise PermissionError(13, "Permission denied")

        monkeypatch.setattr(os, "replace", denied)
    else:
        original = tempfile.NamedTemporaryFile

        class FailingFile:
            def __init__(self, **kwargs):
                self.stream = original(**kwargs)
                self.name = self.stream.name

            def __enter__(self):
                return self

            def write(self, content):
                self.stream.write(content[:5])
                raise OSError(28, "No space left on device")

            def __exit__(self, *args):
                self.stream.close()

        monkeypatch.setattr(tempfile, "NamedTemporaryFile", FailingFile)
    assert main(["report", "--output", "report.md", "--fail-on-unlinked"]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "cannot write report" in captured.err
    assert destination.read_bytes() == b"old report"
    assert not list(project.glob(".spectrace-*"))


@pytest.mark.requirements("ST-RPT-004", "ST-RPT-005", "ST-TST-005")
def test_explicit_roots_do_not_execute_scanned_code_or_conftest(project):
    sentinel = project / "executed"
    source = project / "tests/test_demo.py"
    source.write_text(
        "import missing_spectrace_example\nfrom pathlib import Path\n"
        f"Path({str(sentinel)!r}).touch()\n"
        '@pytest.mark.requirements("REQ-A")\ndef test_one(): pass\n'
    )
    (source.parent / "conftest.py").write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\n"
    )
    before = source.read_bytes()
    result = run_cli(
        project, "report", "--specs", "openspec/specs", "--tests", "tests/test_demo.py"
    )
    assert result.returncode == 0, result.stderr
    assert b"demo/spec.md:2" in result.stdout
    assert b"test&#95;demo.py::test&#95;one" in result.stdout
    assert not sentinel.exists()
    assert source.read_bytes() == before


@pytest.mark.requirements("ST-RPT-002", "ST-RPT-003", "ST-RPT-004", "ST-RPT-005")
def test_documented_example_command_and_report(tmp_path):
    result = run_cli(
        tmp_path,
        "report",
        "--specs",
        str(PROJECT / "examples/specs"),
        "--tests",
        str(PROJECT / "examples/tests"),
    )
    assert result.returncode == 1
    assert result.stdout == (PROJECT / "docs/example-report.md").read_bytes()
    assert result.stderr == b""


@pytest.mark.requirements("ST-RPT-006")
def test_closed_stdout_pipe_returns_output_failure(project):
    # A pipe with no reader deterministically fails even for a small report.
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    try:
        result = subprocess.run(
            [EXECUTABLE, "report"],
            cwd=project,
            stdout=write_fd,
            stderr=subprocess.PIPE,
            check=False,
        )
    finally:
        os.close(write_fd)
    assert result.returncode == 2
    assert b"spectrace:" in result.stderr
    assert b"Exception ignored" not in result.stderr
    assert b"Traceback" not in result.stderr


@pytest.mark.requirements("ST-RPT-006", "ST-RPT-007")
@pytest.mark.skipif(os.name != "posix", reason="POSIX byte filenames")
def test_unencodable_source_path_is_a_clean_output_error(project):
    filename = os.fsencode(project / "tests") + b"/test_\xff.py"
    with open(filename, "wb") as stream:
        stream.write(b'@pytest.mark.requirements("REQ-A")\ndef test_one(): pass\n')
    (project / "report.md").write_bytes(b"previous report")
    result = run_cli(project, "report", "--output", "report.md")
    assert result.returncode == 2 and result.stdout == b""
    assert b"spectrace:" in result.stderr and b"Traceback" not in result.stderr
    assert (project / "report.md").read_bytes() == b"previous report"


@pytest.mark.requirements("ST-RPT-005")
def test_runtime_makes_no_network_connections(project, monkeypatch, capsys):
    import socket

    def forbidden(*args, **kwargs):
        pytest.fail("SpecTrace must not attempt a network connection")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.chdir(project)
    assert main(["report"]) == 0
    assert "# SpecTrace Traceability Report" in capsys.readouterr().out
