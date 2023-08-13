import datetime
import os
import json
import sys
import polars as pl
import rich.progress
import tum_esm_em27_metadata
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
sys.path.append(PROJECT_DIR)

from src import procedures, utils


def run() -> None:
    config = utils.load_config()
    em27_metadata = tum_esm_em27_metadata.load_from_github(
        **config.general.location_data.model_dump()
    )
    console = rich.console.Console()

    for i, output_merging_target in enumerate(config.output_merging_targets):
        print(f"\nprocessing output merging target #{i+1}")
        print(json.dumps(output_merging_target.model_dump(), indent=4))
        assert (
            output_merging_target.campaign_id in em27_metadata.campaign_ids
        ), f"unknown campaign_id {output_merging_target.campaign_id}"

        campaign = next(
            campaign
            for campaign in em27_metadata.campaigns
            if campaign.campaign_id == output_merging_target.campaign_id
        )

        from_date = campaign.from_datetime.date()
        to_date = min(datetime.datetime.utcnow().date(), campaign.to_datetime.date())

        dates: list[datetime.date] = []
        current_date = from_date
        while current_date <= to_date:
            dates.append(current_date)
            current_date += datetime.timedelta(days=1)

        with rich.progress.Progress() as progress:
            task = progress.add_task("processing dataframes", total=len(dates))

            for date in dates:
                sensor_data_contexts: list[
                    tum_esm_em27_metadata.types.SensorDataContext
                ] = []

                # get all sensor data contexts for this campaign's sensors
                for sid in campaign.sensor_ids:
                    sensor_data_contexts += em27_metadata.get(
                        sid,
                        from_datetime=datetime.datetime.combine(
                            date, datetime.time.min
                        ),
                        to_datetime=datetime.datetime.combine(date, datetime.time.max),
                    )

                # only consider data at campaign locations
                sensor_data_contexts = list(
                    filter(
                        lambda ctx: ctx.location.location_id in campaign.location_ids,
                        sensor_data_contexts,
                    )
                )

                ctx_dataframes: list[pl.DataFrame] = []

                for sensor_data_context in sensor_data_contexts:
                    try:
                        df = procedures.export.get_sensor_dataframe(
                            config,
                            sensor_data_context,
                            output_merging_target,
                        )
                    except AssertionError:
                        continue

                    found_data_count += 1
                    ctx_dataframes.append(
                        procedures.export.post_process_dataframe(
                            df=df,
                            sampling_rate=output_merging_target.sampling_rate,
                            max_interpolation_gap_seconds=output_merging_target.max_interpolation_gap_seconds,
                        )
                    )

                if found_data_count > 0:
                    progress.console.print(
                        f"{date}: {found_data_count} sensor(s) with data"
                    )

                    # TODO: check whether this works for overlapping and non-overlapping columns
                    merged_df = procedures.export.merge_dataframes(ctx_dataframes)

                    # save merged dataframe to csv
                    filename = os.path.join(
                        output_merging_target.dst_dir,
                        f"{output_merging_target.campaign_id}_em27_export"
                        + f"_{date.strftime('%Y%m%d')}.csv",
                    )
                    with open(filename, "w") as f:
                        f.write(
                            procedures.export.get_metadata(
                                em27_metadata,
                                campaign,
                                sensor_data_contexts,
                                output_merging_target,
                            )
                        )
                        f.write(
                            merged_df.write_csv(
                                null_value="NaN",
                                has_header=True,
                                float_precision=9,
                            )
                        )

                progress.advance(task)


if __name__ == "__main__":
    run()
