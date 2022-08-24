import pandas as pd
import pytest

from pygt3x.calibration import CalibratedReader
from pygt3x.reader import FileReader


@pytest.fixture
def gt3x_file(resource_path_root):
    return resource_path_root / "small.gt3x"


@pytest.fixture
def agdc_file(resource_path_root):
    return resource_path_root / "WRIST_rawLSB_032Hz_test.agdc"


@pytest.fixture(scope="package")
def agdc_file_with_temperature(resource_path_root):
    return resource_path_root / "temperature" / "CPW1C48210013_baseline.agdc"


@pytest.fixture(scope="package")
def agdc_temperature(agdc_file_with_temperature):
    with FileReader(agdc_file_with_temperature) as reader:
        df = reader.temperature_to_pandas()
    return df


@pytest.fixture(scope="package")
def agdc_temperature_cal(agdc_file_with_temperature):
    with FileReader(agdc_file_with_temperature) as reader:
        calibrated = CalibratedReader(reader)
        df = calibrated.temperature_to_pandas()
    return df


@pytest.fixture
def agdc_file_temperature_acc_cal(resource_path_root):
    file = (
        resource_path_root
        / "temperature"
        / "Csv_Calibrated"
        / "CPW1C48210013_baseline_acceleration_calibrated.csv"
    )
    return pd.read_csv(file)


@pytest.fixture
def agdc_file_temperature_adxl(resource_path_root):
    file = (
        resource_path_root
        / "temperature"
        / "Csv_ADC"
        / "CPW1C48210013_baseline_temperature_ADXL_ADC.csv"
    )
    return pd.read_csv(file)


@pytest.fixture
def agdc_file_temperature_mcu(resource_path_root):
    file = (
        resource_path_root
        / "temperature"
        / "Csv_ADC"
        / "CPW1C48210013_baseline_temperature_MCU_ADC.csv"
    )
    return pd.read_csv(file)


@pytest.fixture
def agdc_file_temperature_adxl_cal(resource_path_root):
    file = (
        resource_path_root
        / "temperature"
        / "Csv_Calibrated"
        / "CPW1C48210013_baseline_temperature_ADXL_calibrated.csv"
    )
    return pd.read_csv(file)


@pytest.fixture
def agdc_file_temperature_mcu_cal(resource_path_root):
    file = (
        resource_path_root
        / "temperature"
        / "Csv_Calibrated"
        / "CPW1C48210013_baseline_temperature_MCU_calibrated.csv"
    )
    return pd.read_csv(file)


@pytest.fixture
def v1_file(resource_path_root):
    return resource_path_root / "neo.gt3x"


@pytest.fixture
def v1_gt(resource_path_root):
    return resource_path_root / "neo.csv"


@pytest.fixture
def calibrated_csv_file(resource_path_root):
    return resource_path_root / "WRIST_rawCalibrated_032Hz.csv"


@pytest.fixture
def ism_enabled_file(resource_path_root):
    return resource_path_root / "ISM_Enabled.gt3x"


@pytest.fixture
def ism_disabled_file(resource_path_root):
    return resource_path_root / "ISM_Disabled.gt3x"


@pytest.fixture
def calibrated_dataframe(calibrated_csv_file):
    return pd.read_csv(calibrated_csv_file, header=10)


@pytest.fixture
def wrist_csv_file(resource_path_root):
    return resource_path_root / "WRIST_rawLSB_032Hz.csv"


@pytest.fixture
def wrist_dataframe(wrist_csv_file):
    return pd.read_csv(wrist_csv_file, header=10)
