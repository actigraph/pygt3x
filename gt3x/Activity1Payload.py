from gt3x.BitPackAcceleration import BitPackAcceleration


class Activity1Payload:
    """
    Class for Activity 1 Payload
    """

    def __init__(self, payload_bytes, timestamp):
        self.AccelerationSamples = \
            BitPackAcceleration.unpack_activity(
                payload_bytes, timestamp, True)
