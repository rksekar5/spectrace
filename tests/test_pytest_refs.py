from pathlib import Path

import pytest

from spectrace.discovery import discover
from spectrace.models import InputError
from spectrace.pytest_refs import read_tests


def scan(path):
    return read_tests(discover(path, "test"))


@pytest.mark.requirements("ST-TST-001", "ST-TST-002")
def test_functions_methods_async_and_source_locations(write_file):
    path = write_file(
        "tests/test_auth.py",
        """import pytest
@pytest.mark.requirements("REQ-A", "REQ-B")
def test_login(): pass
class TestAuth:
    @pytest.mark.requirements("REQ-B")
    async def test_logout(self): pass
""",
    )
    tests = scan(path.parent)
    assert [item.id for item in tests] == [
        "test_auth.py::test_login",
        "test_auth.py::TestAuth::test_logout",
    ]
    assert [item.source.line for item in tests] == [3, 6]
    assert tests[0].requirements == {"REQ-A", "REQ-B"}
    assert tests[1].requirements == {"REQ-B"}


@pytest.mark.requirements("ST-TST-001")
def test_exclude_unsupported_definitions_and_fixtures(write_file):
    path = write_file(
        "test_profile.py",
        """
def helper():
    def test_nested(): pass
class Other:
    def test_not_collected(self): pass
class TestInherited(Other): pass
class TestInit:
    def __init__(self): pass
    def test_not_collected(self): pass
class TestNew:
    def __new__(cls): pass
    def test_not_collected(self): pass
@pytest.fixture
def test_fixture(): pass
@pytest.fixture()
def test_other_fixture(): pass
if True:
    def test_conditional(): pass
async def test_real(): pass
""",
    )
    assert [item.id for item in scan(path)] == ["test_profile.py::test_real"]


@pytest.mark.requirements("ST-TST-001")
def test_empty_tree_and_single_file_identifiers(tmp_path, write_file):
    assert scan(tmp_path) == ()
    path = write_file("unit/test_one.py", "def helper(): pass\n")
    assert scan(path) == ()
    path.write_text("def test_one(): pass\n")
    assert scan(path)[0].id == "test_one.py::test_one"


@pytest.mark.requirements("ST-TST-002")
def test_deduplicate_multiple_decorators(write_file):
    path = write_file(
        "test_links.py",
        """
@pytest.mark.requirements("REQ-A", "REQ-A")
@pytest.mark.requirements("REQ-A", "REQ-B")
def test_links(): pass
""",
    )
    assert scan(path)[0].requirements == {"REQ-A", "REQ-B"}


@pytest.mark.requirements("ST-TST-003")
def test_names_comments_docstrings_assertions_and_aliases_are_not_links(write_file):
    path = write_file(
        "test_REQ_AUTH_001.py",
        '''
import pytest as pt
from pytest import mark
# REQ-AUTH-001
@pt.mark.requirements("REQ-AUTH-001")
@requirements("REQ-AUTH-001")
@mark.requirements("REQ-AUTH-001")
def test_REQ_AUTH_001():
    """REQ-AUTH-001 @pytest.mark.requirements('REQ-AUTH-001')"""
    value = "REQ-AUTH-001"
    assert value, "REQ-AUTH-001"
''',
    )
    tests = scan(path)
    assert len(tests) == 1
    assert tests[0].requirements == frozenset()


@pytest.mark.requirements("ST-TST-004")
@pytest.mark.parametrize(
    "arguments",
    [
        "",
        "ids",
        "f'REQ-{number}'",
        "['REQ-A']",
        "*ids",
        "id='REQ-A'",
        "1",
        "''",
        "'req-a'",
        "'REQ_A'",
        "'REQ A'",
        "'REQ-A' + '-B'",
    ],
)
def test_reject_invalid_marker_arguments(write_file, arguments):
    path = write_file(
        "test_bad.py", f"@pytest.mark.requirements({arguments})\ndef test_bad(): pass\n"
    )
    with pytest.raises(InputError, match="test_bad.py:1:.*marker"):
        scan(path)


@pytest.mark.requirements("ST-TST-004")
def test_reject_bare_marker(write_file):
    path = write_file("test_bad.py", "@pytest.mark.requirements\ndef test_bad(): pass\n")
    with pytest.raises(InputError, match="test_bad.py:1:.*positional literal IDs"):
        scan(path)


