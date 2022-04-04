import numpy as np


class CalibrationV2Service:
    def __init__(self, calibration: dict, sample_rate: int):
        self.offset_vector = np.array([[0, 0, 0]])
        self.sensitivity_matrix = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
        self.set_calibration(calibration, sample_rate)

    def set_calibration(self, calibration: dict, sample_rate: int):
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

    def calibrate_samples(self, sample):
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
