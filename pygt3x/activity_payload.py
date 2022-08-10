"""Binary payload parsing."""
import numpy as np


NHANSE_SCALE = 341


def unpack_bitpack_acceleration(source: bytes):
    """
    Unpack activity stored as sets of 3, 12-bit integers.

    Parameters:
    -----------
    source:
        Activity payload bytes array

    Returns:
    --------
    Generator which produces acceleration samples as Int16 values

    """
    data = np.frombuffer(source, dtype=np.uint8)
    fst_uint8, mid_uint8, lst_uint8 = (
        np.reshape(data, (data.shape[0] // 3, 3)).astype(np.uint16).T
    )
    fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
    snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
    concat = np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1)
    data = concat.reshape((-1, 3))
    data[data > 2047] = data[data > 2047] + 61440

    return data.astype(np.int16)


def read_nhanse_payload(source, start_date: int, sample_rate: float):
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
        unpack_bitpack_acceleration(payload_bytes) / NHANSE_SCALE, 3
    ).reshape((-1, 3))
    data = data[:, [1, 0, 2]]
    time = ((np.ones(data.shape[0]).cumsum() - 1) / sample_rate) + start_date / 1e9
    return np.concatenate((time.reshape((-1, 1)), data), axis=1)


def read_activity1_payload(payload_bytes: bytes, timestamp: int):
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

    data = np.concatenate(
        (np.array(timestamp).repeat(len(data)).reshape(-1, 1), data), axis=1
    )
    data = data[:, [0, 2, 1, 3]]
    return data


def read_activity2_payload(payload_bytes, timestamp):
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
    data = np.concatenate(
        (np.array(timestamp).repeat(len(data)).reshape(-1, 1), data), axis=1
    )
    return data.reshape((-1, 4))


def read_activity3_payload(payload_bytes, timestamp):
    """Parse Activity 3 Payload.

    Parameters:
    -----------
    payload_bytes:
        Data bytes
    timestamp:
        Event timestamp
    """
    data = unpack_bitpack_acceleration(payload_bytes)
    data = np.concatenate(
        (np.array(timestamp).repeat(len(data)).reshape(-1, 1), data), axis=1
    )
    return data
