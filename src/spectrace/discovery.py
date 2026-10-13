"""Bounded, deterministic source discovery without following symbolic links."""

import os
import stat
from pathlib import Path
from typing import Literal

from spectrace.models import InputError, InputFile


def _test_filename(name: str) -> bool:
    return name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def discover(root: Path, kind: Literal["spec", "test"]) -> tuple[InputFile, ...]:
    """Select a single regular input or matching files beneath a directory."""
    try:
        if root.is_symlink():
            raise InputError(f"{root}: symbolic-link input roots are not supported")
        mode = root.stat().st_mode
        if stat.S_ISREG(mode):
            valid = root.suffix == ".md" if kind == "spec" else _test_filename(root.name)
            if not valid:
                raise InputError(f"{root}: unsupported {kind} input filename")
            return (InputFile(root, root.name),)
        if not stat.S_ISDIR(mode):
            raise InputError(f"{root}: expected a regular file or directory")

        def traversal_error(error: OSError) -> None:
            raise error

        files = []
        for directory, dirs, names in os.walk(root, onerror=traversal_error, followlinks=False):
            parent = Path(directory)
            dirs[:] = sorted(
                name
                for name in dirs
                if not name.startswith(".") and not (parent / name).is_symlink()
            )
            for name in sorted(names):
                matches = name == "spec.md" if kind == "spec" else _test_filename(name)
                if not matches:
                    continue
                path = parent / name
                if path.is_symlink():
                    continue
                if not stat.S_ISREG(path.stat().st_mode):
                    raise InputError(f"{path}: selected input is not a regular file")
                files.append(InputFile(path, path.relative_to(root).as_posix()))
        return tuple(sorted(files, key=lambda item: item.relative_path))
    except OSError as error:
        raise InputError(f"{error.filename or root}: {error.strerror or error}") from error
