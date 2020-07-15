import gt3x.BitPackAcceleration

class Activity3Payload:
    """
    Class for Activity 3 Payload
    """

    def __init__(self, payloadBytes, timestamp):
        self.AccelerationSamples = gt3x.BitPackAcceleration.unpack_activity(payloadBytes, timestamp, False)

    
