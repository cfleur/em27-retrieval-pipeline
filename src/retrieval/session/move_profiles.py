import os
import shutil
import src


def run(
    config: src.utils.config.Config,
    session: src.utils.types.RetrievalSession,
) -> None:
    # TODO: add switch to use either GGG2014 or GGG2020

    coordinates_slug = src.utils.functions.get_coordinates_slug(
        lat=session.ctx.location.lat, lon=session.ctx.location.lon
    )
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")

    try:
        shutil.copy(
            os.path.join(
                config.general.data_src_dirs.profiles,
                "GGG2014",
                f"{date_string}_{coordinates_slug}.map",
            ),
            os.path.join(
                session.ctn.data_input_path,
                "map",
                f"{session.ctx.sensor_id}{date_string}.map",
            ),
        )
    except FileNotFoundError as e:
        raise AssertionError(f"map file does not exist: {e}")