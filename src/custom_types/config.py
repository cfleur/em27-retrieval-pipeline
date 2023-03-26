from datetime import datetime
from typing import Any, Callable, Literal, Optional, TypeVar, Union
from pydantic import BaseModel, validator
from tum_esm_utils.validators import (
    validate_str,
    validate_bool,
    validate_int,
)

T = TypeVar("T")


def _validate_list(
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
    allowed: Optional[list[T]] = None,
    required: Optional[list[T]] = None,
    forbidden: Optional[list[T]] = None,
) -> Callable[[Any, list[T]], list[T]]:
    def f(cls: Any, v: list[T]) -> list[T]:
        if not isinstance(v, list):
            raise ValueError(f'"{v}" is not a list')
        if min_len is not None and len(v) < min_len:
            raise ValueError(f'"{v}" has less than {min_len} elements')
        if max_len is not None and len(v) > max_len:
            raise ValueError(f'"{v}" has more than {max_len} elements')
        if allowed is not None:
            for item in v:
                if item not in allowed:
                    raise ValueError(f'"{item}" is not allowed')
        if required is not None:
            for item in required:
                if item not in v:
                    raise ValueError(f'"{v}" has to include "{item}"')
        if forbidden is not None:
            for item in forbidden:
                if item in v:
                    raise ValueError(f'"{v}" should not include "{item}"')
        return v

    return f


class LocationDataConfig(BaseModel):
    """Pydantic model:

    ```python
    github_repository: str
    access_token: Optional[str]
    ```
    """

    github_repository: str
    access_token: Optional[str]

    # validators
    _val_github_repository = validator(
        "github_repository",
        pre=True,
        allow_reuse=True,
    )(
        validate_str(regex=r"^[a-z0-9-_]+/[a-z0-9-_]+$"),
    )
    _val_access_token = validator("access_token", pre=True, allow_reuse=True,)(
        validate_str(nullable=True),
    )


class DataSrcDirsConfig(BaseModel):
    """Pydantic model:

    ```python
    datalogger: str
    vertical_profiles: str
    interferograms: str
    ```
    """

    datalogger: str
    vertical_profiles: str
    interferograms: str

    # validators
    _val_dir = validator(
        "datalogger",
        "vertical_profiles",
        "interferograms",
        pre=True,
        allow_reuse=True,
    )(
        validate_str(is_directory=True),
    )


class DataDstDirsConfig(BaseModel):
    results: str

    # validators
    _val_results = validator("results", pre=True, allow_reuse=True)(
        validate_str(is_directory=True)
    )


class VerticalProfilesFTPServerConfig(BaseModel):
    """Pydantic model:

    ```python
    email: str
    max_day_delay: int = 7
    upload_sleep: int = 60
    upload_timeout: int = 180
    download_sleep: int = 60
    download_timeout: int = 600
    ```
    """

    email: str
    max_day_delay: int = 7
    upload_sleep: int = 60
    upload_timeout: int = 180
    download_sleep: int = 60
    download_timeout: int = 600

    _val_dates = validator("email", pre=True, allow_reuse=True,)(
        validate_str(min_len=3),
    )

    _val_max_delay = validator("max_day_delay", pre=True, allow_reuse=True,)(
        validate_int(minimum=0, maximum=10),
    )

    _val_max_await = validator(
        "upload_sleep",
        "upload_timeout",
        "download_sleep",
        "download_timeout",
        pre=True,
        allow_reuse=True,
    )(
        validate_int(minimum=0),
    )


class VerticalProfilesRequestScopeConfig(BaseModel):
    """Pydantic model:

    ```python
    dst_dir: str
    from_date: str = "19000101"
    to_date: str = datetime.utcnow().strftime("%Y%m%d")
    ggg_2014_download: bool = True
    ggg_2020_download: bool = False
    ```
    """

    dst_dir: str
    from_date: str = "19000101"
    to_date: str = datetime.utcnow().strftime("%Y%m%d")
    ggg_2014_download: bool = True
    ggg_2020_download: bool = False

    _val_dates = validator("from_date", "to_date", pre=True, allow_reuse=True,)(
        validate_str(is_date_string=True),
    )
    _val_bools = validator(
        "ggg_2014_download",
        "ggg_2020_download",
        pre=True,
        allow_reuse=True,
    )(
        validate_bool(),
    )
    _val_dst_dir = validator("dst_dir", pre=True, allow_reuse=True,)(
        validate_str(is_directory=True),
    )


