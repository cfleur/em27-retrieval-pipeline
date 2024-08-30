import datetime
import em27_metadata
import tum_esm_utils
from .. import types, utils


def get_header(
    em27_metadata_interface: em27_metadata.interfaces.EM27MetadataInterface,
    campaign: em27_metadata.types.CampaignMetadata,
    sensor_data_contexts: list[em27_metadata.types.SensorDataContext],
    export_target: types.ExportTargetConfig,
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
        f"    retrieval software:     {export_target.retrieval_algorithm}",
        f"    meteorological model:   {export_target.atmospheric_profile_model}",
        f"    file generated by:      https://github.com/tum-esm/em27-retrieval-pipeline",
        f"    pipeline commit sha:    {tum_esm_utils.shell.get_commit_sha()}",
        f"    pipeline version:       {utils.functions.get_pipeline_version()}",
        f"    file generated at:      {datetime.datetime.now()}",
        f"",
        f"FILE CONTENT:",
        f"    campaign id:            {campaign.campaign_id}",
        f"    campaign sensor ids:    {', '.join(campaign.sensor_ids)}",
        f"    campaign location ids:  {', '.join(campaign.location_ids)}",
        f"    date:                   {sensor_data_contexts[0].from_datetime.strftime('%Y-%m-%d')}",
        f"    data types:             {', '.join(export_target.data_types)}",
        f"    sampling rate:          {export_target.sampling_rate}",
        f"",
    ]

    header_lines.append("SENSOR SERIAL NUMBERS:")
    for sid in campaign.sensor_ids:
        s = next(
            filter(
                lambda s: s.sensor_id == sid,
                em27_metadata_interface.sensors.root
            )
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
                lambda l: l.location_id == lid,
                em27_metadata_interface.locations.root
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
