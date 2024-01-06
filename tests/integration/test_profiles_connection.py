import pytest
import ftplib
import warnings
from src import types


@pytest.mark.order(3)
@pytest.mark.integration
def test_profiles_connection() -> None:
    config = types.Config.load()
    if config.profiles is None:
        warnings.warn(pytest.PytestWarning("Profiles configured"))
        return
    with ftplib.FTP(
        host="ccycle.gps.caltech.edu",
        passwd=config.profiles.server.email,
        user="anonymous",
        timeout=60,
    ) as ftp:
        print(ftp.nlst("ginput-jobs"))
