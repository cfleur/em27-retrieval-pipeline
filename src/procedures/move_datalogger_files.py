import os
import shutil
from src import utils, types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(config: types.ConfigDict, session: types.SessionDict) -> None:
    sensor, date = session["sensor"], session["date"]

    src_dir = os.path.join(config["src"]["datalogger"], sensor)
    dst_dir = os.path.join(PROJECT_DIR, "inputs", f"{sensor}_pressure")
    assert os.path.isdir(src_dir), "src path does not exist"

    matching_files = list(
        filter(
            lambda f: f.startswith(f"{date[:4]}-{date[4:6]}-{date[6:]}_")
            and f.endswith(".dat"),
            os.listdir(src_dir),
        )
    )

    assert len(matching_files) > 0, "no datalogger files found"
    assert len(matching_files) < 2, f"multiple datalogger files found: {matching_files}"

    src_file = f"{src_dir}/{matching_files[0]}"
    dst_file = f"{dst_dir}/{matching_files[0][:10]}.dat"
    with open(src_file, "r") as f:
        line_count = len(f.readlines())

    # 1440 minutes per day + 1 header line
    if line_count < 1441:
        utils.Logger.warning(
            f"{sensor}/{date} - datalogger file only has {line_count}/1441 lines"
        )
    assert line_count >= 30, "datalogger file has less than 30 entries"

    # copy datalogger file
    shutil.copy(src_file, dst_file)
