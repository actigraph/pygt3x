import gt3x.Gt3xHeader

__all__ = ['Gt3xRawEvent']

class Gt3xRawEvent:
    """
    Class for Gt3xRawEvent

    Attributes:
        header: Gt3xHeader
        payload (byte array): Log event payload as byte array
        checksum (byte): Log event checksum
        
    """

    def __init__(self, header: gt3x.Gt3xHeader, payload, checksum):
        self.header = header
        self.payload = payload
        self.checksum = checksum