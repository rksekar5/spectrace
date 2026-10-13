"""Extract literal requirement markers without importing or collecting tests."""

import ast
import tokenize
from collections.abc import Iterable

from spectrace.models import REQUIREMENT_ID, InputError, InputFile, Source, TestDefinition

type Function = ast.FunctionDef | ast.AsyncFunctionDef


def _attribute(node: ast.AST, name: str) -> bool:
    parts = name.split(".")
    for part in reversed(parts[1:]):
        if not isinstance(node, ast.Attribute) or node.attr != part:
            return False
        node = node.value
    return isinstance(node, ast.Name) and node.id == parts[0]


def _fixture(function: Function) -> bool:
    return any(
        _attribute(item.func if isinstance(item, ast.Call) else item, "pytest.fixture")
        for item in function.decorator_list
    )


def _definitions(tree: ast.Module) -> list[tuple[str, Function]]:
    definitions = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.name.startswith("test_") and not _fixture(node):
                definitions.append((node.name, node))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            methods = [
                item
                for item in node.body
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
            ]
            if any(item.name in {"__init__", "__new__"} for item in methods):
                continue
            definitions.extend(
                (f"{node.name}::{item.name}", item)
                for item in methods
                if item.name.startswith("test_") and not _fixture(item)
            )
    return definitions


def _literal_ids(node: ast.AST) -> frozenset[str]:
    if not isinstance(node, ast.Call) or not node.args or node.keywords:
        raise InputError(
            "requirements marker needs one or more positional literal IDs; no keywords"
        )
    ids = set()
    for argument in node.args:
        if (
            not isinstance(argument, ast.Constant)
            or not isinstance(argument.value, str)
            or not REQUIREMENT_ID.fullmatch(argument.value)
        ):
            raise InputError("requirements marker arguments must be valid literal string IDs")
        ids.add(argument.value)
    return frozenset(ids)


def _document(file: InputFile) -> tuple[TestDefinition, ...]:
    try:
        with tokenize.open(file.path) as stream:
            tree = ast.parse(stream.read(), filename=file.relative_path, feature_version=(3, 12))
    except SyntaxError as error:
        location = f"{file.relative_path}:{error.lineno or 1}"
        raise InputError(f"{location}: invalid Python source: {error.msg}") from error
    except UnicodeError as error:
        raise InputError(
            f"{file.relative_path}: invalid Python source encoding: {error}"
        ) from error
    except OSError as error:
        raise InputError(f"{file.relative_path}: {error.strerror or error}") from error

    definitions = _definitions(tree)
    allowed: set[int] = set()
    references: dict[int, set[str]] = {}
    errors: list[tuple[int, int, str]] = []
    seen: dict[str, int] = {}
    for name, function in definitions:
        references[id(function)] = set()
        if name in seen:
            errors.append(
                (
                    function.lineno,
                    function.col_offset,
                    f"duplicate test identifier {file.relative_path}::{name}; "
                    f"first declared at {file.relative_path}:{seen[name]}",
                )
            )
        else:
            seen[name] = function.lineno
        for decorator in function.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if not _attribute(target, "pytest.mark.requirements"):
                continue
            allowed.add(id(target))
            try:
                references[id(function)].update(_literal_ids(decorator))
            except InputError as error:
                errors.append((decorator.lineno, decorator.col_offset, str(error)))

    for node in ast.walk(tree):
        if _attribute(node, "pytest.mark.requirements") and id(node) not in allowed:
            errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    "requirements markers must directly decorate supported test definitions",
                )
            )
    if errors:
        line, _, message = min(errors)
        raise InputError(f"{file.relative_path}:{line}: {message}")
    return tuple(
        TestDefinition(
            f"{file.relative_path}::{name}",
            Source(file.relative_path, function.lineno),
            frozenset(references[id(function)]),
        )
        for name, function in definitions
    )


def read_tests(files: Iterable[InputFile]) -> tuple[TestDefinition, ...]:
    return tuple(test for file in files for test in _document(file))
