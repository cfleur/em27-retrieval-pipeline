import os
import datetime
import em27_metadata
import tum_esm_utils
from src import utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)


def get_pipeline_version() -> str:
    """Returns the current version (`x.y.z`) of the pipeline."""

    with open(os.path.join(PROJECT_DIR, "pyproject.toml"), "r") as f:
        version_line = f.read().split("\n")[2]
        assert version_line.startswith("version = ")
        return version_line.split(" = ")[1].strip(' "')


def get_header(
    em27_metadata_storage: em27_metadata.interfaces.EM27MetadataInterface,
    campaign: em27_metadata.types.CampaignMetadata,
    sensor_data_contexts: list[em27_metadata.types.SensorDataContext],
    output_merging_target: utils.config.OutputMergingTargetConfig,
) -> str:
    """Returns a description of the campaign."""

    header_lines = [
        f"CONTACT:",
        f"    person:                 Prof. Dr.-Ing. Jia Chen <jia.chen@tum.de>",
        f"    department:             Professorship of Environmental Sensing and Modeling",
        f"    institution:            Technical University of Munich",
        f"    website:                https://www.ee.cit.tum.de/en/esm",
        f"",
        f"FILE GENERATION:",
        f"    retrieval software:     Proffast 2.2",
        f"    meteorological model:   GGG2014",
        f"    file generated by:      https://github.com/tum-esm/em27-retrieval-pipeline",
        f"    pipeline commit sha:    {tum_esm_utils.shell.get_commit_sha()}",
        f"    pipeline version:       {get_pipeline_version()}",
        f"    file generated at:      {datetime.datetime.now()}",  # type: ignore
        f"",
        f"FILE CONTENT:",
        f"    campaign id:            {campaign.campaign_id}",
        f"    campaign sensor ids:    {', '.join(campaign.sensor_ids)}",
        f"    campaign location ids:  {', '.join(campaign.location_ids)}",
        f"    date:                   {sensor_data_contexts[0].from_datetime.strftime('%Y-%m-%d')}",
        f"    data types:             {', '.join(output_merging_target.data_types)}",
        f"    sampling rate:          {output_merging_target.sampling_rate}",
        f"",
    ]

    header_lines.append("SENSOR SERIAL NUMBERS:")
    for sid in campaign.sensor_ids:
        s = next(
            filter(lambda s: s.sensor_id == sid, em27_metadata_storage.sensors)
        )
        header_lines.append(
            "    " + tum_esm_utils.text.
            pad_string(f"{sid}: ", pad_position="right", min_width=10) +
            f"{s.serial_number}"
        )

    header_lines.append("")

    header_lines.append("LOCATION COORDINATES [lat, lon, alt]:")
    for lid in campaign.location_ids:
        l = next(
            filter(
                lambda l: l.location_id == lid, em27_metadata_storage.locations
            )
        )
        header_lines.append(
            "    " + tum_esm_utils.text.
            pad_string(f"{lid}: ", pad_position="right", min_width=10) +
            f"{l.lat}, {l.lon}, {l.alt} "
        )

    header_lines.append("")

    header_lines.append("SENSOR LOCATIONS:")
    for sid in campaign.sensor_ids:
        ctxs = list(
            filter(lambda sdc: sdc.sensor_id == sid, sensor_data_contexts)
        )
        if len(ctxs) == 0:
            header_lines.append(f"    {sid}: no data")
        else:
            lids = [ctx.location.location_id for ctx in ctxs]
            header_lines.append(f"    {sid}: {', '.join(lids)}")

    header_lines.append("")

    header_lines = ["## " + line for line in header_lines]
    header_lines.append("#" * 80)
    return "\n".join(header_lines) + "\n"