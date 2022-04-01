import struct

from pygt3x.bit_pack_acceleration import BitPackAcceleration
from pygt3x.componenets import AccelerationSample


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
        for sample in struct.iter_unpack("<hhh", payload_bytes):
            yield AccelerationSample(timestamp, sample[0], sample[1], sample[2])

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
