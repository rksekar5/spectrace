"""Command-line interface for SpecTrace."""

import argparse
import os
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

from spectrace.discovery import discover
from spectrace.mapping import resolve_links
from spectrace.models import InputError, InputFile
from spectrace.pytest_refs import read_tests
from spectrace.report import render_markdown
from spectrace.requirements import read_requirements


def _write_stdout(content: bytes) -> None:
    try:
        sys.stdout.buffer.write(content)
        sys.stdout.buffer.flush()
    except OSError:
        # A failed buffered write would otherwise be retried at interpreter exit,
        # overriding our documented status 2 with Python's flush-error status 120.
        with open(os.devnull, "wb") as sink:
            os.dup2(sink.fileno(), sys.stdout.fileno())
        raise


def _write_report(destination: Path, content: bytes, inputs: tuple[InputFile, ...]) -> None:
    """Replace only a complete report; preserve existing data on any failure."""
    temporary: Path | None = None
    try:
        if destination.is_symlink() or destination.is_dir():
            raise InputError(f"{destination}: output must not be a symlink or directory")
        if destination.resolve() in {item.path.resolve() for item in inputs}:
            raise InputError(f"{destination}: output collides with a selected input")
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, prefix=".spectrace-", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, destination)
        temporary = None
    except OSError as error:
        raise InputError(
            f"{destination}: cannot write report: {error.strerror or error}"
        ) from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spectrace", description=__doc__, allow_abbrev=False)
    parser.add_argument("--version", action="version", version=f"spectrace {version('spectrace')}")
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser(
        "report", help="report explicit requirement-to-test links", allow_abbrev=False
    )
    report.add_argument(
        "--specs",
        type=Path,
        default=Path("openspec/specs"),
        help="spec file or directory (default: openspec/specs)",
    )
    report.add_argument(
        "--tests", type=Path, default=Path("tests"), help="test file or directory (default: tests)"
    )
    report.add_argument(
        "--output", default="-", metavar="PATH", help="report file, or - for stdout (default)"
    )
    report.add_argument(
        "--fail-on-unlinked",
        action="store_true",
        help="exit 1 if a requirement has no explicit test link",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        spec_files = discover(args.specs, "spec")
        catalog = read_requirements(spec_files)
        test_files = discover(args.tests, "test")
        tests = read_tests(test_files)
        result = resolve_links(catalog, tests)
        content = render_markdown(result).encode("utf-8")
        if args.output == "-":
            _write_stdout(content)
        else:
            _write_report(Path(args.output), content, spec_files + test_files)
        return int(bool(result.unknown or (args.fail_on_unlinked and result.unlinked)))
    except (InputError, OSError, UnicodeError) as error:
        print(f"spectrace: {error}", file=sys.stderr)
        return 2
