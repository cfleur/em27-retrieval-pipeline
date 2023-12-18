import os
import shutil
from typing import Generator
import pytest
import tum_esm_utils
from src import types, utils

_PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("..")


@pytest.fixture
def wrap_test_with_mainlock() -> Generator[None, None, None]:
    with utils.semaphores.with_automation_lock():
        yield


@pytest.fixture(scope="session")
def download_sample_data() -> Generator[None, None, None]:
    """Download sample data from https://syncandshare.lrz.de and
    extract it to the testing data directory. This is done only
    once per test run. The tar file will not be deleted afterwards
    and the download is skipped if the tar file already exists.

    The tar file has about 96MB."""

    testing_data_path = os.path.join(
        _PROJECT_DIR, "data", "testing", "container"
    )
    tarball_filename = "em27-retrieval-pipeline-test-inputs-1.0.0.tar.gz"

    # download testing data tarball if it does not exist
    if not os.path.isfile(os.path.join(testing_data_path, tarball_filename)):
        tum_esm_utils.shell.run_shell_command(
            f"wget --quiet https://syncandshare.lrz.de/dl/" +
            f"fiUY18aZDWf3CYNisatQB9/{tarball_filename}",
            working_directory=testing_data_path,
        )

    # remove existing input data
    for input_dir in [
        os.path.join(testing_data_path, "inputs", t)
        for t in ["log", "map", "ifg"]
    ]:
        if os.path.isdir(input_dir):
            shutil.rmtree(input_dir)

    # extract tarball
    tum_esm_utils.shell.run_shell_command(
        f"tar -xzf {tarball_filename}",
        working_directory=testing_data_path,
    )

    yield


@pytest.fixture(scope="function")
def clear_output_data() -> Generator[None, None, None]:
    """Remove all directories in the testing output directory"""

    for d in [
        os.path.join(_PROJECT_DIR, "data", "testing", "container", "outputs"),
        os.path.join(_PROJECT_DIR, "data", "containers")
    ]:
        for sd in os.listdir(d):
            subdir = os.path.join(d, sd)
            if os.path.isdir(subdir):
                shutil.rmtree(subdir)

    yield


"""
@pytest.fixture(scope="session")
def provide_export_config() -> Generator[custom_types.Config, None, None]:
    # Provide a temporary config file that points to the export testing data.

    # LOAD CONFIG TEMPLATE

    config_template = tum_esm_utils.files.load_json_file(
        os.path.join(PROJECT_DIR, "config", "config.template.json")
    )

    # UPDATE INPUTS

    config_template["general"]["data_dst_dirs"]["results"] = os.path.join(
        PROJECT_DIR, "data", "testing", "merging", "raw"
    )

    # UPDATE OUTPUTS

    config_template["output_merging_targets"][0]["dst_dir"] = os.path.join(
        PROJECT_DIR, "data", "testing", "merging", "merged"
    )

    # PARSE CONFIG OBJECT

    config = custom_types.Config(**config_template)

    # RUN TEST

    yield config
"""


@pytest.fixture(scope="session")
def provide_config_template() -> Generator[types.Config, None, None]:
    """Provide a temporary config used in profiles download."""

    config = types.Config.load(
        os.path.join(_PROJECT_DIR, "config", "config.template.json"),
        ignore_path_existence=True,
    )
    config.general.data.datalogger.root = "/tmp"
    config.general.data.atmospheric_profiles.root = "/tmp"
    config.general.data.interferograms.root = "/tmp"
    config.general.data.results.root = "/tmp"
    config.export_targets = []

    yield config
