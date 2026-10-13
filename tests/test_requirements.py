from pathlib import Path

import pytest

from spectrace.discovery import discover
from spectrace.models import InputError
from spectrace.requirements import read_requirements


def catalog(path):
    return read_requirements(discover(path, "spec"))


@pytest.mark.requirements("ST-CAT-002", "ST-CAT-003", "ST-CAT-004")
@pytest.mark.parametrize("section", ["Requirements", "ADDED Requirements"])
def test_canonical_and_added_requirements_preserve_content(write_file, section):
    path = write_file(
        "requirements.md",
        f"## {section}\n\n### Requirement: [REQ-A] First\n\nThe app SHALL act.\n"
        "\n#### Scenario: First\n- **WHEN** used\n- **THEN** it acts\n"
        "\n### Requirement: [REQ-B] Second\nAnother body.\n",
    )
    first, second = catalog(path)
    assert (first.id, first.title, str(first.source)) == ("REQ-A", "First", "requirements.md:3")
    assert (
        first.body
        == "The app SHALL act.\n\n#### Scenario: First\n- **WHEN** used\n- **THEN** it acts"
    )
    assert second.body == "Another body."


@pytest.mark.requirements("ST-CAT-002")
@pytest.mark.parametrize("fence", ["```python", "~~~markdown", "   ````text"])
def test_ignore_fenced_examples_and_comments(write_file, fence):
    closing = fence.strip().split("python")[0].split("markdown")[0].split("text")[0]
    path = write_file(
        "spec.md",
        f"## Requirements\n### Requirement: [REQ-A] Real\nBody\n{fence}\n"
        "### Requirement: [REQ-FAKE] Example\n## REMOVED Requirements\n"
        f"<!-- unclosed inside code\n{closing}\n<!--\n"
        "### Requirement: [REQ-FAKE] Comment\n```\n-->\n"
        "### Requirement: [REQ-B] Also real\nBody\n",
    )
    requirements = catalog(path)
    assert [item.id for item in requirements] == ["REQ-A", "REQ-B"]
    assert "REQ-FAKE" in requirements[0].body


@pytest.mark.requirements("ST-CAT-002")
def test_fence_closing_must_match_character_length_and_suffix(write_file):
    path = write_file(
        "spec.md",
        "## Requirements\n### Requirement: [REQ-A] Real\nBody\n````python\n"
        "```\n~~~\n````text\n### Requirement: [REQ-FAKE] Still fenced\n"
        "`````\n### Requirement: [REQ-B] Real\nBody\n",
    )
    assert [item.id for item in catalog(path)] == ["REQ-A", "REQ-B"]


@pytest.mark.requirements("ST-CAT-002")
@pytest.mark.parametrize("section", ["MODIFIED", "REMOVED", "RENAMED"])
def test_reject_delta_operations(write_file, section):
    path = write_file(
        "spec.md", f"## {section} Requirements\n### Requirement: [REQ-A] Test\nBody\n"
    )
    with pytest.raises(InputError, match="spec.md:1:.*canonical specs or an ADDED-only tree"):
        catalog(path)


@pytest.mark.requirements("ST-CAT-002")
def test_reject_misplaced_heading(write_file):
    path = write_file("spec.md", "# Title\n### Requirement: [REQ-A] Outside\nBody\n")
    with pytest.raises(InputError, match="spec.md:2:.*outside"):
        catalog(path)


@pytest.mark.requirements("ST-CAT-003")
@pytest.mark.parametrize(
    "heading",
    [
        "Missing ID",
        "[] Empty",
        "[REQ-A]",
        "[req-auth-001] Title",
        "[REQ_001] Title",
        "[REQ 001] Title",
        "[REQ] Title",
    ],
)
def test_reject_invalid_id_or_title(write_file, heading):
    path = write_file("spec.md", f"## Requirements\n### Requirement: {heading}\nBody\n")
    with pytest.raises(InputError, match="spec.md:2:.*explicit ID"):
        catalog(path)


@pytest.mark.requirements("ST-CAT-003")
def test_id_does_not_depend_on_title(write_file):
    one = catalog(
        write_file("a.md", "## Requirements\n### Requirement: [REQ-AUTH-001] Old\nBody\n")
    )[0]
    two = catalog(
        write_file("b.md", "## Requirements\n### Requirement: [REQ-AUTH-001] New\nBody\n")
    )[0]
    assert one.id == two.id == "REQ-AUTH-001"
    assert one.title != two.title


