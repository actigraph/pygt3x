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
        header = gt3x.Gt3xHeader(self.source.read(8))
        raw_event = gt3x.Gt3xRawEvent(header, self.source.read(header.payload_size), self.source.read(1))
        return raw_event