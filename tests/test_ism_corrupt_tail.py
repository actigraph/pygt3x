from functools import reduce
from operator import xor
import struct
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest

from pygt3x.reader import FileReader


START = 1600000000


def _record(event_type, second, payload, corrupt=False):
    header = struct.pack("<BBIH", 0x1E, event_type, START + second, len(payload))
    checksum = reduce(xor, header + payload, 0) ^ 0xFF
    if corrupt:
        checksum ^= 1
    return header + payload + bytes([checksum])


def _read(tmp_path, sample_rate, tail):
    params = _record(21, 0, bytes([0, 0, 2, 0, 4, 0, 0, 0]))
    activity = _record(26, 0, struct.pack("<hhh", 10, 20, 30) * sample_rate)
    sleep = _record(3, 1, b"\x08")
    battery = _record(2, 5, struct.pack("<H", 3700))
    path = tmp_path / "synthetic.gt3x"
    with ZipFile(path, "w") as archive:
        archive.writestr(
            "info.txt", f"Sample Rate: {sample_rate}\nAcceleration Scale: 1\n"
        )
        archive.writestr("log.bin", params + activity + sleep + battery + tail)
    with FileReader(str(path)) as reader:
        return reader.to_pandas(calibrate=False)


@pytest.mark.parametrize("sample_rate", [30, 100])
@pytest.mark.parametrize("second", [3, 9])
@pytest.mark.parametrize("repeat", [1, 2])
def test_bad_checksum_tail_preserves_sleep_boundary(
    tmp_path, sample_rate, second, repeat
):
    expected = _read(tmp_path, sample_rate, b"")
    assert len(expected) == 5 * sample_rate
    assert expected.IdleSleepMode.sum() == 4 * sample_rate
    np.testing.assert_allclose(
        expected.index, START + np.arange(5 * sample_rate) / sample_rate,
        rtol=0, atol=5e-7,
    )
    tail = _record(2, second, struct.pack("<H", 3700), corrupt=True) * repeat
    actual = _read(tmp_path, sample_rate, tail)
    pd.testing.assert_frame_equal(actual, expected)


@pytest.mark.parametrize("sample_rate", [30, 100])
@pytest.mark.parametrize("length", [4, 9, 10])
def test_incomplete_tail_preserves_sleep_boundary(tmp_path, sample_rate, length):
    expected = _read(tmp_path, sample_rate, b"")
    tail = _record(2, 9, struct.pack("<H", 3700))[:length]
    actual = _read(tmp_path, sample_rate, tail)
    pd.testing.assert_frame_equal(actual, expected)
