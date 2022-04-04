import numpy as np
import pandas as pd

from pygt3x.callibration_v2_service import CalibrationV2Service
from pygt3x.reader import FileReader


class CalibratedReader:
    """Calibrated event reader.

    Will calibrate activity events as they are read.
    """

    def __init__(self, source: FileReader):
        self.source = source
        self.acceleration = np.concatenate(list(self.source.get_acceleration()))

    def calibrate_acceleration(self):
        """Calibrates acceleration samples."""
        calibration = self.source.calibration
        info = self.source.info
        acceleration = self.acceleration

        if calibration is None or calibration["isCalibrated"]:
            # Data is already calibrated, so just return unscaled values
            accel_scale = info.get_acceleration_scale()
            calibrated_acceleration = np.concatenate(
                (
                    acceleration[:, :-3],
                    acceleration[:, -3:] / accel_scale,
                ),
                axis=1,
            )
        elif calibration["calibrationMethod"] == 2:
            # Use calibration method 2 to calibrate activity
            sample_rate = info.get_sample_rate()
            calibrated_acceleration = self.calibrate_v2(
                acceleration, calibration, sample_rate
            )
        else:
            raise NotImplementedError(
                f"Unknown calibration method: " f"{calibration['calibrationMethod']}"
            )
        return calibrated_acceleration

    @staticmethod
    def calibrate_v2(samples, calibration: dict, sample_rate: int):
        calibration_service = CalibrationV2Service(calibration, sample_rate)
        return calibration_service.calibrate_samples(samples)

    def to_pandas(self):
        """
        Returns acceleration data as pandas data frame
        """
        col_names = ["Timestamp", "X", "Y", "Z"]
        data = self.calibrate_acceleration()
        df = pd.DataFrame(data, columns=col_names)
        df.index = df["Timestamp"]
        del df["Timestamp"]
        return df
