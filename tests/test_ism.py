import pandas as pd
import pytest

from pygt3x.calibration import CalibratedReader
from pygt3x.reader import FileReader


def test_ism_enabled(ism_enabled_file, ism_disabled_file):
    with FileReader(ism_enabled_file) as reader:
        calibrated = CalibratedReader(reader)
        df_enabled = calibrated.to_pandas()
    with FileReader(ism_disabled_file) as reader:
        calibrated = CalibratedReader(reader)
        df_disabled = calibrated.to_pandas()
    assert (df_enabled.X.groupby(level=0).count() == 30).all()
    assert (df_enabled.loc[1616169537:1616169574, "X"] == df_enabled.loc[1616169537:1616169574, "X"].iloc[0]).all()
    assert (df_enabled.index == df_disabled.index[:5370]).all()
