import pytest

from pygt3x.calibration import CalibrationV2Service
from pygt3x.reader import FileReader

test_calibration = {
    "positiveZeroGOffsetX_32": 256,
    "positiveZeroGOffsetY_32": 256,
    "positiveZeroGOffsetZ_32": 256,
    "negativeZeroGOffsetX_32": -256,
    "negativeZeroGOffsetY_32": -256,
    "negativeZeroGOffsetZ_32": -256,
    "zeroGOffsetX_32": 0,
    "zeroGOffsetY_32": 0,
    "zeroGOffsetZ_32": 0,
    "offsetX_32": 37,
    "offsetY_32": 13,
    "offsetZ_32": 46,
    "sensitivityXX_32": 24804,
    "sensitivityYY_32": 26621,
    "sensitivityZZ_32": 24304,
    "sensitivityXY_32": -615,
    "sensitivityXZ_32": -222,
    "sensitivityYZ_32": -28,
}


def test_read(gt3x_file):
    with FileReader(gt3x_file) as reader:
        uncalibrated_df = reader.to_pandas(calibrate=False).mean()
        df = reader.to_pandas().mean()
    assert uncalibrated_df.X == pytest.approx(-76.11525538046477)
    assert uncalibrated_df.Y == pytest.approx(87.69668894475443)
    assert uncalibrated_df.Z == pytest.approx(103.93508015342586)
    assert df.X == pytest.approx(-0.2973251938819885)
    assert df.Y == pytest.approx(0.3425652086734772)
    assert df.Z == pytest.approx(0.40599629282951355)


def test_calibrate_32hz(calibrated_dataframe, wrist_dataframe):
    service = CalibrationV2Service(test_calibration, 32)
    output = service.calibrate_samples(wrist_dataframe.to_numpy())
    baseline_epsilon = 1e-14

    assert abs(calibrated_dataframe.to_numpy() - output).max().max() <= baseline_epsilon
