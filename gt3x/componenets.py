"""GT3x header structure."""
import struct
from typing import List


class AccelerationSample:
    """
    Acceleration Sample Model

    """

    def __init__(self, timestamp: int, x: float, y: float, z: float):
        self.timestamp = timestamp
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"Timestamp: {self.timestamp}, X: {self.x}," f" Y: {self.y}, Z: {self.z}"

    def __iter__(self):
        return iter([self.timestamp, self.x, self.y, self.z])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.timestamp == other.timestamp
                and self.x == other.x
                and self.y == other.y
                and self.z == other.z
            )
        else:
            return False

    def __sub__(self, other):
        return AccelerationSample(
            self.timestamp, self.x - other.x, self.y - other.y, self.z - other.z
        )

    def __abs__(self):
        return AccelerationSample(self.timestamp, abs(self.x), abs(self.y), abs(self.z))


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

    calibrated_acceleration: List[AccelerationSample] = []

    def __init__(self, header: Header, payload, checksum):
        self.header = header
        self.payload = payload
        self.checksum = checksum


class Info(dict):
    def get_sample_rate(self):
        return int(self["Sample Rate"])

    def get_acceleration_scale(self):
        return float(self["Acceleration Scale"])
