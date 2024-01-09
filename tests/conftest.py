from importlib.resources import files

import pandas as pd
import pytest

from pygt3x.reader import FileReader
from tests import resources


@pytest.fixture
def gt3x_file():
    return files(resources).joinpath("small.gt3x")


@pytest.fixture
def agdc_file():
    return files(resources).joinpath("WRIST_rawLSB_032Hz_test.agdc")


@pytest.fixture(scope="package")
def agdc_file_with_temperature():
    return files(resources).joinpath("temperature/CPW1C48210013_baseline.agdc")


@pytest.fixture(scope="package")
def agdc_temperature(agdc_file_with_temperature):
    with FileReader(agdc_file_with_temperature) as reader:
        df = reader.temperature_to_pandas(calibrate=False)
    return df


@pytest.fixture(scope="package")
def agdc_temperature_cal(agdc_file_with_temperature):
    with FileReader(agdc_file_with_temperature) as reader:
        df = reader.temperature_to_pandas()
    return df


@pytest.fixture
def agdc_file_temperature_acc_cal():
    file = files(resources).joinpath(
        "temperature/Csv_Calibrated/CPW1C48210013_baseline_acceleration_calibrated.csv",
    )
    return pd.read_csv(file)


@pytest.fixture
def agdc_file_temperature_adxl():
    file = files(resources).joinpath(
        "temperature/Csv_ADC/CPW1C48210013_baseline_temperature_ADXL_ADC.csv",
    )
    return pd.read_csv(file)


@pytest.fixture
def agdc_file_temperature_mcu():
    file = files(resources).joinpath(
        "temperature/Csv_ADC/CPW1C48210013_baseline_temperature_MCU_ADC.csv",
    )
    return pd.read_csv(file)


@pytest.fixture
def agdc_file_temperature_adxl_cal():
    file = files(resources).joinpath(
        "temperature/Csv_Calibrated/"
        "CPW1C48210013_baseline_temperature_ADXL_calibrated.csv",
    )
    return pd.read_csv(file)


@pytest.fixture
def agdc_file_temperature_mcu_cal():
    file = files(resources).joinpath(
        "temperature/Csv_Calibrated/"
        "CPW1C48210013_baseline_temperature_MCU_calibrated.csv",
    )
    return pd.read_csv(file)


@pytest.fixture
def nhanes_file():
    return files(resources).joinpath("AI1_NEO1B41100255_2016-10-17.gt3x")


@pytest.fixture
def v1_file():
    return files(resources).joinpath("neo.gt3x")


@pytest.fixture
def v1_gt():
    return files(resources).joinpath("neo.csv")


@pytest.fixture
def calibrated_csv_file():
    return files(resources).joinpath("WRIST_rawCalibrated_032Hz.csv")


@pytest.fixture
def ism_enabled_file():
    return files(resources).joinpath("ISM_Enabled.gt3x")


@pytest.fixture
def ism_disabled_file():
    return files(resources).joinpath("ISM_Disabled.gt3x")


@pytest.fixture
def calibrated_dataframe(calibrated_csv_file):
    return pd.read_csv(calibrated_csv_file, header=10)


@pytest.fixture
def wrist_csv_file():
    return files(resources).joinpath("WRIST_rawLSB_032Hz.csv")


@pytest.fixture
def wrist_dataframe(wrist_csv_file):
    return pd.read_csv(wrist_csv_file, header=10)
