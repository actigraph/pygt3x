import gt3x.Gt3xHeader
import gt3x.Gt3xRawEvent

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
        headerBytes = self.source.read(8)
        if len(headerBytes) != 8:
            return None
        header = gt3x.Gt3xHeader(headerBytes)
        payloadBytes = self.source.read(header.payload_size)
        if len(payloadBytes) != header.payload_size:
            return None
        checksum = self.source.read(1)
        if not checksum:
            return None
        raw_event = gt3x.Gt3xRawEvent(header, payloadBytes, checksum)
        return raw_event