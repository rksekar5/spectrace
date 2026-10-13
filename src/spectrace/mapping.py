"""Resolve explicit source associations; no execution or coverage inference."""

from collections.abc import Iterable
from dataclasses import dataclass

from spectrace.models import Requirement, TestDefinition


@dataclass(frozen=True)
class RequirementTrace:
    requirement: Requirement
    tests: tuple[TestDefinition, ...]


@dataclass(frozen=True)
class UnknownReference:
    id: str
    test: TestDefinition


@dataclass(frozen=True)
class TraceReport:
    rows: tuple[RequirementTrace, ...]
    tests: tuple[TestDefinition, ...]
    unknown: tuple[UnknownReference, ...]

    @property
    def unlinked(self) -> tuple[Requirement, ...]:
        return tuple(row.requirement for row in self.rows if not row.tests)


def resolve_links(
    requirements: Iterable[Requirement], tests: Iterable[TestDefinition]
) -> TraceReport:
    catalog = {item.id: item for item in requirements}
    discovered = tuple(sorted(tests, key=lambda item: item.id))
    links: dict[str, dict[str, TestDefinition]] = {identifier: {} for identifier in catalog}
    unknown: dict[tuple[str, str], UnknownReference] = {}
    for test in discovered:
        for identifier in test.requirements:
            if identifier in catalog:
                links[identifier][test.id] = test
            else:
                unknown[(identifier, test.id)] = UnknownReference(identifier, test)
    return TraceReport(
        tuple(
            RequirementTrace(catalog[identifier], tuple(links[identifier].values()))
            for identifier in sorted(catalog)
        ),
        discovered,
        tuple(unknown[key] for key in sorted(unknown)),
    )
