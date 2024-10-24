"""Calibrate accelerometer values."""

from typing import Dict

import numpy as np
from numpy import typing as npt


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
        return np.matmul(
            self.sensitivity_matrix,
            (sample - self.offset_vector).transpose(),
        ).transpose()
