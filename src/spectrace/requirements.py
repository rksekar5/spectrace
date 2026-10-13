"""Read the approved OpenSpec Markdown subset and validate explicit identities."""

import re
from collections.abc import Iterable, Iterator

from spectrace.models import REQUIREMENT_ID, InputError, InputFile, Requirement, Source

_HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_REQUIREMENT = re.compile(r"^Requirement: \[([^\]]+)\][ \t]+(\S.*)$")
_SECTIONS = {"Requirements", "ADDED Requirements"}
_UNSUPPORTED = {"MODIFIED Requirements", "REMOVED Requirements", "RENAMED Requirements"}


def _headings(lines: list[str], path: str) -> Iterator[tuple[int, int, str]]:
    """Yield structural headings, ignoring code fences and comment contents."""
    fence: tuple[str, int, int] | None = None
    comment_line: int | None = None
    for number, line in enumerate(lines, 1):
        if fence:
            match = _FENCE.fullmatch(line)
            if (
                match
                and match[1][0] == fence[0]
                and len(match[1]) >= fence[1]
                and not match[2].strip()
            ):
                fence = None
            continue
        if comment_line is None and (match := _FENCE.fullmatch(line)):
            fence = (match[1][0], len(match[1]), number)
            continue

        # Preserve positions when removing comments: indented or commented-out
        # headings must not become unindented structural headings.
        visible = ""
        offset = 0
        while offset < len(line):
            if comment_line is not None:
                end = line.find("-->", offset)
                if end < 0:
                    visible += " " * (len(line) - offset)
                    break
                visible += " " * (end + 3 - offset)
                offset = end + 3
                comment_line = None
            else:
                start = line.find("<!--", offset)
                if start < 0:
                    visible += line[offset:]
                    break
                visible += line[offset:start]
                comment_line = number
                offset = start
        if match := _HEADING.fullmatch(visible):
            yield number, len(match[1]), match[2]
    if fence:
        raise InputError(f"{path}:{fence[2]}: unterminated code fence")
    if comment_line is not None:
        raise InputError(f"{path}:{comment_line}: unterminated HTML comment")


def _document(file: InputFile) -> tuple[Requirement, ...]:
    try:
        text = file.path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise InputError(f"{file.relative_path}: byte {error.start}: invalid UTF-8") from error
    except OSError as error:
        raise InputError(f"{file.relative_path}: {error.strerror or error}") from error
    lines = text.split("\n")
    entries: list[Requirement] = []
    active: tuple[str, str, int] | None = None
    section = ""

    def finish(end: int) -> None:
        if active is None:
            return
        identifier, title, number = active
        body_lines = lines[number:end]
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()
        if not body_lines:
            raise InputError(f"{file.relative_path}:{number}: empty requirement body")
        entries.append(
            Requirement(
                identifier, title, "\n".join(body_lines), Source(file.relative_path, number)
            )
        )

    for number, level, heading in _headings(lines, file.relative_path):
        if level <= 3:
            finish(number - 1)
            active = None
        if level <= 2:
            section = heading if level == 2 else ""
        if level == 2 and heading in _UNSUPPORTED:
            raise InputError(
                f"{file.relative_path}:{number}: unsupported {heading}; "
                "use canonical specs or an ADDED-only tree"
            )
        if level != 3 or not heading.startswith("Requirement:"):
            continue
        location = f"{file.relative_path}:{number}"
        if section not in _SECTIONS:
            raise InputError(f"{location}: requirement outside a supported Requirements section")
        match = _REQUIREMENT.fullmatch(heading)
        if not match or not REQUIREMENT_ID.fullmatch(match[1]):
            raise InputError(
                f"{location}: expected Requirement: [ID] Title with a valid explicit ID"
            )
        active = (match[1], match[2], number)
    finish(len(lines))
    return tuple(entries)


def read_requirements(files: Iterable[InputFile]) -> tuple[Requirement, ...]:
    catalog: dict[str, Requirement] = {}
    for file in files:
        for requirement in _document(file):
            if previous := catalog.get(requirement.id):
                raise InputError(
                    f"{requirement.source}: duplicate ID {requirement.id}; "
                    f"first declared at {previous.source}"
                )
            catalog[requirement.id] = requirement
    if not catalog:
        raise InputError("specification input contains no requirements (or no selected spec files)")
    return tuple(catalog.values())
