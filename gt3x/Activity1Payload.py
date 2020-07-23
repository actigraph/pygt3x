import gt3x.BitPackAcceleration


class Activity1Payload:
    """
    Class for Activity 1 Payload
    """

    def __init__(self, payload_bytes, timestamp):
        self.AccelerationSamples = gt3x.BitPackAcceleration.unpack_activity(payload_bytes, timestamp, True)
