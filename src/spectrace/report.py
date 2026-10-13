"""Pure, deterministic Markdown rendering."""

import html

from spectrace.mapping import TraceReport


def _cell(value: str) -> str:
    value = html.escape(value, quote=False).replace("\r", " ").replace("\n", " ")
    # Entities keep source text literal in Markdown, including link syntax.
    for character in "|`\\[]()*_~!":
        value = value.replace(character, f"&#{ord(character)};")
    return value


def render_markdown(report: TraceReport) -> str:
    linked = sum(bool(row.tests) for row in report.rows)
    linked_tests = {test.id for row in report.rows for test in row.tests}
    lines = [
        "# SpecTrace Traceability Report",
        "",
        "Links are declared source associations. They do not prove collection, execution,",
        "passing tests, or behavioral coverage. Tests are represented at definition granularity.",
        "Paths are relative to the selected specification and test roots.",
        "",
        "## Summary",
        "",
        f"- Requirements: {len(report.rows)}",
        f"- Linked requirements: {linked}",
        f"- Unlinked requirements: {len(report.rows) - linked}",
        f"- Discovered tests: {len(report.tests)}",
        f"- Linked tests: {len(linked_tests)}",
        f"- Resolved links: {sum(len(row.tests) for row in report.rows)}",
        f"- Unknown references: {len(report.unknown)}",
        "",
        "## Requirements",
        "",
        "| ID | Title | Specification | Tests (definition line) | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report.rows:
        requirement = row.requirement
        tests = "; ".join(f"{test.id} (line {test.source.line})" for test in row.tests) or "None"
        status = "LINKED" if row.tests else "UNLINKED"
        cells = (requirement.id, requirement.title, str(requirement.source), tests, status)
        lines.append("| " + " | ".join(_cell(cell) for cell in cells) + " |")
    lines.extend(["", "## Unlinked Requirements", ""])
    if report.unlinked:
        lines.extend(
            f"- {_cell(item.id)}: {_cell(item.title)} ({_cell(str(item.source))})"
            for item in report.unlinked
        )
    else:
        lines.append("None")
    lines.extend(["", "## Unknown References", ""])
    if report.unknown:
        lines.extend(["| ID | Test | Source |", "| --- | --- | --- |"])
        lines.extend(
            "| "
            + " | ".join(_cell(cell) for cell in (item.id, item.test.id, str(item.test.source)))
            + " |"
            for item in report.unknown
        )
    else:
        lines.append("None")
    return "\n".join(lines) + "\n"
