"""GT3x header structure."""
import struct


class Gt3xHeader:
    """
    Class for Gt3xHeader

    Attributes:
        separator (byte): Log separator value
        timestamp (long): Unix epoch timestamp in seconds
        eventType (byte): GT3X event type
        payload_size (int): Event payload size in bytes

    """

    def __init__(self, header_bytes: bytes):
        (separator,
         eventType,
         timestamp,
         payload_size) = struct.unpack("<BBLH", header_bytes)
        self.separator = separator
        self.timestamp = timestamp
        self.eventType = eventType
        self.payload_size = payload_size
