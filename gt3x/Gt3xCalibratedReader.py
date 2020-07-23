import gt3x.Gt3xFileReader
import gt3x.Gt3xRawEvent
import gt3x.AccelerationSample
import gt3x.Gt3xEventTypes
import pandas as pd
import gt3x.CalibrationV2Service


class Gt3xCalibratedReader:
    """
    Calibrated event reader. Will calibrate activity events as they are read.
    """

    def __init__(self, source: gt3x.Gt3xFileReader):
        self.source = source

    def read_info(self):
        """
        Returns info dictionary from source reader
        """
        return self.source.read_info()

    def read_calibration(self):
        return self.source.read_calibration()

    def calibrate_acceleration(self, raw_event: gt3x.Gt3xRawEvent):
        """
        Calibrates acceleration samples.

        Parameters:
            raw_event (Gt3xRawEvent): Activity event to calibrate.

        """
        if gt3x.Gt3xEventTypes(raw_event.header.eventType) == gt3x.Gt3xEventTypes.Activity3:
            payload = gt3x.Activity3Payload(raw_event.payload, raw_event.header.timestamp)
        elif gt3x.Gt3xEventTypes(raw_event.header.eventType) == gt3x.Gt3xEventTypes.Activity:
            payload = gt3x.Activity1Payload(raw_event.payload, raw_event.header.timestamp)
        elif gt3x.Gt3xEventTypes(raw_event.header.eventType) == gt3x.Gt3xEventTypes.Activity2:
            payload = gt3x.Activity2Payload(raw_event.payload, raw_event.header.timestamp)
        else:
            raise ValueError("Cannot calibrate non-activity event type")

        calibration = self.source.read_calibration()
        info = self.read_info()

        if calibration is None or calibration['isCalibrated']:
            # Data is already calibrated, so just return unscaled values
            accel_scale = info.get_acceleration_scale()
            raw_event.CalibratedAcceleration = [
                gt3x.AccelerationSample(raw_event.header.timestamp, x=sample.x / accel_scale, y=sample.y / accel_scale,
                                        z=sample.z / accel_scale) for sample in payload.AccelerationSamples]
        elif calibration['calibrationMethod'] == 2:
            # Use calibration method 2 to calibrate activity
            sample_rate = info.get_sample_rate()
            raw_event.CalibratedAcceleration = self.calibrate_v2(payload.AccelerationSamples, calibration, sample_rate)
        else:
            raise NotImplementedError(f"Unknown calibration method: {calibration['calibrationMethod']}")

    @staticmethod
    def calibrate_v2(samples, calibration: dict, sample_rate: int):
        calibration_service = gt3x.CalibrationV2Service(calibration, sample_rate)

        return calibration_service.calibrate_samples(samples)

    def read_events(self, num_rows: int = None):
        """
        Read events from source and calibrates activity.

        Parameters:
            num_rows (int): Optionally limits number of rows to return.

        """
        for raw_event in self.source.read_events(num_rows):
            if not gt3x.Gt3xEventTypes(raw_event.header.eventType) in [gt3x.Gt3xEventTypes.Activity,
                                                                       gt3x.Gt3xEventTypes.Activity2,
                                                                       gt3x.Gt3xEventTypes.Activity3]:
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
