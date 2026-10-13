"""Source declarations shared by discovery, parsing, and reporting."""

import re
from dataclasses import dataclass
from pathlib import Path

REQUIREMENT_ID = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+")


class InputError(Exception):
    """An expected input/output failure suitable for a concise CLI diagnostic."""


@dataclass(frozen=True)
class Source:
    path: str
    line: int

    def __str__(self) -> str:
        return f"{self.path}:{self.line}"


@dataclass(frozen=True)
class InputFile:
    path: Path
    relative_path: str


@dataclass(frozen=True)
class Requirement:
    id: str
    title: str
    body: str
    source: Source


@dataclass(frozen=True)
class TestDefinition:
    id: str
    source: Source
    requirements: frozenset[str]
