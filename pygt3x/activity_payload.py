"""Binary payload parsing."""
import numpy as np


class BitPackAcceleration:
    """Handle binary packed acceleration data."""

    @staticmethod
    def unpack(source: bytes):
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


class NHANESPayload:
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

    SCALE = 341

    def __init__(self, source, start_date: int, sample_rate: float):
        """Read payload."""
        payload_bytes = source.read()
        data = np.round(
            BitPackAcceleration.unpack(payload_bytes) / NHANESPayload.SCALE, 3
        ).reshape((-1, 3))
        data = data[:, [1, 0, 2]]
        time = ((np.ones(data.shape[0]).cumsum() - 1) / sample_rate) + start_date / 1e9
        self.AccelerationSamples = np.concatenate((time.reshape((-1, 1)), data), axis=1)


class Activity1Payload:
    """Class for Parsing Activity 1 Payloads.

    Parameters:
    -----------
    payload_bytes:
        Data bytes
    timestamp:
        Event timestamp
    """

    def __init__(self, payload_bytes: bytes, timestamp: int):
        """Parse payload."""
        data = BitPackAcceleration.unpack(payload_bytes)

        data = np.concatenate(
            (np.array(timestamp).repeat(len(data)).reshape(-1, 1), data), axis=1
        )
        data = data[:, [0, 2, 1, 3]]
        self.AccelerationSamples = data


class Activity2Payload:
    """Class for Activity 2 Payload.

    Parameters:
    -----------
    payload_bytes:
        Data bytes
    timestamp:
        Event timestamp
    """

    def __init__(self, payload_bytes, timestamp):
        """Parse payload."""
        if (len(payload_bytes) % 6) != 0:
            payload_bytes = payload_bytes[: -(len(payload_bytes) % 6) + 1]
        data = np.frombuffer(payload_bytes, dtype=np.int16).reshape((-1, 3))
        data = np.concatenate(
            (np.array(timestamp).repeat(len(data)).reshape(-1, 1), data), axis=1
        )
        self.AccelerationSamples = data.reshape((-1, 4))


class Activity3Payload:
    """
    Parse Activity 3 Payload.

    Parameters:
    -----------
    payload_bytes:
        Data bytes
    timestamp:
        Event timestamp
    """

    def __init__(self, payload_bytes, timestamp):
        """Parse payload."""
        data = BitPackAcceleration.unpack(payload_bytes)
        data = np.concatenate(
            (np.array(timestamp).repeat(len(data)).reshape(-1, 1), data), axis=1
        )
        self.AccelerationSamples = data
