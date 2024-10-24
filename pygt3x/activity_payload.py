"""Binary payload parsing."""

import struct

import numpy as np

NHANES_SCALE = 341


def unpack_bitpack_acceleration(source: bytes):
    """
    Unpack activity stored as sets of 3, 12-bit integers.

    In GT3x files, data is packed as 12 bit numbers. Each sample contains 36 bits. In
    order to read this data, we proceed by packs of 3 bytes, which will give us 24 bits,
    corresponding to two numbers (out of 3).

    This works well is there are an even number of sample, because we can divide them
    into three axes (2*36=72, which can be divided by 3). Otherwise, the last 12 bits
    are unaccounted for. To avoid this issue, if we cannot divide bytes into 3, we pad
    the data with zeros.

    Parameters:
    -----------
    source:
        Activity payload bytes array

    Returns:
    --------
    Generator which produces acceleration samples as Int16 values

    """
    data = np.frombuffer(source, dtype=np.uint8)
    if (data.shape[0] % 3) == 1:
        data = np.pad(data, (0, 2), "constant")
    fst_uint8, mid_uint8, lst_uint8 = (
        np.reshape(data, (data.shape[0] // 3, 3)).astype(np.uint16).T
    )
    fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
    snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
    concat = np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1)
    try:
        data = concat.reshape((-1, 3))
    except ValueError:
        data = concat.reshape((-1))[:-1].reshape((-1, 3))
    data[data > 2047] = data[data > 2047] + 61440

    return data.astype(np.int16)


def unpack_bitpack_temperature(source: bytes):
    """
    Unpack temperature stored as sets of 3 bytes.

    Parameters:
    -----------
    source:
        Temperature payload bytes array

    Returns:
    --------
    Temperature samples as Int16 values

    """
    data = np.empty((1, 2))
    for i in range(len(source) // 3):
        sensor = source[i * 3]
        if sensor == 0:
            (value,) = struct.unpack("<H", source[i * 3 + 1 : (i + 1) * 3])
        else:
            assert sensor == 1
            (value,) = struct.unpack("<h", source[i * 3 + 1 : (i + 1) * 3])
        data[0, sensor] = value
    return data


def read_nhanes_payload(source, start_date: int, sample_rate: float):
    """
    Handle reading NHANES GT3x data.

    Parameters:
    -----------
    source:
        IO stream for activity.bin file data
    start_data:
        Start date (in nS)
    sample_rate:
        Sampling rate
    """
    payload_bytes = source.read()
    data = np.round(
        unpack_bitpack_acceleration(payload_bytes) / NHANES_SCALE, 3
    ).reshape((-1, 3))
    data = data[:, [1, 0, 2]]
    time = ((np.ones(data.shape[0]).cumsum() - 1) / sample_rate) + start_date / 1e9
    return np.concatenate(
        (time.reshape((-1, 1)), data, np.zeros((data.shape[0], 1))), axis=1
    )


def read_activity1_payload(payload_bytes: bytes, timestamp: int, sample_rate: float):
    """
    Parse Activity 1 Payloads.

    Parameters:
    -----------
    payload_bytes:
        Data bytes
    timestamp:
        Event timestamp
    """
    data = unpack_bitpack_acceleration(payload_bytes)
    time = ((np.ones(data.shape[0]).cumsum() - 1) / sample_rate) + timestamp
    data = np.concatenate(
        (time.reshape((-1, 1)), data, np.zeros((data.shape[0], 1))), axis=1
    )
    data = data[:, [0, 2, 1, 3, 4]]
    return data


def read_activity2_payload(payload_bytes, timestamp, sample_rate):
    """Read Activity 2 Payload.

    Parameters:
    -----------
    payload_bytes:
        Data bytes
    timestamp:
        Event timestamp
    """
    if (len(payload_bytes) % 6) != 0:
        payload_bytes = payload_bytes[: -(len(payload_bytes) % 6) + 1]
    data = np.frombuffer(payload_bytes, dtype=np.int16).reshape((-1, 3))
    time = ((np.ones(data.shape[0]).cumsum() - 1) / sample_rate) + timestamp
    data = np.concatenate(
        (time.reshape(-1, 1), data, np.zeros((data.shape[0], 1))), axis=1
    )
    return data.reshape((-1, 5))


def read_activity3_payload(payload_bytes, timestamp, sample_rate):
    """Parse Activity 3 Payload.

    Parameters:
    -----------
    payload_bytes:
        Data bytes
    timestamp:
        Event timestamp
    """
    data = unpack_bitpack_acceleration(payload_bytes)
    time = ((np.ones(data.shape[0]).cumsum() - 1) / sample_rate) + timestamp
    data = np.concatenate(
        (time.reshape(-1, 1), data, np.zeros((data.shape[0], 1))), axis=1
    )
    return data


def read_temperature_payload(payload_bytes, timestamp):
    """Parse Temperature Payload.

    Parameters:
    -----------
    payload_bytes:
        Data bytes
    timestamp:
        Event timestamp
    """
    data = unpack_bitpack_temperature(payload_bytes)
    data = np.concatenate(
        (np.array(timestamp).repeat(len(data)).reshape(-1, 1), data), axis=1
    )
    return data
