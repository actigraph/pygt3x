import pandas as pd
import pytest

from pygt3x.calibration import CalibratedReader
from pygt3x.reader import FileReader


def test_read_agdc(agdc_file):
    with FileReader(agdc_file) as reader:
        calibrated = CalibratedReader(reader)
        df = calibrated.to_pandas()
    assert df.mean().X == pytest.approx(1.1185734272003174)
    assert df.mean().Y == pytest.approx(0.4293369650840759)
    assert df.mean().Z == pytest.approx(-0.08194955438375473)


def test_read_v1(v1_file, v1_gt):
    expected = pd.read_csv(v1_gt, skiprows=11, names=("X", "Y", "Z")).mean()
    with FileReader(v1_file) as reader:
        df = reader.to_pandas().mean()
    assert df.X == pytest.approx(expected.X)
    assert df.Y == pytest.approx(expected.Y)
    assert df.Z == pytest.approx(expected.Z)
