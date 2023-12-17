from typing import Literal
import datetime
import os
import em27_metadata
import polars as pl
import tum_esm_utils
import rich.console
import rich.progress
from src import types, utils

console = rich.console.Console()

console.print("loading config")
config = types.Config.load()

console.print("loading metadata")
metadata = em27_metadata.load_from_github(
    github_repository=config.general.metadata.github_repository,
    access_token=config.general.metadata.access_token,
)


def _date_range(
    from_date: datetime.date,
    to_date: datetime.date,
) -> list[datetime.date]:
    delta = to_date - from_date
    assert delta.days >= 0, "from_date must be before to_date"
    return [
        from_date + datetime.timedelta(days=i) for i in range(delta.days + 1)
    ]


def _ggg2014_profiles_exists(
    path: str,
    lat: float,
    lon: float,
    date: datetime.date,
) -> bool:
    date_string = date.strftime("%Y%m%d")
    coords_string = utils.text.get_coordinates_slug(lat, lon)
    return "✅" if os.path.isfile(
        os.path.join(path, "GGG2014", f"{date_string}_{coords_string}.map")
    ) else "-"


def _ggg2020_profiles_exists(
    path: str,
    lat: float,
    lon: float,
    date: datetime.date,
) -> str:
    date_string = date.strftime("%Y%m%d")
    coords_string = utils.text.get_coordinates_slug(lat, lon)
    return "✅" if all([
        os.path.isfile(
            os.path.
            join(path, "GGG2020", f"{date_string}{h:02d}_{coords_string}.map")
        ) for h in range(0, 22, 3)
    ]) else "-"


def _count_ifg_datapoints(
    path: str,
    sensor_id: str,
    date: datetime.date,
) -> int:

    try:
        return len(
            os.listdir(os.path.join(path, sensor_id, date.strftime('%Y%m%d')))
        )
    except FileNotFoundError:
        return 0


def _count_datalogger_datapoints(
    path: str,
    sensor_id: str,
    date: datetime.date,
) -> int:
    try:
        with open(
            os.path.join(
                path, sensor_id,
                f"datalogger-{sensor_id}-{date.strftime('%Y%m%d')}.csv"
            ), "r"
        ) as f:
            return len(f.readlines()) - 1
    except FileNotFoundError:
        return 0


def _check_retrieval_output(
    sdc: em27_metadata.types.SensorDataContext,
    retrieval_algorithm: Literal["proffast-1.0", "proffast-2.2",
                                 "proffast-2.3"],
    atmospheric_model: Literal["GGG2014", "GGG2020"],
) -> Literal["✅", "❌", "-"]:
    output_folder_slug = sdc.from_datetime.strftime("%Y%m%d")
    if sdc.multiple_ctx_on_this_date:
        output_folder_slug += sdc.from_datetime.strftime("_%H%M%S")
        output_folder_slug += sdc.to_datetime.strftime("_%H%M%S")

    success_path = os.path.join(
        config.general.data.results.root,
        retrieval_algorithm,
        atmospheric_model,
        sensor.sensor_id,
        "successful",
        output_folder_slug,
    )
    failed_path = os.path.join(
        config.general.data.results.root,
        retrieval_algorithm,
        atmospheric_model,
        sensor.sensor_id,
        "failed",
        output_folder_slug,
    )
    if os.path.isdir(success_path):
        return "✅"
    elif os.path.isdir(failed_path):
        return "❌"
    else:
        return "-"


