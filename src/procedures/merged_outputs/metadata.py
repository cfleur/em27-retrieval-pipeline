import pendulum
import tum_esm_em27_metadata
import tum_esm_utils

from src import custom_types


def get_metadata(
    campaign: tum_esm_em27_metadata.types.CampaignMetadata,
    sensor_data_contexts: dict[str, tum_esm_em27_metadata.types.SensorDataContext],
    output_merging_target: custom_types.config.OutputMergingTargetConfig,
) -> str:
    """Returns a description of the campaign."""

    # TODO: include all sensor serial numbers
    # TODO: include all location coordinates

    metadata_lines = [
        f"CONTACT:",
        f"    person:                Prof. Dr.-Ing. Jia Chen <jia.chen@tum.de>",
        f"    department:            Professorship of Environmental Sensing and Modeling",
        f"    institution:           Technical University of Munich",
        f"    website:               https://www.ee.cit.tum.de/en/esm",
        f"",
        f"FILE GENERATION:",
        f"    retrieval software:    Proffast 2.2",
        f"    meteorological model:  GGG2014",
        f"    file generated by:     https://github.com/tum-esm/automated-retrieval-pipeline",
        f"    pipeline commit sha:   {tum_esm_utils.shell.get_commit_sha()}",
        f"    file generated at:     {pendulum.now().to_w3c_string()}",  # type: ignore
        f"",
        f"FILE CONTENT:",
        f"    campaign id:           {campaign.campaign_id}",
        f"    date:                  {next(c for c in sensor_data_contexts.values()).from_datetime.strftime('%Y-%m-%d')}",
        f"    data types:            {', '.join(output_merging_target.data_types)}",
        f"    sampling rate:         {output_merging_target.sampling_rate}",
    ]

    metadata_lines.append("")

    metadata_lines.append("SENSOR SERIAL NUMBERS:")
    for s in campaign.stations:
        sdc = sensor_data_contexts.get(s.sensor_id, None)
        serial_numer = "no data" if (sdc is None) else sdc.serial_number
        metadata_lines.append(f"    {s.sensor_id}: {serial_numer}")

    metadata_lines.append("")

    metadata_lines.append("SENSOR LOCATIONS:")
    campaign_location_ids = [s.default_location_id for s in campaign.stations]
    for s in campaign.stations:
        sdc = sensor_data_contexts.get(s.sensor_id, None)
        location_id = "no data" if (sdc is None) else sdc.location.location_id

        if fixed_sensor_locations:
            included_in_file = location_id == s.default_location_id
        else:
            included_in_file = location_id in campaign_location_ids

        metadata_lines.append(
            f"    {s.sensor_id}: {location_id} "
            + f"(campaign default: {s.default_location_id})"
            + (" NOT INCLUDED IN THIS FILE" if not included_in_file else "")
        )

    metadata_lines.append("")

    metadata_lines.append("SENSOR COORDINATES (lat, lon, alt):")
    for s in campaign.stations:
        sdc = sensor_data_contexts.get(s.sensor_id, None)
        lat = "no data" if (sdc is None) else sdc.location.lat
        lon = "no data" if (sdc is None) else sdc.location.lon
        alt = "no data" if (sdc is None) else sdc.location.alt
        metadata_lines.append(f"    {s.sensor_id}: {lat}, {lon}, {alt} ")

    metadata_lines.append("")

    metadata_lines = ["## " + line for line in metadata_lines]
    metadata_lines.append("#" * 80)
    return "\n".join(metadata_lines)