@pytest.mark.requirements("ST-CAT-004")
@pytest.mark.parametrize("ending", ["# End", "## End", "### End"])
def test_body_boundaries_and_line_endings(write_file, ending):
    path = write_file(
        "spec.md",
        "## Requirements\r\n### Requirement: [REQ-A] Title\r\n\r\nBody\r\n"
        f"#### Scenario: Example\r\nDetails\r\n\r\n{ending}\r\nUnrelated\r\n",
    )
    requirement = catalog(path)[0]
    assert requirement.body == "Body\n#### Scenario: Example\nDetails"
    assert requirement.source.line == 2


@pytest.mark.requirements("ST-CAT-004")
@pytest.mark.parametrize("tail", ["", "### Another heading\nBody\n"])
def test_reject_empty_body(write_file, tail):
    path = write_file("spec.md", "## Requirements\n### Requirement: [REQ-A] Empty\n \n" + tail)
    with pytest.raises(InputError, match="spec.md:2: empty requirement body"):
        catalog(path)


@pytest.mark.requirements("ST-CAT-005")
@pytest.mark.parametrize("across_files", [False, True])
def test_duplicate_id_names_both_locations(tmp_path, write_file, across_files):
    text = "## Requirements\n### Requirement: [REQ-A] Same\nBody\n"
    first = write_file("a/spec.md", text if across_files else text + text)
    if across_files:
        write_file("b/spec.md", text)
    with pytest.raises(InputError) as error:
        catalog(tmp_path if across_files else first)
    assert "duplicate ID REQ-A" in str(error.value)
    assert "first declared at" in str(error.value)
    assert ("a/spec.md:2" if across_files else "spec.md:2") in str(error.value)
    assert ("b/spec.md:2" if across_files else "spec.md:5") in str(error.value)


@pytest.mark.requirements("ST-CAT-005")
def test_empty_tree_and_zero_requirement_document(tmp_path, write_file):
    with pytest.raises(InputError, match="no requirements"):
        catalog(tmp_path)
    with pytest.raises(InputError, match="no requirements"):
        catalog(write_file("spec.md", "# Notes\nNothing here\n"))


@pytest.mark.requirements("ST-CAT-005")
@pytest.mark.parametrize("suffix", ["```python\n", "~~~\n", "<!-- unfinished\n"])
def test_unterminated_fence_or_comment(write_file, suffix):
    path = write_file("spec.md", "## Requirements\n### Requirement: [REQ-A] Valid\nBody\n" + suffix)
    with pytest.raises(InputError, match="spec.md:4: unterminated"):
        catalog(path)


@pytest.mark.requirements("ST-CAT-005")
def test_invalid_utf8_and_read_failure(write_file, monkeypatch):
    path = write_file("spec.md")
    path.write_bytes(b"\xff")
    with pytest.raises(InputError, match="spec.md: byte 0: invalid UTF-8"):
        catalog(path)

    def denied(self, **kwargs):
        raise PermissionError(13, "Permission denied", str(self))

    monkeypatch.setattr(Path, "read_text", denied)
    with pytest.raises(InputError, match="spec.md: Permission denied"):
        catalog(path)


@pytest.mark.requirements("ST-CAT-002", "ST-CAT-003")
def test_approved_change_is_an_added_only_catalog():
    root = Path(__file__).resolve().parents[1]
    requirements = catalog(root / "openspec/changes/bootstrap-spectrace/specs")
    assert len(requirements) == 18
    assert len({item.id for item in requirements}) == 18


@pytest.mark.requirements("ST-CAT-002", "ST-CAT-003", "ST-CAT-004")
def test_documented_requirement_example(write_file):
    root = Path(__file__).resolve().parents[1]
    docs = (root / "docs/input-formats.md").read_text()
    sample = docs.split("```markdown\n", 1)[1].split("```", 1)[0]
    requirement = catalog(write_file("documented.md", sample))[0]
    assert requirement.id == "REQ-AUTH-001"
    assert requirement.title == "Reject invalid passwords"
    assert "#### Scenario: Invalid password" in requirement.body
