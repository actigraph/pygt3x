import gt3x.BitPackAcceleration

class Activity1Payload:
    """
    Class for Activity 1 Payload
    """

    def __init__(self, payloadBytes, timestamp):
        self.AccelerationSamples = gt3x.BitPackAcceleration.unpack_activity(payloadBytes, timestamp, True)

    
