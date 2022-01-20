from typing import List

from gt3x.AccelerationSample import AccelerationSample
from gt3x.Gt3xHeader import Gt3xHeader


class Gt3xRawEvent:
    """
    Class for Gt3xRawEvent

    Attributes:
        header: Gt3xHeader
        payload (byte array): Log event payload as byte array
        checksum (byte): Log event checksum

        CalibratedAcceleration: AccelerationSample
    """
    CalibratedAcceleration: List[AccelerationSample] = []

    def __init__(self, header: Gt3xHeader, payload, checksum):
        self.header = header
        self.payload = payload
        self.checksum = checksum
