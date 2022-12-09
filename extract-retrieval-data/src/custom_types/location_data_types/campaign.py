from typing import Literal
from pydantic import BaseModel

from src.custom_types.location_data_types import Date, SensorId, LocationId


Direction = Literal["center", "north", "south", "east", "west"]


class CampaignStation(BaseModel):
    """A campaign's station, e.g.,
    {
        "sensor": "ma",
        "default_location": "HAW",
        "direction": <class 'Direction'>
    }.
    """

    sensor: SensorId
    default_location: LocationId
    direction: Direction


class Campaign(BaseModel):
    """A campaign, e.g., "Hamburg":
    {
        "from_date": "20220524",
        "to_date": "20270715",
        "stations": list[<class 'CampaignStation'>]
    }.
    """

    from_date: Date
    to_date: Date
    stations: list[CampaignStation]
