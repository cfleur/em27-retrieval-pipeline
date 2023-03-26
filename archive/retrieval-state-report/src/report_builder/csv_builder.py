from datetime import datetime

import pandas as pd
import os


class CsvReportBuilder:

    df: pd.DataFrame = None
    DAYS = ["Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa.", "So."]

    def __init__(self, directory_name: str, file_name: str):
        self.file_name = file_name
        self.directory_name = directory_name

    def create_output(
        self,
        series: pd.Series,
        subreport_name: str,
        sensor: str | None = None,
        status: str | None = None
    ) -> None:
        if sensor is None or status is None:
            raise ValueError('Sensor and status cannot be None')
        series.name = sensor + " " + status
        series.index.name = "sensor"
        cdf = pd.DataFrame(series).transpose()
        if self.df is None:
            self.df = cdf
        else:
            self.df = pd.concat([self.df, cdf])
            self.df.fillna(0, inplace=True)

    def save_file(self) -> None:
        days_of_week = []
        for col in self.df.columns:
            days_of_week.append(self.DAYS[col.weekday()])
        self.df.loc["Tag"] = days_of_week
        os.makedirs(self.directory_name, exist_ok=True)
        self.df.transpose().to_csv(
            "{}/{}.csv".format(self.directory_name, self.file_name)
        )