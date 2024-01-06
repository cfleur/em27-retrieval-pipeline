import datetime
import os
import shutil
import time
from typing import Generator
import pytest
import em27_metadata
import tum_esm_utils
import multiprocessing
from src import types
from tests.fixtures import (
    wrap_test_with_mainlock, download_sample_data, provide_config_template,
    remove_temporary_retrieval_data
)
from src import retrieval

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)

SENSOR_DATA_CONTEXTS = [
    em27_metadata.types.SensorDataContext(
        sensor_id="so",
        serial_number=39,
        from_datetime=datetime.datetime.combine(date, datetime.time.min),
        to_datetime=datetime.datetime.combine(date, datetime.time.max),
        utc_offset=0,
        pressure_data_source="so",
        calibration_factors=em27_metadata.types.CalibrationFactors(),
        multiple_ctx_on_this_date=False,
        location=em27_metadata.types.LocationMetadata(
            location_id="SOD",
            details="Sodankyla",
            lon=26.630,
            lat=67.366,
            alt=181.0,
        ),
    ) for date in [
        datetime.date(2017, 6, 8),
        datetime.date(2017, 6, 9),
    ]
] + [
    em27_metadata.types.SensorDataContext(
        sensor_id="mc",
        serial_number=115,
        from_datetime=datetime.datetime.combine(date, datetime.time.min),
        to_datetime=datetime.datetime.combine(date, datetime.time.max),
        utc_offset=0,
        pressure_data_source="mc",
        calibration_factors=em27_metadata.types.CalibrationFactors(),
        multiple_ctx_on_this_date=False,
        location=em27_metadata.types.LocationMetadata(
            location_id="ZEN",
            details="Zentralfriedhof",
            lon=16.438481,
            lat=48.147699,
            alt=180.0,
        ),
    ) for date in [
        datetime.date(2022, 6, 2),
    ]
]


@pytest.fixture(scope="session")
def provide_container_factory(
    provide_config_template: types.Config,
) -> Generator[retrieval.dispatching.container_factory.ContainerFactory, None,
               None]:
    logger = retrieval.utils.logger.Logger(
        "pytest",
        write_to_file=False,
        print_to_console=True,
    )
    yield retrieval.dispatching.container_factory.ContainerFactory(
        provide_config_template, logger, test_mode=True
    )


# this test will only mock the retrieval algorithm
@pytest.mark.order(4)
@pytest.mark.ci
def test_container_lifecycle_ci(
    wrap_test_with_mainlock: None,
    download_sample_data: None,
    remove_temporary_retrieval_data: None,
    provide_config_template: types.Config,
    provide_container_factory: retrieval.dispatching.container_factory.
    ContainerFactory,
) -> None:
    _run(
        provide_config_template,
        provide_container_factory,
        only_run_mock_retrieval=True,
    )


# this test will run the actual retrieval algorithm
@pytest.mark.order(5)
@pytest.mark.complete
def test_container_lifecycle_complete(
    wrap_test_with_mainlock: None,
    download_sample_data: None,
    remove_temporary_retrieval_data: None,
    provide_config_template: types.Config,
    provide_container_factory: retrieval.dispatching.container_factory.
    ContainerFactory,
) -> None:
    _run(
        provide_config_template,
        provide_container_factory,
        only_run_mock_retrieval=False,
    )


