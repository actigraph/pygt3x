"""GT3x header structure."""
import struct


class Header:
    """
    Class for Gt3xHeader

    Attributes:
        separator (byte): Log separator value
        timestamp (long): Unix epoch timestamp in seconds
        eventType (byte): GT3X event type
        payload_size (int): Event payload size in bytes

    """

    def __init__(self, header_bytes: bytes):
        (separator, eventType, timestamp, payload_size) = struct.unpack(
            "<BBLH", header_bytes
        )
        self.separator = separator
        self.timestamp = timestamp
        self.eventType = eventType
        self.payload_size = payload_size


class RawEvent:
    """
    Class for Gt3xRawEvent

    Parameters:
        header: Gt3xHeader
        payload (byte array): Log event payload as byte array
        checksum (byte): Log event checksum

    Attributes:
        calibrated_acceleration: List[AccelerationSample]
    """

    calibrated_acceleration = None

    def __init__(self, header: Header, payload, checksum):
        self.header = header
        self.payload = payload
        self.checksum = checksum


class Info(dict):
    def get_sample_rate(self):
        return int(self["Sample Rate"])

    def get_acceleration_scale(self):
        return float(self["Acceleration Scale"])
