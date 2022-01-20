from typing import Union

import pandas as pd

from gt3x.AccelerationSample import AccelerationSample
from gt3x.Activity1Payload import Activity1Payload
from gt3x.Activity2Payload import Activity2Payload
from gt3x.Activity3Payload import Activity3Payload
from gt3x.CalibrationV2Service import CalibrationV2Service
from gt3x.Gt3xEventTypes import Gt3xEventTypes
from gt3x.Gt3xFileReader import Gt3xFileReader
from gt3x.Gt3xRawEvent import Gt3xRawEvent


class Gt3xCalibratedReader:
    """Calibrated event reader.

    Will calibrate activity events as they are read.
    """

    def __init__(self, source: Gt3xFileReader):
        self.source = source

    def read_info(self):
        """
        Returns info dictionary from source reader
        """
        return self.source.read_info()

    def read_calibration(self):
        return self.source.read_calibration()

    def calibrate_acceleration(self, raw_event: Gt3xRawEvent):
        """
        Calibrates acceleration samples.

        Parameters:
            raw_event (Gt3xRawEvent): Activity event to calibrate.

        """
        payload: Union[Activity1Payload,
                       Activity2Payload,
                       Activity3Payload]
        if Gt3xEventTypes(
                raw_event.header.eventType
        ) == Gt3xEventTypes.Activity3:
            payload = Activity3Payload(
                raw_event.payload, raw_event.header.timestamp)
        elif Gt3xEventTypes(
                raw_event.header.eventType
        ) == Gt3xEventTypes.Activity:
            payload = Activity1Payload(
                raw_event.payload, raw_event.header.timestamp)
        elif Gt3xEventTypes(
                raw_event.header.eventType
        ) == Gt3xEventTypes.Activity2:
            payload = Activity2Payload(
                raw_event.payload, raw_event.header.timestamp)
        else:
            raise ValueError(
                "Cannot calibrate non-activity event type")

        calibration = self.source.read_calibration()
        info = self.read_info()

        if calibration is None or calibration['isCalibrated']:
            # Data is already calibrated, so just return unscaled values
            accel_scale = info.get_acceleration_scale()
            raw_event.CalibratedAcceleration = [
                AccelerationSample(
                    raw_event.header.timestamp,
                    x=sample.x / accel_scale,
                    y=sample.y / accel_scale,
                    z=sample.z / accel_scale
                ) for sample in payload.AccelerationSamples]
        elif calibration['calibrationMethod'] == 2:
            # Use calibration method 2 to calibrate activity
            sample_rate = info.get_sample_rate()
            raw_event.CalibratedAcceleration = self.calibrate_v2(
                payload.AccelerationSamples, calibration, sample_rate)
        else:
            raise NotImplementedError(
                f"Unknown calibration method: "
                f"{calibration['calibrationMethod']}")

    @staticmethod
    def calibrate_v2(samples, calibration: dict, sample_rate: int):
        calibration_service = CalibrationV2Service(
            calibration, sample_rate)

        return calibration_service.calibrate_samples(samples)

    def read_events(self, num_rows: int = None):
        """
        Read events from source and calibrates activity.

        Parameters:
            num_rows (int): Optionally limits number of rows to return.

        """
        for raw_event in self.source.read_events(num_rows):
            if not Gt3xEventTypes(
                    raw_event.header.eventType) in [
                       Gt3xEventTypes.Activity,
                       Gt3xEventTypes.Activity2,
                       Gt3xEventTypes.Activity3]:
                continue
            self.calibrate_acceleration(raw_event)
            yield raw_event

    def get_samples(self):
        for raw_event in self.read_events():
            self.calibrate_acceleration(raw_event)
            for sample in raw_event.CalibratedAcceleration:
                yield sample.timestamp, sample.x, sample.y, sample.z

    def to_pandas(self):
        """
        Returns acceleration data as pandas data frame
        """
        col_names = ['Timestamp', 'X', 'Y', 'Z']
        data = self.get_samples()
        df = pd.DataFrame(data, columns=col_names)
        df.index = df["Timestamp"]
        del df["Timestamp"]
        return df
