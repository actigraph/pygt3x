import struct

__all__ = ['Gt3xHeader']

class Gt3xHeader:
    """
    Class for Gt3xHeader
    
    Attributes:
        separator (byte): Log separator value
        timestamp (long): Unix epoch timestamp in seconds
        eventType (byte): GT3X event type
        payload_size (int): Event payload size in bytes

    """
    separator = 0
    timestamp = 0
    eventType = 0
    payload_size = 0
    
    def __init__(self, bytes):
        (separator, eventType, timestamp, payload_size) = struct.unpack("<BBLH", bytes)
        self.separator = separator
        self.timestamp = timestamp
        self.eventType = eventType
        self.payload_size = payload_size