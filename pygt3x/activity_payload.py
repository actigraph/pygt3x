import numpy as np
from pygt3x.bit_pack_acceleration import BitPackAcceleration


class Activity1Payload:
    """
    Class for Activity 1 Payload
    """

    def __init__(self, payload_bytes, timestamp):
        self.AccelerationSamples = BitPackAcceleration.unpack_activity(
            payload_bytes, timestamp, True
        )


class Activity2Payload:
    """Class for Activity 2 Payload."""

    @staticmethod
    def unpack_activity2(payload_bytes, timestamp):
        if (len(payload_bytes) % 6) != 0:
            payload_bytes = payload_bytes[: -(len(payload_bytes) % 6) + 1]
        data = np.frombuffer(payload_bytes, dtype=np.int16).reshape((-1, 3))
        data = np.concatenate(
            (np.array(timestamp).repeat(len(data)).reshape(-1, 1), data), axis=1
        )
        return data.reshape((-1, 4))

    def __init__(self, payload_bytes, timestamp):
        self.AccelerationSamples = self.unpack_activity2(payload_bytes, timestamp)


class Activity3Payload:
    """
    Class for Activity 3 Payload
    """

    def __init__(self, payload_bytes, timestamp):
        self.AccelerationSamples = BitPackAcceleration.unpack_activity(
            payload_bytes, timestamp, False
        )
