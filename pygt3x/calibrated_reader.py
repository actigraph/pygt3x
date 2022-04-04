from typing import Union

import numpy as np
import pandas as pd

from pygt3x.activity_payload import Activity1Payload
from pygt3x.activity_payload import Activity2Payload
from pygt3x.activity_payload import Activity3Payload
from pygt3x.callibration_v2_service import CalibrationV2Service
from pygt3x.componenets import AccelerationSample
from pygt3x.componenets import RawEvent
from pygt3x.events import Types
from pygt3x.reader import FileReader


class CalibratedReader:
    """Calibrated event reader.

    Will calibrate activity events as they are read.
    """

    def __init__(self, source: FileReader):
        self.source = source

    def read_info(self):
        """
        Returns info dictionary from source reader
        """
        return self.source.read_info()

    def read_calibration(self):
        return self.source.read_calibration()

    def calibrate_acceleration(self, raw_event: RawEvent):
        """
        Calibrates acceleration samples.

        Parameters:
            raw_event (RawEvent): Activity event to calibrate.

        """
        payload: Union[Activity1Payload, Activity2Payload, Activity3Payload]
        if Types(raw_event.header.eventType) == Types.Activity3:
            payload = Activity3Payload(raw_event.payload, raw_event.header.timestamp)
        elif Types(raw_event.header.eventType) == Types.Activity:
            payload = Activity1Payload(raw_event.payload, raw_event.header.timestamp)
        elif Types(raw_event.header.eventType) == Types.Activity2:
            payload = Activity2Payload(raw_event.payload, raw_event.header.timestamp)
        else:
            raise ValueError("Cannot calibrate non-activity event type")

        calibration = self.source.read_calibration()
        info = self.read_info()

        if calibration is None or calibration["isCalibrated"]:
            # Data is already calibrated, so just return unscaled values
            accel_scale = info.get_acceleration_scale()
            raw_event.calibrated_acceleration = np.concatenate(
                (
                    payload.AccelerationSamples[:, :-3],
                    payload.AccelerationSamples[:, -3:] / accel_scale,
                ),
                axis=1,
            )
        elif calibration["calibrationMethod"] == 2:
            # Use calibration method 2 to calibrate activity
            sample_rate = info.get_sample_rate()
            raw_event.calibrated_acceleration = self.calibrate_v2(
                payload.AccelerationSamples, calibration, sample_rate
            )
        else:
            raise NotImplementedError(
                f"Unknown calibration method: " f"{calibration['calibrationMethod']}"
            )

    @staticmethod
    def calibrate_v2(samples, calibration: dict, sample_rate: int):
        calibration_service = CalibrationV2Service(calibration, sample_rate)
        return calibration_service.calibrate_samples(samples)

    def read_events(self, num_rows: int = None):
        """
        Read events from source and calibrates activity.

        Parameters:
            num_rows (int): Optionally limits number of rows to return.

        """
        for raw_event in self.source.read_events(num_rows):
            if not Types(raw_event.header.eventType) in [
                Types.Activity,
                Types.Activity2,
                Types.Activity3,
            ]:
                continue
            self.calibrate_acceleration(raw_event)
            yield raw_event

    def get_samples(self):
        for raw_event in self.read_events():
            yield raw_event.calibrated_acceleration

    def to_pandas(self):
        """
        Returns acceleration data as pandas data frame
        """
        col_names = ["Timestamp", "X", "Y", "Z"]
        data = np.concatenate(list(self.get_samples()))
        df = pd.DataFrame(data, columns=col_names)
        df.index = df["Timestamp"]
        del df["Timestamp"]
        return df
