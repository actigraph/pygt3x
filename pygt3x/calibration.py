"""Calibrate accelerometer values."""
from typing import Dict

import numpy as np
from numpy import typing as npt
import pandas as pd

from pygt3x.reader import FileReader


class CalibrationV2Service:
    """Calibration service.

    Parameters:
    -----------
    calibration
        Calibration info
    sample_rate
        Sample per (per S)
    """

    def __init__(self, calibration: Dict[str, int], sample_rate: int):
        """Initialise fields."""
        self.offset_vector = np.array([[0, 0, 0]])
        self.sensitivity_matrix = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
        self.set_calibration(calibration, sample_rate)

    def set_calibration(self, calibration: Dict[str, int], sample_rate: int):
        """Parse calibration info.

        Parameters:
        -----------
        calibration
            Calibration info
        sample_rate
            Sample per (per S)
        """
        offset_x = float(calibration[f"offsetX_{sample_rate}"])
        offset_y = float(calibration[f"offsetY_{sample_rate}"])
        offset_z = float(calibration[f"offsetZ_{sample_rate}"])

        sensitivity_xx = float(calibration[f"sensitivityXX_{sample_rate}"])
        sensitivity_yy = float(calibration[f"sensitivityYY_{sample_rate}"])
        sensitivity_zz = float(calibration[f"sensitivityZZ_{sample_rate}"])

        sensitivity_xy = float(calibration[f"sensitivityXY_{sample_rate}"])
        sensitivity_xz = float(calibration[f"sensitivityXZ_{sample_rate}"])
        sensitivity_yz = float(calibration[f"sensitivityYZ_{sample_rate}"])

        s11 = (sensitivity_xx * 0.01) ** -1.0
        s12 = ((sensitivity_xy * 0.01 + 250) ** -1.0) - 0.004
        s13 = ((sensitivity_xz * 0.01 + 250) ** -1.0) - 0.004

        s21 = ((sensitivity_xy * 0.01 + 250) ** -1.0) - 0.004
        s22 = (sensitivity_yy * 0.01) ** -1.0
        s23 = ((sensitivity_yz * 0.01 + 250) ** -1.0) - 0.004

        s31 = ((sensitivity_xz * 0.01 + 250) ** -1.0) - 0.004
        s32 = ((sensitivity_yz * 0.01 + 250) ** -1.0) - 0.004
        s33 = (sensitivity_zz * 0.01) ** -1.0

        self.offset_vector = np.array([[offset_x, offset_y, offset_z]])
        self.sensitivity_matrix = np.array(
            [[s11, s21, s31], [s12, s22, s32], [s13, s23, s33]]
        )

    def calibrate_samples(self, sample: npt.NDArray):
        """Calibrate acceleration info.

        Parameters:
        -----------
        sample
            Acceleration data
        """
        return np.concatenate(
            (
                sample[:, :-3],
                np.matmul(
                    self.sensitivity_matrix,
                    (sample[:, -3:] - self.offset_vector).transpose(),
                ).transpose(),
            ),
            axis=1,
        )


class CalibratedReader:
    """Calibrated event reader.

    Will calibrate activity events as they are read.

    Parameters:
    -----------
    source
        Input file reader
    """

    def __init__(self, source: FileReader):
        """Initialise fields."""
        self.source = source
        data = list(self.source.get_acceleration())
        if len(data) == 0:
            self.acceleration = np.empty((0, 4))
        else:
            self.acceleration = np.concatenate(data)

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
    def calibrate_v2(
        samples: npt.NDArray, calibration: Dict[str, int], sample_rate: int
    ):
        """Calibrates acceleration samples.

        Parameters:
        -----------
        sample
            Acceleration data
        calibration
            Calibration info
        sample_rate
            File sample rate
        """
        calibration_service = CalibrationV2Service(calibration, sample_rate)
        return calibration_service.calibrate_samples(samples)

    def to_pandas(self):
        """Return acceleration data as pandas data frame."""
        col_names = ["Timestamp", "X", "Y", "Z"]
        data = self.calibrate_acceleration()
        df = pd.DataFrame(data, columns=col_names)
        df.set_index("Timestamp", drop=True, inplace=True)
        df = df.apply(lambda x: pd.to_numeric(x, downcast="float"))
        return df
