import numpy as np
import pandas as pd
import pytest

from pygt3x.reader import FileReader


def test_read_agdc(agdc_file):
    with FileReader(agdc_file) as reader:
        df = reader.to_pandas()
    assert df.mean().X == pytest.approx(1.1185734272003174)
    assert df.mean().Y == pytest.approx(0.4293369650840759)
    assert df.mean().Z == pytest.approx(-0.08194955438375473)


def test_read_agdc_calibrated_acc(
    agdc_file_with_temperature, agdc_file_temperature_acc_cal
):
    with FileReader(agdc_file_with_temperature) as reader:
        df = reader.to_pandas()
    np.testing.assert_allclose(df.X.values, agdc_file_temperature_acc_cal.x_g.values)
    np.testing.assert_allclose(df.Y.values, agdc_file_temperature_acc_cal.y_g.values)
    np.testing.assert_allclose(df.Z.values, agdc_file_temperature_acc_cal.z_g.values)


def test_read_agdc_temp_adxl(agdc_temperature, agdc_file_temperature_adxl):
    np.testing.assert_allclose(
        agdc_temperature.TemperatureADXL.values,
        agdc_file_temperature_adxl.celsius_adc.values,
    )


def test_read_agdc_temp_mcu(agdc_temperature, agdc_file_temperature_mcu):
    np.testing.assert_allclose(
        agdc_temperature.TemperatureMCU.values,
        agdc_file_temperature_mcu.celsius_adc.values,
    )


def test_read_agdc_temp_adxl_cal(agdc_temperature_cal, agdc_file_temperature_adxl_cal):
    assert (
        np.abs(
            agdc_temperature_cal.TemperatureADXL.values
            - agdc_file_temperature_adxl_cal.celsius.values
        ).max()
        < 1e-6
    )


def test_read_agdc_temp_mcu_cal(agdc_temperature_cal, agdc_file_temperature_mcu_cal):
    assert (
        np.abs(
            agdc_temperature_cal.TemperatureMCU.values
            - agdc_file_temperature_mcu_cal.celsius.values
        ).max()
        < 1e-6
    )


def test_read_v1(v1_file, v1_gt):
    expected = pd.read_csv(v1_gt, skiprows=11, names=("X", "Y", "Z")).mean()
    with FileReader(v1_file) as reader:
        df = reader.to_pandas().mean()
    assert df.X == pytest.approx(expected.X)
    assert df.Y == pytest.approx(expected.Y)
    assert df.Z == pytest.approx(expected.Z)


def test_read_nhanes(nhanes_file):
    with FileReader(nhanes_file) as reader:
        df = reader.to_pandas()
        assert len(df) == 18143953
