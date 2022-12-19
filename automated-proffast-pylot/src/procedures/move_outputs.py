from datetime import datetime
import json
import os
import shutil
import subprocess
from typing import Optional
from src import utils, types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def detect_error_type(output_src: str) -> Optional[str]:
    if not os.path.isdir(f"{output_src}/logfiles"):
        return None

    known_errors: list[tuple[str, str]] = [
        ("preprocess_output", "charfilter not found!"),
        ("preprocess_output", "Zero IFG block size!"),
        ("inv_output", "CO channel: no natural grid!"),
        ("inv_output", "Cannot access tabellated x-sections!"),
    ]

    for o, m in known_errors:
        try:
            with open(f"{output_src}/logfiles/{o}.log", "r") as f:
                file_content = "".join(f.readlines())
            if m in file_content:
                return m
        except FileNotFoundError:
            pass

    return None


def run(config: types.ConfigDict, logger: utils.Logger, session: types.SessionDict) -> None:
    sensor, date, container_id = session["sensor"], session["date"], session["container_id"]

    output_src = (
        f"{PROJECT_DIR}/outputs/{sensor}_"
        + f"SN{str(session['serial_number']).zfill(3)}_{date[2:]}-{date[2:]}"
    )
    output_csv = (
        f"{output_src}/comb_invparms_{sensor}_"
        + f"SN{str(session['serial_number']).zfill(3)}_"
        + f"{date[2:]}-{date[2:]}.csv"
    )
    assert os.path.isdir(output_src), "pylot output directory missing"

    # --- MOVE OUTPUT DATA ---

    # determine output directory path on DSS
    day_was_successful = os.path.isfile(output_csv)
    if day_was_successful:
        with open(output_csv, "r") as f:
            if len(f.readlines()) > 1:
                logger.debug(f"Retrieval output csv exists")
            else:
                day_was_successful = False
                logger.warning(f"Retrieval output csv is empty")
    else:
        logger.debug(f"Retrieval output csv is missing")

    output_dirname = "proffast-2.2-outputs"
    output_dst = config["dst"] + f"/{sensor}/{output_dirname}"
    if not os.path.isdir(output_dst):
        os.mkdir(f"{output_dst}")
        os.mkdir(f"{output_dst}/successful")
        os.mkdir(f"{output_dst}/failed")

    output_dst_successful = f"{output_dst}/successful/{date}"
    output_dst_failed = f"{output_dst}/failed/{date}"

    if day_was_successful:
        output_dst = output_dst_successful
    if not day_was_successful:
        output_dst = output_dst_failed
        error_type = detect_error_type(output_src)
        if error_type is None:
            logger.debug("Unknown error type")
        else:
            logger.debug(f"Known error type: {error_type}")

    # remove old outputs
    if os.path.isdir(output_dst_successful):
        logger.debug(f"Removing old successful output")
        shutil.rmtree(output_dst_successful)
    if os.path.isdir(output_dst_failed):
        logger.debug(f"Removing old failed output")
        shutil.rmtree(output_dst_failed)

    # move new outputs
    shutil.copytree(output_src, output_dst)
    shutil.rmtree(output_src)

    # --- MOVE INTERFEROGRAMS ---

    existing_src_directories = utils.get_existing_src_directories(config, sensor, date)
    utils.assert_directory_equality(existing_src_directories)

    ifg_src = existing_src_directories[0]
    ifg_dst = f"{config['dst']}/{sensor}/ifgs/{date}"
    if not os.path.isdir(ifg_dst):
        logger.debug(f"Copying ifgs from {ifg_src} to dst")
        shutil.copytree(ifg_src, ifg_dst)

    ifg_src_upload = os.path.join(
        config["src"]["interferograms"]["upload"], sensor, date
    )
    if os.path.isdir(ifg_src_upload):
        # somewhat redundant - but better check twice
        try:
            utils.assert_directory_equality([ifg_src_upload, ifg_dst])
        except AssertionError:
            raise AssertionError("directories differ, skipped removal")
        logger.debug("Removing ifgs from cloud")
        shutil.rmtree(ifg_src_upload)

    # --- POSSIBLY REMOVE ITEMS FROM MANUAL QUEUE ---

    utils.RetrievalQueue.remove_from_queue_file(sensor, date, config, logger)

    # --- STORE AUTOMATION LOGS ---

    date_logs = logger.get_session_logs()
    with open(f"{output_dst}/automation_{container_id}.log", "w") as f:
        f.writelines(date_logs)

    # --- STORE AUTOMATION INFO ---

    with open(f"{output_dst}/about.json", "w") as f:
        now = datetime.utcnow()
        try:
            commit_sha = (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "--verify", "HEAD"], cwd=PROJECT_DIR
                )
                .decode()
                .replace("\n", "")
            )
        except:
            commit_sha = None
        about_dict = {
            "proffastVersion": "2.2",
            "locationRepository": config["location_repository"],
            "automationVersion": commit_sha,
            "generationDate": now.strftime("%Y%m%d"),
            "generationTime": now.strftime("%T"),
        }
        json.dump(about_dict, f, indent=4)
    
    # Clear directories "inputs" and "outputs"
    for subdir in ["inputs", "outputs"]:
        shutil.rmtree(f"{PROJECT_DIR}/{subdir}")
        os.mkdir(f"{PROJECT_DIR}/{subdir}")
        os.system(f"touch {PROJECT_DIR}/{subdir}/.gitkeep")