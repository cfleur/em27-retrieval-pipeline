from typing import Optional
import pytest
import shutil
import os
from tests.fixtures import wrap_test_with_mainlock, PROJECT_DIR
from src import custom_types, utils, interfaces, procedures

PYLOT_ROOT_DIR = os.path.join(PROJECT_DIR, "src", "prfpylot")
SENSOR_DATA_CONTEXT = custom_types.SensorDataContext(
    sensor_id="mc",
    serial_number=115,
    utc_offset=0.0,
    date="20220602",
    location=custom_types.Location(
        location_id="ZEN",
        details="Zentralfriedhof",
        lon=16.438481,
        lat=48.147699,
        alt=180.0,
    ),
)


@pytest.mark.integration
def test_pylot(wrap_test_with_mainlock):

    config = custom_types.Config(
        **{
            "process_data_automatically": True,
            "data_filter": {
                "sensor_ids_to_consider": ["mc", "so"],
                "start_date": "20220101",
                "end_date": "20991231",
                "min_days_delay": 5,
            },
            "location_data": {
                "github_repository": "tum-esm/em27-location-data",
                "access_token": "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",
            },
            "data_src_dirs": {
                "datalogger": f"{PROJECT_DIR}/example/inputs/log",
                "vertical_profiles": f"{PROJECT_DIR}/example/inputs/map",
                "interferograms": f"{PROJECT_DIR}/example/inputs/ifg",
            },
            "data_dst_dirs": {"results": f"{PROJECT_DIR}/example/outputs"},
        }
    )

    # remove old containers
    for f in os.listdir(os.path.join(PYLOT_ROOT_DIR, "containers")):
        p = os.path.join(PYLOT_ROOT_DIR, "containers", f)
        if os.path.isdir(p) and (f != "main"):
            shutil.rmtree(p)

    # set up container
    logger = utils.Logger("pytest", print_only=True)
    pylot_factory = interfaces.PylotFactory(logger)
    session = procedures.create_session.run(pylot_factory, SENSOR_DATA_CONTEXT)

    # run container
    procedures.process_session.run(config, session)

    # assert output correctness
    # TODO