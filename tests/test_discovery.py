import os

import pytest

from spectrace.discovery import discover
from spectrace.models import InputError


@pytest.mark.requirements("ST-CAT-001", "ST-TST-001")
@pytest.mark.parametrize(
    "kind,name,ignored", [("spec", "spec.md", "notes.md"), ("test", "test_x.py", "conftest.py")]
)
def test_bounded_sorted_discovery(tmp_path, write_file, kind, name, ignored):
    write_file(f"root/z/{name}")
    write_file(f"root/a/{name}")
    write_file(f"root/{ignored}")
    write_file(f"root/.hidden/{name}")
    outside = write_file(f"sibling/{name}")
    (tmp_path / "root/linked").symlink_to(outside.parent, target_is_directory=True)
    (tmp_path / "root" / name).symlink_to(outside)
    files = discover(tmp_path / "root", kind)
    assert [file.relative_path for file in files] == [f"a/{name}", f"z/{name}"]


@pytest.mark.requirements("ST-CAT-001", "ST-TST-001")
@pytest.mark.parametrize(
    "kind,name", [("spec", "requirements.md"), ("test", "test_x.py"), ("test", "x_test.py")]
)
def test_single_file_uses_basename(write_file, kind, name):
    path = write_file(f"nested/{name}")
    assert [file.relative_path for file in discover(path, kind)] == [name]


@pytest.mark.requirements("ST-CAT-001", "ST-CAT-005", "ST-TST-005")
@pytest.mark.parametrize("kind,name", [("spec", "spec.md"), ("test", "test_x.py")])
def test_reject_symlink_root(tmp_path, write_file, kind, name):
    target = write_file(f"actual/{name}")
    link = tmp_path / name
    link.symlink_to(target)
    with pytest.raises(InputError, match="symbolic-link"):
        discover(link, kind)


@pytest.mark.requirements("ST-CAT-005", "ST-TST-005")
@pytest.mark.parametrize("kind", ["spec", "test"])
def test_missing_wrong_extension_and_nonregular_input(tmp_path, write_file, kind):
    with pytest.raises(InputError, match="missing"):
        discover(tmp_path / "missing", kind)
    with pytest.raises(InputError, match="unsupported"):
        discover(write_file("wrong.txt"), kind)
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    with pytest.raises(InputError, match="regular file or directory"):
        discover(fifo, kind)


@pytest.mark.requirements("ST-CAT-005", "ST-TST-005")
def test_unreadable_directory_is_not_silently_empty(tmp_path, monkeypatch):
    def denied(path):
        raise PermissionError(13, "Permission denied", str(path))

    monkeypatch.setattr(os, "scandir", denied)
    with pytest.raises(InputError, match="Permission denied"):
        discover(tmp_path, "spec")
