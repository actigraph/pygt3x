"""Binary payload parsing."""
import numpy as np
from pygt3x.bit_pack_acceleration import BitPackAcceleration


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
