import os
import shutil
from typing import Generator
import filelock
import pytest
import tum_esm_utils
from src import custom_types, utils


# TODO: syncronize mainlock names across codebase
PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
lock = filelock.FileLock(os.path.join(PROJECT_DIR, "src", "main.lock"), timeout=0)


@pytest.fixture
def wrap_test_with_mainlock() -> Generator[None, None, None]:
    try:
        lock.acquire()
        yield
        lock.release()
    except filelock.Timeout:
        raise Exception("automation is already running")


@pytest.fixture(scope="session")
def download_sample_data() -> Generator[None, None, None]:
    """Download sample data from https://syncandshare.lrz.de and
    extract it to the testing data directory. This is done only
    once per test run. The tar file will not be deleted afterwards
    and the download is skipped if the tar file already exists.

    The tar file has about 96MB."""

    testing_data_path = os.path.join(PROJECT_DIR, "data", "testing", "container")
    tarball_filename = "automated-proffast-pylot-example-inputs.tar.gz"

    # download testing data tarball if it does not exist
    if not os.path.isfile(os.path.join(testing_data_path, tarball_filename)):
        tum_esm_utils.shell.run_shell_command(
            f"wget --quiet https://syncandshare.lrz.de/dl/"
            + f"fiA9bjdafNcuVGrmMfDL49/{tarball_filename}",
            working_directory=testing_data_path,
        )

    # remove existing input data
    for input_dir in [
        os.path.join(testing_data_path, "inputs", t) for t in ["log", "map", "ifg"]
    ]:
        if os.path.isdir(input_dir):
            shutil.rmtree(input_dir)

    # extract tarball
    tum_esm_utils.shell.run_shell_command(
        f"tar -xf {tarball_filename}",
        working_directory=testing_data_path,
    )

    yield


@pytest.fixture(scope="function")
def clear_output_data() -> Generator[None, None, None]:
    """Remove all directories in the testing output directory"""

    testing_data_output_dir = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "outputs"
    )
    for d in os.listdir(testing_data_output_dir):
        subdir = os.path.join(testing_data_output_dir, d)
        if os.path.isdir(subdir):
            shutil.rmtree(subdir)


@pytest.fixture(scope="function")
def provide_tmp_config() -> Generator[custom_types.Config, None, None]:
    """Create a temporary config file that points to the testing data.
    This is done before each test; the original config file is restored
    afterwards."""

    config_path = os.path.join(PROJECT_DIR, "config", "config.json")
    config_template_path = os.path.join(PROJECT_DIR, "config", "config.template.json")

    # backup original config to restore it later
    tmp_config_path = os.path.join(PROJECT_DIR, "config", "config.tmp.json")
    assert not os.path.isfile(tmp_config_path), f'"{tmp_config_path}" should not exist'
    if os.path.isfile(config_path):
        os.rename(config_path, tmp_config_path)

    # create temporary config where all directories point to the testing data
    config_template = tum_esm_utils.files.load_json_file(config_template_path)
    for attribute_name, dir_name in [
        ("datalogger", "log"),
        ("vertical_profiles", "map"),
        ("interferograms", "ifg"),
    ]:
        config_template["general"]["data_src_dirs"][attribute_name] = os.path.join(
            PROJECT_DIR, "data", "testing", "container", "inputs", dir_name
        )

    # enable processing of storage data of sensors "mc" and "so"
    config_template["general"]["data_dst_dirs"]["results"] = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "outputs"
    )
    config_template["automated_proffast"]["data_sources"]["storage"] = True
    config_template["automated_proffast"]["data_sources"]["manual-queue"] = True
    config_template["automated_proffast"]["storage_data_filter"][
        "sensor_ids_to_consider"
    ] = ["mc", "so"]

    # define target directory for merged results
    config_template["output_merging_targets"][0]["dst_dir"] = os.path.join(
        PROJECT_DIR, "data", "testing", "pipeline", "results_merged"
    )
    tum_esm_utils.files.dump_json_file(config_path, config_template)

    # run test
    yield custom_types.Config(**config_template)

    # possibly restore original config
    os.remove(config_path)
    if os.path.isfile(tmp_config_path):
        os.rename(tmp_config_path, config_path)


@pytest.fixture(scope="function")
def provide_tmp_manual_queue() -> Generator[custom_types.ManualQueue, None, None]:
    """Create a temporary manual queue file that contains items for
    testing."""

    manual_queue_path = os.path.join(PROJECT_DIR, "config", "manual-queue.json")

    # backup original config to restore it later
    tmp_manual_queue_path = os.path.join(PROJECT_DIR, "config", "manual-queue.tmp.json")
    assert not os.path.isfile(
        tmp_manual_queue_path
    ), f'"{tmp_manual_queue_path}" should not exist'
    if os.path.isfile(manual_queue_path):
        os.rename(manual_queue_path, tmp_manual_queue_path)

    manual_queue = custom_types.ManualQueue(
        items=[
            custom_types.ManualQueueItem(
                sensor_id="so",
                date="20170101",
                priority=1,
            ),
            custom_types.ManualQueueItem(
                sensor_id="so",
                date="20170103",
                priority=1,
            ),
            custom_types.ManualQueueItem(
                sensor_id="so",
                date="20170102",
                priority=-1,
            ),
        ]
    )

    tum_esm_utils.files.dump_json_file(manual_queue_path, manual_queue.dict()["items"])

    # run test
    yield manual_queue

    # possibly restore original config
    os.remove(manual_queue_path)
    if os.path.isfile(tmp_manual_queue_path):
        os.rename(tmp_manual_queue_path, manual_queue_path)
