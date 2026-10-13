import pytest


@pytest.fixture
def write_file(tmp_path):
    def write(relative, text=""):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    return write
