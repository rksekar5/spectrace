from pathlib import Path

import pytest

from spectrace.mapping import resolve_links
from spectrace.models import Requirement, Source
from spectrace.models import TestDefinition as Definition
from spectrace.report import render_markdown


def requirements():
    return tuple(
        Requirement(f"REQ-{letter}", title, "Body", Source("demo/spec.md", number))
        for letter, title, number in [("A", "First", 3), ("B", "Second", 6), ("C", "Third", 9)]
    )


def sample_tests(unknown=False):
    return (
        Definition(
            "test_demo.py::test_a", Source("test_demo.py", 5), frozenset({"REQ-A", "REQ-B"})
        ),
        Definition(
            "test_demo.py::test_b",
            Source("test_demo.py", 10),
            frozenset({"REQ-A", "REQ-TYPO"} if unknown else {"REQ-A"}),
        ),
    )


@pytest.mark.requirements("ST-RPT-001", "ST-RPT-002", "ST-RPT-003")
def test_many_to_many_mapping_and_counts():
    report = resolve_links(requirements(), sample_tests())
    assert [[test.id for test in row.tests] for row in report.rows] == [
        ["test_demo.py::test_a", "test_demo.py::test_b"],
        ["test_demo.py::test_a"],
        [],
    ]
    assert [item.id for item in report.unlinked] == ["REQ-C"]
    markdown = render_markdown(report)
    for summary in [
        "Requirements: 3",
        "Linked requirements: 2",
        "Unlinked requirements: 1",
        "Discovered tests: 2",
        "Linked tests: 2",
        "Resolved links: 3",
        "Unknown references: 0",
    ]:
        assert summary in markdown


@pytest.mark.requirements("ST-RPT-001", "ST-RPT-003")
@pytest.mark.parametrize("with_test", [False, True])
def test_no_explicit_links_means_all_requirements_unlinked(with_test):
    tests = (
        (Definition("test_demo.py::test_REQ_A", Source("test_demo.py", 1), frozenset()),)
        if with_test
        else ()
    )
    report = resolve_links(requirements(), tests)
    assert [item.id for item in report.unlinked] == ["REQ-A", "REQ-B", "REQ-C"]
    markdown = render_markdown(report)
    assert f"Discovered tests: {int(with_test)}" in markdown
    assert "Resolved links: 0" in markdown
    assert markdown.count("| UNLINKED |") == 3


@pytest.mark.requirements("ST-RPT-002", "ST-RPT-001")
def test_unknown_pairs_do_not_create_requirements_or_resolved_links():
    tests = sample_tests(unknown=True)
    report = resolve_links(requirements(), tests)
    assert [(item.id, item.test.id) for item in report.unknown] == [
        ("REQ-TYPO", "test_demo.py::test_b")
    ]
    assert len(report.rows) == 3
    assert sum(len(row.tests) for row in report.rows) == 3
    assert len(report.rows[0].tests) == 2


@pytest.mark.requirements("ST-RPT-002", "ST-RPT-003", "ST-RPT-004")
def test_complete_documented_report_matches_expected_fixture():
    expected = (Path(__file__).resolve().parents[1] / "docs/example-report.md").read_text()
    assert render_markdown(resolve_links(requirements(), sample_tests(unknown=True))) == expected


@pytest.mark.requirements("ST-RPT-003")
def test_empty_gap_sections_and_static_limitation():
    report = resolve_links(requirements()[:2], sample_tests())
    markdown = render_markdown(report)
    assert "## Unlinked Requirements\n\nNone\n" in markdown
    assert "## Unknown References\n\nNone\n" in markdown
    assert "do not prove collection, execution," in markdown
    assert "passing tests, or behavioral coverage" in markdown
    assert "COVERED" not in markdown and "PASS" not in markdown


@pytest.mark.requirements("ST-RPT-004")
def test_order_independence_and_portable_output():
    normal = render_markdown(resolve_links(requirements(), sample_tests(unknown=True)))
    reversed_input = render_markdown(
        resolve_links(reversed(requirements()), reversed(sample_tests(unknown=True)))
    )
    assert normal.encode("utf-8") == reversed_input.encode("utf-8")
    assert normal.endswith("\n") and "\r" not in normal
    assert "/workspace" not in normal and "/tmp" not in normal


@pytest.mark.requirements("ST-RPT-004")
def test_source_text_cannot_create_columns_html_or_markdown_links():
    source = Source("a|`&<tag>\nfile.md", 1)
    requirement = Requirement("REQ-A", "<script>|`&\r\n[link](target)*", "Body", source)
    markdown = render_markdown(resolve_links([requirement], []))
    row = next(line for line in markdown.splitlines() if line.startswith("| REQ-A"))
    assert row.count("|") == 6
    assert "&lt;script&gt;&#124;&#96;&amp;  &#91;link&#93;&#40;target&#41;&#42;" in row
    assert "a&#124;&#96;&amp;&lt;tag&gt; file.md:1" in row
    assert "<script>" not in markdown and "[link](target)" not in markdown


@pytest.mark.requirements("ST-RPT-002", "ST-RPT-004")
def test_unknown_references_sort_by_id_then_test():
    tests = (
        Definition("z_test.py::test_z", Source("z_test.py", 2), frozenset({"REQ-Z", "REQ-X"})),
        Definition("a_test.py::test_a", Source("a_test.py", 3), frozenset({"REQ-X"})),
    )
    report = resolve_links(requirements(), tests)
    assert [(item.id, item.test.id) for item in report.unknown] == [
        ("REQ-X", "a_test.py::test_a"),
        ("REQ-X", "z_test.py::test_z"),
        ("REQ-Z", "z_test.py::test_z"),
    ]
    assert "Linked tests: 0" in render_markdown(report)
