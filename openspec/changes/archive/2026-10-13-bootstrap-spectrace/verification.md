# Verification: bootstrap-spectrace

Performed with the `openspec-verify-change` workflow against the approved proposal,
three delta specifications, design, task checklist, implementation, and executed
tests. The change remains active and unarchived; merging requires review.

## Summary

| Dimension | Result |
| --- | --- |
| Completeness | 21/21 implementation tasks verified; all 18 ADDED requirements implemented |
| Correctness | All 51 acceptance scenarios have executed test evidence, mapped below |
| Coherence | Approved module boundaries, static parsing, explicit IDs, offline runtime, and deterministic reporting preserved |

No critical findings, warnings, or suggestions remain. No applicable verification
checks were skipped. This is implementation-review evidence, not authorization to
merge or archive.

## Executed checks

- Python 3.12.14: `python -m pytest -q` — **127 passed, 0 failed, 0 errors, 0 skipped**.
- `ruff check .` and `ruff format --check .` — passed.
- `openspec validate bootstrap-spectrace --strict --no-interactive` — passed.
- `openspec doctor --json` — healthy local OpenSpec root.
- Editable install with the pinned development extra in a fresh Python 3.12
  environment; package import and console entry point worked outside the checkout.
- `python -m build` — sdist and wheel built successfully using isolated build
  environments. The wheel was rebuilt after the stdout regression fix.
- Installed the final wheel into a separate environment with **only the spectrace
  distribution**. Help/version and the documented example worked outside the
  checkout; exact Markdown bytes and exit status 1 matched expectations.
- The installed wheel returns status 2 for a closed stdout pipe, without an
  interpreter shutdown exception. The source regression also checks unencodable
  filenames and preservation of a previous output file.
- Self-trace against the change's ADDED-only specs and real test sources:
  **18 requirements, 18 linked, 0 unlinked, 62 static test definitions,
  105 explicit resolved links, 0 unknown references**. Parametrized test cases
  account for the larger executed pytest count.

The self-trace is evidence of declared associations only. Actual assertions and
the independently executed pytest results establish the scenario evidence below;
the tool does not interpret test outcomes or infer links from names.

## Requirement implementation mapping

| Requirement | Implementation evidence |
| --- | --- |
| ST-CAT-001 | `src/spectrace/discovery.py:15` — bounded, sorted input selection |
| ST-CAT-002 | `src/spectrace/requirements.py:15` and `:63` — fences/comments, supported sections, delta rejection |
| ST-CAT-003 | `src/spectrace/models.py:7` and `requirements.py:63` — explicit ID grammar and title validation |
| ST-CAT-004 | `src/spectrace/requirements.py:63` — bodies, boundaries, normalization, source lines |
| ST-CAT-005 | `src/spectrace/requirements.py:118`, `:63`, and `discovery.py:15` — duplicate/empty/invalid input errors |
| ST-TST-001 | `src/spectrace/discovery.py:15` and `pytest_refs.py:28` — conventional static definitions |
| ST-TST-002 | `src/spectrace/pytest_refs.py:50` and `:67` — literal markers, sets, source locations |
| ST-TST-003 | `src/spectrace/pytest_refs.py:12` and `:67` — exact AST shape, no textual inference or aliases |
| ST-TST-004 | `src/spectrace/pytest_refs.py:50` and `:67` — malformed and misplaced marker diagnostics |
| ST-TST-005 | `src/spectrace/pytest_refs.py:67` — encoding-aware AST parsing without imports or collection |
| ST-TST-006 | `src/spectrace/pytest_refs.py:28` and `:67` — one record per supported definition |
| ST-RPT-001 | `src/spectrace/mapping.py:32` — explicit many-to-many joins and gaps |
| ST-RPT-002 | `src/spectrace/mapping.py:32` and `cli.py:81` — unknown pairs and status 1 |
| ST-RPT-003 | `src/spectrace/report.py:16` — complete sections, counts, and static limitation |
| ST-RPT-004 | `src/spectrace/report.py:8`, `:16`, and `mapping.py:32` — escaping and stable ordering |
| ST-RPT-005 | `src/spectrace/cli.py:54`, `:81`, and `pyproject.toml` — local installed command and interface |
| ST-RPT-006 | `src/spectrace/cli.py:18` and `:81` — output failures, diagnostics, and exit precedence |
| ST-RPT-007 | `src/spectrace/cli.py:30` — collision checks and complete temporary-file replacement |

