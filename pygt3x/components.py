"""GT3x header structure."""
import struct


class Header:
    """
    GT3X Header.

    Attributes:
        separator (byte): Log separator value
        timestamp (long): Unix epoch timestamp in seconds
        eventType (byte): GT3X event type
        payload_size (int): Event payload size in bytes

    """

    def __init__(self, header_bytes: bytes):
        """Unpack header."""
        (separator, eventType, timestamp, payload_size) = struct.unpack(
            "<BBLH", header_bytes
        )
        self.separator = separator
        self.timestamp = timestamp
        self.eventType = eventType
        self.payload_size = payload_size


class RawEvent:
    """
    Gt3xRawEvent class.

    Parameters:
        header: Gt3xHeader
        payload: Log event payload as byte array
        checksum: Log event checksum

    Attributes:
        calibrated_acceleration: List[AccelerationSample]
    """

    calibrated_acceleration = None

    def __init__(self, header: Header, payload: bytes, checksum: bytes):
        """Initialise fields."""
        self.header = header
        self.payload = payload
        self.checksum = checksum


class Info(dict):
    """Metadata class."""

    def get_sample_rate(self):
        """Get sample rate.

        Returns:
        --------
        File sample rate.
        """
        return int(self["Sample Rate"])

    def get_acceleration_scale(self):
        """Get acceleration scale.

        Returns:
        --------
        Acceleration scale.
        """
        return float(self["Acceleration Scale"])
