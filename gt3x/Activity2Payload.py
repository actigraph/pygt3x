import gt3x.AccelerationSample
import io

class Activity2Payload:
    """
    Class for Activity 2 Payload
    """

    def unpack_activity2(self, payloadBytes, timestamp):
        stream = io.BytesIO(payloadBytes)
        sample = [0,0,0]
        
        for _ in range(0, int(len(payloadBytes)/6)):
            for axis in range(0,3):
                b = stream.read(2)
                sample[axis] = int.from_bytes(b, byteorder='little', signed=True)
                yield gt3x.AccelerationSample(timestamp, sample[0], sample[1], sample[2])

    def __init__(self, payloadBytes, timestamp):
        self.AccelerationSamples = self.unpack_activity2(payloadBytes, timestamp)