"""GT3x header structure."""
import io
import struct
from dataclasses import dataclass


@dataclass
class Header:
    """
    GT3X Header.

    Attributes:
    -----------
    separator:
        Log separator value
    timestamp:
        Unix epoch timestamp in seconds
    eventType:
        GT3X event type
    payload_size:
        Event payload size in bytes
    """

    separator: bytes
    timestamp: int
    event_types: bytes
    payload_size: int

    def __init__(self, header_bytes: bytes):
        """Unpack header."""
        (separator, event_type, timestamp, payload_size) = struct.unpack(
            "<BBLH", header_bytes
        )
        self.separator = separator
        self.timestamp = timestamp
        self.event_type = event_type
        self.payload_size = payload_size


@dataclass(frozen=True)
class RawEvent:
    """
    Gt3xRawEvent class.

    Attributes:
    -----------
    header:
        Header object
    payload:
        Log event payload as byte array
    checksum:
        Log event checksum
    """

    header: Header
    payload: bytes
    checksum: bytes


@dataclass
class Info:
    """Metadata class."""

    start_date: int
    device_type: str
    acceleration_max: float
    sample_rate: int
    timezone: str
    subject_name: str
    battery_voltage: float
    download_date: int
    unexpected_resets: int
    last_sample_time: int
    acceleration_min: float
    acceleration_scale: float
    serial_numer: str
    limb: str
    board_revision: str
    stop_date: int
    firmware: str

    def __init__(self, zip_file):
        """Parse info.txt and returns dictionary with key/value pairs."""
        output = dict()
        with io.TextIOWrapper(
            zip_file.open("info.txt", "r"), encoding="utf-8-sig"
        ) as f:
            for line in f.readlines():
                values = line.split(":")
                # The format of TimeZone is this: "TimeZone: -04:00:00"
                if len(values) == 2 or values[0] == "TimeZone":
                    output[values[0].strip()] = ":".join(values[1:]).strip()
        self.start_date = int(output.get("Start Date", 0))
        self.device_type = output.get("Device Type", None)
        self.acceleration_max = float(output.get("Acceleration Max", 0))
        self.sample_rate = int(output.get("Sample Rate", 0))
        self.timezone = output.get("TimeZone", None)
        self.subject_name = output.get("Subject Name", None)
        self.battery_voltage = float(
            output.get("Battery Voltage", "0").replace(",", ".")
        )
        self.download_date = int(output.get("Download Date", 0))
        self.unexpected_resets = output.get("Unexpected Resets", 0)
        self.last_sample_time = int(output.get("Last Sample Time", 0))
        self.acceleration_min = float(output.get("Acceleration Min", 0))
        self.acceleration_scale = float(output.get("Acceleration Scale", 0))
        self.serial_numer = output.get("Serial Number", None)
        self.limb = output.get("Limb", None)
        self.board_revision = output.get("Board Revision", None)
        self.stop_date = int(output.get("Stop Date", 0))
        self.firmware = output.get("Firmware", None)
