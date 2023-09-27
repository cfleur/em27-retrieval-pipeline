import os
import shutil
import pytest
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)


def _rmdir(path: str) -> None:
    path = os.path.join(PROJECT_DIR, path)
    if os.path.isdir(path):
        shutil.rmtree(path)


@pytest.mark.order(1)
@pytest.mark.ci_quick
@pytest.mark.ci_intensive
@pytest.mark.ci_complete
def test_static_types() -> None:
    _rmdir(".mypy_cache/3.11/src")
    _rmdir(".mypy_cache/3.11/tests")

    for path in [
        "src/cli/main.py",
        "src/run_proffast.py",
        "src/download_profiles.py",
        "src/export_outputs.py",
        "tests/",
        "src/retrieval/proffast-1.0/main/prfpylot/main.py",
    ]:
        assert os.system(
            f"cd {PROJECT_DIR} && .venv/bin/python -m mypy {path}"
        ) == 0
