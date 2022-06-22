import pytest

from pygt3x.calibration import CalibratedReader
from pygt3x.reader import FileReader


def test_read_agdc(agdc_file):
    with FileReader(agdc_file) as reader:
        calibrated = CalibratedReader(reader)
        df = calibrated.to_pandas()
    assert df.mean().X == pytest.approx(1.118586370635872)
    assert df.mean().Y == pytest.approx(0.4294534356312101)
    assert df.mean().Z == pytest.approx(-0.08104933668082379)


def test_read_v1(v1_file):
    with FileReader(v1_file) as reader:
        df = reader.to_pandas()
    assert df.mean().X == pytest.approx(0.0632553876916240)
    assert df.mean().Y == pytest.approx(-0.06169351255276604)
    assert df.mean().Z == pytest.approx(-0.6742046211952898)