def _run(
    config: types.Config,
    container_factory: retrieval.dispatching.container_factory.ContainerFactory,
    only_run_mock_retrieval: bool,
) -> None:

    _point_config_to_test_data(config)
    retrieval.utils.retrieval_status.RetrievalStatusList.reset()

    NUMBER_OF_JOBS = len(SENSOR_DATA_CONTEXTS) * 2 * 3
    print(f"Running {NUMBER_OF_JOBS} retrieval jobs in parallel")

    def run_session(
        session: types.RetrievalSession,
        config: types.Config,
    ) -> None:
        retrieval.session.process_session.run(
            config,
            session,
            test_mode=only_run_mock_retrieval,
        )
        _assert_output_correctness(
            session.retrieval_algorithm,
            session.atmospheric_profile_model,
            session.ctx,
        )

    atm: types.AtmosphericProfileModel
    alg: types.RetrievalAlgorithm
    processes: list[multiprocessing.Process] = []
    for sdc in SENSOR_DATA_CONTEXTS:
        for atm in [  # type: ignore
            "GGG2014", "GGG2020"
        ]:
            for alg in [ # type: ignore
                "proffast-1.0", "proffast-2.2", "proffast-2.3"
            ]:
                assert config.retrieval is not None
                if alg == "proffast-1.0" and atm == "GGG2020":
                    continue

                # set up container factory
                retrieval.utils.retrieval_status.RetrievalStatusList.add_items(
                    [sdc],
                    alg,
                    atm,
                )
                # create session and run container
                session = retrieval.session.create_session.run(
                    container_factory,
                    sdc,
                    retrieval_algorithm=alg,
                    atmospheric_profile_model=atm
                )
                name = (
                    f"{session.ctn.container_id}:{alg}-{atm}-" +
                    f"{sdc.sensor_id}-{sdc.from_datetime.date()}"
                )
                p = multiprocessing.Process(
                    target=run_session,
                    args=(session, config),
                    name=name,
                    daemon=True,
                )
                p.start()
                print(f"Starting process {p.name}")
                processes.append(p)

    # wait until all processes have been started
    time.sleep(0.3)

    # wait for all processes to finish
    while True:
        finished_processes: list[multiprocessing.Process] = []
        for p in processes:
            if not p.is_alive():
                assert p.exitcode == 0, f"Process {p.name} failed"
                p.join()
                finished_processes.append(p)
                print(f"Finished process {p.name}")
                container_factory.remove_container(p.name.split(":")[0])
                print(f"Removed container of process {p.name}")

        for p in finished_processes:
            processes.remove(p)

        if len(processes) == 0:
            break

        time.sleep(15)


def _point_config_to_test_data(config: types.Config, ) -> None:
    config.general.data.datalogger.root = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "log"
    )
    config.general.data.interferograms.root = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "ifg"
    )
    config.general.data.atmospheric_profiles.root = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "map"
    )
    config.general.data.results.root = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "outputs"
    )


def _assert_output_correctness(
    retrieval_algorithm: types.RetrievalAlgorithm,
    atmospheric_profile_model: types.AtmosphericProfileModel,
    sensor_data_context: em27_metadata.types.SensorDataContext,
) -> None:
    date_string = sensor_data_context.from_datetime.strftime("%Y%m%d")
    out_path = os.path.join(
        PROJECT_DIR, "data/testing/container/outputs", retrieval_algorithm,
        atmospheric_profile_model, sensor_data_context.sensor_id, "successful",
        date_string
    )
    expected_files = [
        "about.json",
        "logfiles/container.log",
    ]
    if retrieval_algorithm in ["proffast-2.2", "proffast-2.3"]:
        expected_files.extend([
            (
                f"comb_invparms_{sensor_data_context.sensor_id}_" +
                f"SN{str(sensor_data_context.serial_number).zfill(3)}" +
                f"_{date_string[2:]}-{date_string[2:]}.csv"
            ),
            "pylot_config.yml",
            "pylot_log_format.yml",
            "logfiles/preprocess_output.log",
            "logfiles/pcxs_output.log",
            "logfiles/inv_output.log",
        ])
    if retrieval_algorithm == "proffast-1.0":
        expected_files.extend([
            (
                f"{sensor_data_context.sensor_id}{date_string[2:]}-" +
                f"combined-invparms.csv"
            ),
            (
                f"{sensor_data_context.sensor_id}{date_string[2:]}-" +
                f"combined-invparms.parquet"
            ),
            "logfiles/wrapper.log",
            "logfiles/preprocess4.log",
            "logfiles/pcxs10.log",
            "logfiles/invers10.log",
        ])

    for filename in expected_files:
        filepath = os.path.join(out_path, filename)
        assert os.path.isfile(
            filepath
        ), f"output file does not exist ({filepath})"
