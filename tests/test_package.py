import subprocess
import sys
from importlib.metadata import metadata, version
from pathlib import Path

import pytest


@pytest.mark.requirements("ST-RPT-005")
@pytest.mark.parametrize("argument", ["--help", "--version"])
def test_installed_entry_point_without_project(tmp_path, argument):
    result = subprocess.run(
        [str(Path(sys.executable).with_name("spectrace")), argument],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "spectrace" in result.stdout
    assert result.stderr == ""
    if argument == "--version":
        assert result.stdout == f"spectrace {version('spectrace')}\n"


@pytest.mark.requirements("ST-RPT-005")
def test_package_has_no_runtime_dependencies():
    package = metadata("spectrace")
    assert package["Requires-Python"] == ">=3.12"
    assert all('extra == "dev"' in item for item in package.get_all("Requires-Dist", []))