@pytest.mark.requirements("ST-TST-004")
@pytest.mark.parametrize(
    "source",
    [
        'pytestmark = pytest.mark.requirements("REQ-A")',
        '@pytest.mark.requirements("REQ-A")\nclass TestBad: pass',
        '@pytest.mark.requirements("REQ-A")\ndef helper(): pass',
        'case = pytest.param(1, marks=pytest.mark.requirements("REQ-A"))',
        'class TestBad:\n    pytestmark = pytest.mark.requirements("REQ-A")',
        '@pytest.fixture\n@pytest.mark.requirements("REQ-A")\ndef test_fixture(): pass',
        "marker = pytest.mark.requirements",
    ],
)
def test_reject_recognized_marker_in_unsupported_scope(write_file, source):
    with pytest.raises(InputError, match="test_bad.py:.*directly decorate"):
        scan(write_file("test_bad.py", source))


@pytest.mark.requirements("ST-TST-005")
def test_no_imports_collection_or_source_execution(tmp_path, write_file):
    sentinel = tmp_path / "executed"
    source = f"""import unavailable_dependency_spectrace_probe
from pathlib import Path
Path({str(sentinel)!r}).write_text("executed")
raise RuntimeError("must not execute")
@pytest.mark.requirements("REQ-A")
def test_safe(): pass
"""
    path = write_file("tests/test_safe.py", source)
    write_file("tests/conftest.py", f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\n")
    tests = scan(path.parent)
    assert len(tests) == 1
    assert tests[0].requirements == {"REQ-A"}
    assert not sentinel.exists()


@pytest.mark.requirements("ST-TST-005")
@pytest.mark.parametrize(
    "source",
    [
        b"def test_bad(:\n",
        b"# coding: utf-8\n# \xff\n",
        b"# coding: no-such-codec\n",
        b"x = '\x00'\n",
    ],
)
def test_invalid_python_or_encoding(write_file, source):
    path = write_file("test_bad.py")
    path.write_bytes(source)
    with pytest.raises(InputError, match="test_bad.py:.*invalid Python source"):
        scan(path)


@pytest.mark.requirements("ST-TST-005")
def test_encoding_declaration_is_respected(write_file):
    path = write_file("test_latin.py")
    path.write_bytes(
        b'# coding: latin-1\n# caf\xe9\n@pytest.mark.requirements("REQ-A")\ndef test_one(): pass\n'
    )
    assert scan(path)[0].requirements == {"REQ-A"}


@pytest.mark.requirements("ST-TST-005")
@pytest.mark.parametrize(
    "source,first,second",
    [
        ("def test_one(): pass\ndef test_one(): pass\n", 1, 2),
        ("class TestOne:\n    def test_one(self): pass\n    def test_one(self): pass\n", 2, 3),
        (
            "class TestOne:\n    def test_one(self): pass\n"
            "class TestOne:\n    def test_one(self): pass\n",
            2,
            4,
        ),
    ],
)
def test_duplicate_identifiers_are_errors(write_file, source, first, second):
    with pytest.raises(InputError) as error:
        scan(write_file("test_duplicate.py", source))
    assert f"test_duplicate.py:{second}: duplicate test identifier" in str(error.value)
    assert f"first declared at test_duplicate.py:{first}" in str(error.value)


@pytest.mark.requirements("ST-TST-005")
def test_unreadable_test_source(write_file, monkeypatch):
    import tokenize

    path = write_file("test_unreadable.py")

    def denied(path):
        raise PermissionError(13, "Permission denied", str(path))

    monkeypatch.setattr(tokenize, "open", denied)
    with pytest.raises(InputError, match="test_unreadable.py: Permission denied"):
        scan(path)


@pytest.mark.requirements("ST-TST-006", "ST-TST-002")
@pytest.mark.parametrize(
    "marker", ["parametrize('value', range(10))", "skip", "skipif(True, reason='example')", "xfail"]
)
def test_runtime_markers_do_not_expand_or_remove_static_links(write_file, marker):
    path = write_file(
        "test_cases.py",
        f'@pytest.mark.{marker}\n@pytest.mark.requirements("REQ-A")\ndef test_cases(): pass\n',
    )
    tests = scan(path)
    assert len(tests) == 1
    assert tests[0].id == "test_cases.py::test_cases"
    assert tests[0].requirements == {"REQ-A"}


@pytest.mark.requirements("ST-TST-002", "ST-TST-003")
def test_documented_test_example(write_file):
    docs = (Path(__file__).resolve().parents[1] / "docs/input-formats.md").read_text()
    sample = docs.split("```python\n", 1)[1].split("```", 1)[0]
    tests = scan(write_file("test_documented.py", sample))
    assert tests[0].requirements == {"REQ-AUTH-001"}
