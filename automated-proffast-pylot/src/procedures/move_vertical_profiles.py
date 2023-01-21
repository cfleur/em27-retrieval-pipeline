import os
import shutil
from src import custom_types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(config: custom_types.ConfigDict, session: custom_types.SessionDict) -> None:
    sensor, date = session["sensor"], session["date"]
    container_id = session["container_id"]

    src_filepath = os.path.join(
        config["src"]["vertical_profiles"], sensor, f"{sensor}{date}.map"
    )
    dst_filepath = os.path.join(
        PROJECT_DIR, "inputs", container_id, f"{sensor}_map", f"{sensor}{date}.map"
    )

    assert os.path.isfile(src_filepath), "map file does not exist"
    shutil.copy(src_filepath, dst_filepath)