## Acceptance scenario evidence

Test references below name executed tests, not inferred requirement links. Their
source definitions also contain explicit `pytest.mark.requirements` annotations.
Parametrized references include all applicable executed cases.

| Requirement | Approved scenario | Executed test evidence |
| --- | --- | --- |
| ST-CAT-001 | Select the canonical specification tree | `test_discovery.py::test_bounded_sorted_discovery` |
| ST-CAT-001 | Select a single document | `test_discovery.py::test_single_file_uses_basename` |
| ST-CAT-001 | Avoid hidden files and linked trees | `test_discovery.py::test_bounded_sorted_discovery`; `test_discovery.py::test_reject_symlink_root` |
| ST-CAT-002 | Read a canonical specification | `test_requirements.py::test_canonical_and_added_requirements_preserve_content` |
| ST-CAT-002 | Read this proposed change explicitly | `test_requirements.py::test_approved_change_is_an_added_only_catalog` |
| ST-CAT-002 | Ignore examples | `test_requirements.py::test_ignore_fenced_examples_and_comments`; `test_requirements.py::test_fence_closing_must_match_character_length_and_suffix` |
| ST-CAT-002 | Reject a delta requiring baseline resolution | `test_requirements.py::test_reject_delta_operations` |
| ST-CAT-002 | Reject a misplaced requirement | `test_requirements.py::test_reject_misplaced_heading` |
| ST-CAT-003 | Extract a valid heading | `test_requirements.py::test_documented_requirement_example` |
| ST-CAT-003 | Reject absent or malformed identifiers | `test_requirements.py::test_reject_invalid_id_or_title` |
| ST-CAT-003 | Retain identity when a title changes | `test_requirements.py::test_id_does_not_depend_on_title` |
| ST-CAT-004 | Preserve a multiline requirement | `test_requirements.py::test_body_boundaries_and_line_endings` |
| ST-CAT-004 | Reject an empty requirement | `test_requirements.py::test_reject_empty_body` |
| ST-CAT-005 | Reject duplicate requirement identity | `test_requirements.py::test_duplicate_id_names_both_locations` |
| ST-CAT-005 | Distinguish an empty catalog from successful traceability | `test_requirements.py::test_empty_tree_and_zero_requirement_document` |
| ST-CAT-005 | Report unreadable or malformed source | `test_requirements.py::test_invalid_utf8_and_read_failure`; `test_requirements.py::test_unterminated_fence_or_comment` |
| ST-TST-001 | Discover functions and class methods | `test_pytest_refs.py::test_functions_methods_async_and_source_locations` |
| ST-TST-001 | Exclude unsupported definitions | `test_pytest_refs.py::test_exclude_unsupported_definitions_and_fixtures` |
| ST-TST-001 | Represent a single selected file | `test_pytest_refs.py::test_empty_tree_and_single_file_identifiers` |
| ST-TST-001 | Accept an empty existing test tree | `test_cli.py::test_empty_test_directory_exposes_all_gaps` |
| ST-TST-002 | Link one test to several requirements | `test_pytest_refs.py::test_functions_methods_async_and_source_locations` |
| ST-TST-002 | Deduplicate repeated markers | `test_pytest_refs.py::test_deduplicate_multiple_decorators` |
| ST-TST-002 | Preserve a marked method location | `test_pytest_refs.py::test_functions_methods_async_and_source_locations` |
| ST-TST-003 | Requirement-like names provide no evidence | `test_pytest_refs.py::test_names_comments_docstrings_assertions_and_aliases_are_not_links` |
| ST-TST-003 | Aliased markers do not silently establish links | `test_pytest_refs.py::test_names_comments_docstrings_assertions_and_aliases_are_not_links` |
| ST-TST-004 | Reject dynamic and malformed arguments | `test_pytest_refs.py::test_reject_invalid_marker_arguments` |
| ST-TST-004 | Reject an empty or bare marker | `test_pytest_refs.py::test_reject_invalid_marker_arguments`; `test_pytest_refs.py::test_reject_bare_marker` |
| ST-TST-004 | Reject unsupported scope | `test_pytest_refs.py::test_reject_recognized_marker_in_unsupported_scope` |
| ST-TST-005 | Source side effects never execute | `test_pytest_refs.py::test_no_imports_collection_or_source_execution`; `test_cli.py::test_explicit_roots_do_not_execute_scanned_code_or_conftest` |
| ST-TST-005 | Report invalid Python | `test_pytest_refs.py::test_invalid_python_or_encoding` |
| ST-TST-005 | Reject an ambiguous definition | `test_pytest_refs.py::test_duplicate_identifiers_are_errors` |
| ST-TST-006 | Parametrized test remains one definition | `test_pytest_refs.py::test_runtime_markers_do_not_expand_or_remove_static_links` |
| ST-TST-006 | Skipped test is a declared link only | `test_pytest_refs.py::test_runtime_markers_do_not_expand_or_remove_static_links`; `test_mapping_report.py::test_empty_gap_sections_and_static_limitation` |
| ST-RPT-001 | Build a many-to-many map | `test_mapping_report.py::test_many_to_many_mapping_and_counts` |
| ST-RPT-001 | Test discovery does not imply traceability | `test_mapping_report.py::test_no_explicit_links_means_all_requirements_unlinked` |
| ST-RPT-002 | Mixed known and unknown IDs | `test_mapping_report.py::test_unknown_pairs_do_not_create_requirements_or_resolved_links`; `test_cli.py::test_unknown_reference_is_reported_once_and_fails` |
| ST-RPT-002 | Deduplicate unknown references | `test_cli.py::test_unknown_reference_is_reported_once_and_fails` |
| ST-RPT-003 | Report a known inventory | `test_mapping_report.py::test_many_to_many_mapping_and_counts` |
| ST-RPT-003 | Make the static limitation visible | `test_mapping_report.py::test_empty_gap_sections_and_static_limitation` |
| ST-RPT-003 | Empty test input exposes all gaps | `test_cli.py::test_empty_test_directory_exposes_all_gaps` |
| ST-RPT-004 | Deterministic ordering | `test_mapping_report.py::test_order_independence_and_portable_output` |
| ST-RPT-004 | Escape a hostile title or filename | `test_mapping_report.py::test_source_text_cannot_create_columns_html_or_markdown_links` |
| ST-RPT-004 | Keep file and directory inputs portable | `test_cli.py::test_explicit_roots_do_not_execute_scanned_code_or_conftest` |
| ST-RPT-005 | Use explicit input roots | `test_cli.py::test_documented_example_command_and_report`; `test_cli.py::test_runtime_makes_no_network_connections` |
| ST-RPT-005 | Request help without a project | `test_cli.py::test_help_and_version_need_no_inputs` |
| ST-RPT-006 | Unlinked requirements are informational by default | `test_cli.py::test_default_and_strict_gap_exit_codes` |
| ST-RPT-006 | Fully linked valid input succeeds | `test_cli.py::test_fully_linked_succeeds` |
| ST-RPT-006 | Invalid input prevents misleading success | `test_cli.py::test_usage_and_missing_inputs_fail_without_report`; `test_cli.py::test_invalid_source_has_precedence_and_preserves_previous_report` |
| ST-RPT-007 | Save a report that identifies gaps | `test_cli.py::test_gap_report_is_saved_with_status_one` |
| ST-RPT-007 | Preserve a previous report on failure | `test_cli.py::test_invalid_source_has_precedence_and_preserves_previous_report`; `test_cli.py::test_failed_write_or_replace_preserves_old_report` |
| ST-RPT-007 | Reject overwriting a selected source | `test_cli.py::test_reject_input_collision_directory_and_missing_parent` |

## Design and limits

Code review confirmed the seven planned module boundaries with immutable source
records, `tokenize` plus Python 3.12 AST parsing, explicit literal marker matching,
no inspected-module imports/collection, and no runtime third-party dependencies.
Reports are rendered before output; file replacement is atomic; stdout errors
preserve the documented status rather than failing during interpreter shutdown.

The documented static discovery profile, ADDED-only/canonical Markdown subset,
unsupported aliases/dynamic collection, and definition-level parametrization are
intentional approved limits. Verification ran on Python 3.12/Linux; this report
does not claim an unexecuted cross-platform matrix. Canonical specs were not synced,
and the OpenSpec change was not archived.