class AutomatedProffastDataFilterConfig(BaseModel):
    """Pydantic model:

    ```python
    sensor_ids_to_consider: list[str]
    start_date: str
    end_date: str
    min_days_delay: int
    ```
    """

    sensor_ids_to_consider: list[str]
    start_date: str
    end_date: str
    min_days_delay: int

    # validators
    _val_sensor_ids_to_consider = validator(
        "sensor_ids_to_consider", pre=True, allow_reuse=True
    )(
        _validate_list(min_len=1),
    )
    _val_date_string = validator(
        *["start_date", "end_date"],
        pre=True,
        allow_reuse=True,
    )(
        validate_str(is_date_string=True),
    )
    _val_min_days_delay = validator("min_days_delay", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=60),
    )


class GeneralConfig(BaseModel):
    """Pydantic model:

    ```python
    location_data: LocationDataConfig
    data_src_dirs: DataSrcDirsConfig
    data_dst_dirs: DataDstDirsConfig
    ```
    """

    location_data: LocationDataConfig
    data_src_dirs: DataSrcDirsConfig
    data_dst_dirs: DataDstDirsConfig


class VerticalProfilesConfig(BaseModel):
    """Pydantic model:

    ```python
    ftp_server: VerticalProfilesFTPServerConfig
    request_scope: VerticalProfilesRequestScopeConfig
    ```
    """

    ftp_server: VerticalProfilesFTPServerConfig
    request_scope: VerticalProfilesRequestScopeConfig


class AutomatedProffastConfig(BaseModel):
    """Pydantic model:

    ```python
    process_data_automatically: bool
    data_filter: AutomatedProffastDataFilterConfig
    ```
    """

    process_data_automatically: bool
    data_filter: AutomatedProffastDataFilterConfig

    # validators
    _val_bool = validator("process_data_automatically", pre=True, allow_reuse=True)(
        validate_bool()
    )


class OutputMergingTargetConfig(BaseModel):
    """Pydantic model:

    ```python
    campaign_id: str
    data_types: list[Literal[
        "gnd_p", "gnd_t", "app_sza", "azimuth",
        "xh2o", "xair", "xco2", "xch4", "xco", "xch4_s5p"
    ]]
    sampling_rate: str
    dst_dir: str
    ```
    """

    campaign_id: str
    data_types: list[
        Literal[
            "gnd_p",
            "gnd_t",
            "app_sza",
            "azimuth",
            "xh2o",
            "xair",
            "xco2",
            "xch4",
            "xco",
            "xch4_s5p",
        ]
    ]
    sampling_rate: Literal[
        "10m", "5m", "2m", "1m", "30s", "15s", "10s", "5s", "2s", "1s"
    ]
    dst_dir: str

    # validators
    _val_campaign_id = validator("campaign_id", pre=True, allow_reuse=True)(
        validate_str(),
    )
    _val_data_types = validator("data_types", pre=True, allow_reuse=True)(
        _validate_list(
            min_len=1,
            allowed=[
                "gnd_p",
                "gnd_t",
                "app_sza",
                "azimuth",
                "xh2o",
                "xair",
                "xco2",
                "xch4",
                "xco",
                "xch4_s5p",
            ],
        )
    )
    _val_sampling_rate = validator("sampling_rate", pre=True, allow_reuse=True)(
        validate_str(
            allowed=["10m", "5m", "2m", "1m", "30s", "15s", "10s", "5s", "2s", "1s"]
        ),
    )
    _val_dst_dir = validator("dst_dir", pre=True, allow_reuse=True)(
        validate_str(is_directory=True),
    )


class Config(BaseModel):
    general: GeneralConfig
    vertical_profiles: VerticalProfilesConfig
    automated_proffast: AutomatedProffastConfig
    output_merging_targets: list[OutputMergingTargetConfig]