from gt3x.BitPackAcceleration import BitPackAcceleration


class Activity3Payload:
    """
    Class for Activity 3 Payload
    """

    def __init__(self, payload_bytes, timestamp):
        self.AccelerationSamples = \
            BitPackAcceleration.unpack_activity(
                payload_bytes, timestamp, False)
