"""GT3x header structure."""
import io
import logging
import struct
from dataclasses import InitVar, dataclass

import numpy as np


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
    checksum: InitVar[bytes]

    def __post_init__(self, checksum: bytes):
        """Verify event's checksum."""
        new_checksum = self.header.separator ^ self.header.event_type
        timestamp = self.header.timestamp.to_bytes(4, "little")
        new_checksum = np.bitwise_xor.reduce(
            np.frombuffer(timestamp, dtype=np.uint8), initial=new_checksum
        )
        payload_size = self.header.payload_size.to_bytes(4, "little")
        new_checksum = np.bitwise_xor.reduce(
            np.frombuffer(payload_size, dtype=np.uint8), initial=new_checksum
        )
        new_checksum = np.bitwise_xor.reduce(
            np.frombuffer(self.payload, dtype=np.uint8), initial=new_checksum
        )
        new_checksum = int(~new_checksum & 0xFF)
        if new_checksum.to_bytes(1, "little") != checksum:
            logging.warning(f"Corrupted event at {self.header.timestamp}.")
            raise ValueError("Event checksum does not match.")


@dataclass
class Info:
    """Metadata class."""

    acceleration_max: float
    acceleration_min: float
    acceleration_scale: float
    age: float
    battery_voltage: float
    board_revision: str
    device_type: str
    dominance: str
    download_date: int
    firmware: str
    height: float
    last_sample_time: int
    limb: str
    mass: float
    race: str
    sample_rate: int
    serial_numer: str
    sex: str
    side: str
    start_date: int
    stop_date: int
    subject_name: str
    timezone: str
    unexpected_resets: int

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
        self.acceleration_max = float(output.get("Acceleration Max", 0))
        self.acceleration_min = float(output.get("Acceleration Min", 0))
        self.acceleration_scale = float(output.get("Acceleration Scale", 0))
        self.age = float(output["Age"]) if "Age" in output else None
        self.battery_voltage = float(
            output.get("Battery Voltage", "0").replace(",", ".")
        )
        self.board_revision = output.get("Board Revision", None)
        self.device_type = output.get("Device Type", None)
        self.dominance = output.get("Dominance", None)
        self.download_date = (
            int(output["Download Date"]) if "Download Date" in output else None
        )
        self.firmware = output.get("Firmware", None)
        self.height = float(output["Height"]) if "Height" in output else None
        self.last_sample_time = int(output.get("Last Sample Time", 0))
        self.limb = output.get("Limb", None)
        self.mass = float(output["Mass"]) if "Mass" in output else None
        self.race = output.get("Race", None)
        self.sample_rate = int(output.get("Sample Rate", 0))
        self.serial_numer = output.get("Serial Number", None)
        self.sex = output.get("Sex", None)
        self.side = output.get("Side", None)
        self.start_date = int(output.get("Start Date", 0))
        self.stop_date = int(output.get("Stop Date", 0))
        self.subject_name = output.get("Subject Name", None)
        self.timezone = output.get("TimeZone", None)
        self.unexpected_resets = output.get("Unexpected Resets", 0)
