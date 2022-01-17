from gt3x.Gt3xHeader import Gt3xHeader
from gt3x.Gt3xRawEvent import Gt3xRawEvent

__all__ = ['Gt3xLogReader']


class Gt3xLogReader:
    """
    Class to handle reading GT3X/AGDC log events
    """

    def __init__(self, source):
        """
        Constructor for Gt3xLogReader

        Parameters:
        source: IO stream for log.bin file data

        """
        self.source = source

    def read_event(self):
        header_bytes = self.source.read(8)
        if len(header_bytes) != 8:
            return None
        header = Gt3xHeader(header_bytes)
        payload_bytes = self.source.read(header.payload_size)
        if len(payload_bytes) != header.payload_size:
            return None
        checksum = self.source.read(1)
        if not checksum:
            return None
        raw_event = Gt3xRawEvent(header, payload_bytes, checksum)
        return raw_event