try:
    for sensor in metadata.sensors:
        from_datetimes: list[datetime.datetime] = []
        to_datetimes: list[datetime.datetime] = []
        location_ids: list[str] = []
        interferograms: list[int] = []
        datalogger: list[int] = []
        ggg2014_profiles: list[str] = []
        ggg2020_profiles: list[str] = []
        ggg2014_proffast_10_outputs: list[str] = []
        ggg2014_proffast_22_outputs: list[str] = []
        ggg2014_proffast_23_outputs: list[str] = []
        ggg2020_proffast_22_outputs: list[str] = []
        ggg2020_proffast_23_outputs: list[str] = []
        console.print(
            f"determining sensor data contexts for sensor {sensor.sensor_id}"
        )
        sdcs = metadata.get(
            sensor_id=sensor.sensor_id,
            from_datetime=sensor.locations[0].from_datetime,
            to_datetime=sensor.locations[-1].to_datetime
        )
        with rich.progress.Progress() as progress:
            task = progress.add_task(
                "parsing all sensor data contexts", total=len(sdcs)
            )
            for sdc in sdcs:
                date_range = _date_range(
                    sdc.from_datetime.date(), sdc.to_datetime.date()
                )
                subtask = progress.add_task(
                    f"{sdc.from_datetime.date()} - {sdc.to_datetime.date()} ({sdc.location.location_id})",
                    total=len(date_range)
                )
                for date in date_range:
                    from_datetimes.append(
                        max(
                            datetime.datetime.combine(
                                date, datetime.time.min, tzinfo=datetime.UTC
                            ), sdc.from_datetime
                        )
                    )
                    to_datetimes.append(
                        min(
                            datetime.datetime.combine(
                                date, datetime.time.max, tzinfo=datetime.UTC
                            ), sdc.to_datetime
                        )
                    )
                    location_ids.append(sdc.location.location_id)
                    interferograms.append(
                        _count_ifg_datapoints(
                            config.general.data.interferograms.root,
                            sensor.sensor_id,
                            date,
                        )
                    )
                    datalogger.append(
                        _count_datalogger_datapoints(
                            config.general.data.datalogger.root,
                            sensor.sensor_id,
                            date,
                        )
                    )
                    ggg2014_profiles.append(
                        _ggg2014_profiles_exists(
                            config.general.data.atmospheric_profiles.root,
                            sdc.location.lat,
                            sdc.location.lon,
                            date,
                        )
                    )
                    ggg2020_profiles.append(
                        _ggg2020_profiles_exists(
                            config.general.data.atmospheric_profiles.root,
                            sdc.location.lat,
                            sdc.location.lon,
                            date,
                        )
                    )
                    ggg2014_proffast_10_outputs.append(
                        _check_retrieval_output(sdc, "proffast-1.0", "GGG2014")
                    )
                    ggg2014_proffast_22_outputs.append(
                        _check_retrieval_output(sdc, "proffast-2.2", "GGG2014")
                    )
                    ggg2014_proffast_23_outputs.append(
                        _check_retrieval_output(sdc, "proffast-2.3", "GGG2014")
                    )
                    ggg2020_proffast_22_outputs.append(
                        _check_retrieval_output(sdc, "proffast-2.2", "GGG2020")
                    )
                    ggg2020_proffast_23_outputs.append(
                        _check_retrieval_output(sdc, "proffast-2.3", "GGG2020")
                    )
                    progress.advance(subtask)
                progress.remove_task(subtask)
                progress.advance(task)

        df = pl.DataFrame({
            "from_datetime": from_datetimes,
            "to_datetime": to_datetimes,
            "location_id": location_ids,
            "interferograms": interferograms,
            "datalogger": datalogger,
            "ggg2014_profiles": ggg2014_profiles,
            "ggg2014_proffast_10_outputs": ggg2014_proffast_10_outputs,
            "ggg2014_proffast_22_outputs": ggg2014_proffast_22_outputs,
            "ggg2014_proffast_23_outputs": ggg2014_proffast_23_outputs,
            "ggg2020_profiles": ggg2020_profiles,
            "ggg2020_proffast_22_outputs": ggg2020_proffast_22_outputs,
            "ggg2020_proffast_23_outputs": ggg2020_proffast_23_outputs,
        }).with_columns([
            pl.col("location_id").str.pad_start(8),
            pl.col("interferograms").cast(str).str.pad_start(5),
            pl.col("datalogger").cast(str).str.pad_start(5),
        ])
        df.write_csv(
            tum_esm_utils.files.
            rel_to_abs_path(f"./data/reports/{sensor.sensor_id}.csv"),
            datetime_format="%Y-%m-%dT%H:%M:%S%z",
        )
except KeyboardInterrupt:
    console.print("aborted by user")
