import io

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
        stream = io.BytesIO(payload_bytes)
        sample = [0, 0, 0]

        for _ in range(0, int(len(payload_bytes) / 6)):
            for axis in range(0, 3):
                b = stream.read(2)
                sample[axis] = int.from_bytes(b, byteorder="little", signed=True)
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
