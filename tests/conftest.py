import pandas as pd
import pytest


@pytest.fixture
def gt3x_file(resource_path_root):
    return resource_path_root / "small.gt3x"


@pytest.fixture
def agdc_file(resource_path_root):
    return resource_path_root / "WRIST_rawLSB_032Hz_test.agdc"


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
def calibrated_dataframe(calibrated_csv_file):
    return pd.read_csv(calibrated_csv_file, header=10)


@pytest.fixture
def wrist_csv_file(resource_path_root):
    return resource_path_root / "WRIST_rawLSB_032Hz.csv"


@pytest.fixture
def wrist_dataframe(wrist_csv_file):
    return pd.read_csv(wrist_csv_file, header=10)
