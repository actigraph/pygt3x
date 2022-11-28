"""GT3x header structure."""
import io
import logging
import struct
from dataclasses import InitVar, dataclass

import numpy as np
from typing import Optional, Union


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
    age: Optional[float]
    battery_voltage: float
    board_revision: Optional[str]
    device_type: Optional[str]
    dominance: Optional[str]
    download_date: Optional[int]
    firmware: Optional[str]
    height: Optional[float]
    last_sample_time: int
    limb: Optional[str]
    mass: Optional[float]
    race: Optional[str]
    sample_rate: int
    serial_numer: Optional[str]
    sex: Optional[str]
    side: Optional[str]
    start_date: int
    stop_date: int
    subject_name: Optional[str]
    timezone: Optional[str]
    unexpected_resets: Union[str, int]

    @staticmethod
    def read_zip(zip_file):
        """Parse info.txt and returns an Info object."""
        output = dict()
        with io.TextIOWrapper(
            zip_file.open("info.txt", "r"), encoding="utf-8-sig"
        ) as f:
            for line in f.readlines():
                values = line.split(":")
                # The format of TimeZone is this: "TimeZone: -04:00:00"
                if len(values) == 2 or values[0] == "TimeZone":
                    output[values[0].strip()] = ":".join(values[1:]).strip()
        return Info(
            acceleration_max=float(output.get("Acceleration Max", 0)),
            acceleration_min=float(output.get("Acceleration Min", 0)),
            acceleration_scale=float(output.get("Acceleration Scale", 0)),
            age=float(output["Age"]) if "Age" in output else None,
            battery_voltage=float(output.get("Battery Voltage", "0").replace(",", ".")),
            board_revision=output.get("Board Revision", None),
            device_type=output.get("Device Type", None),
            dominance=output.get("Dominance", None),
            download_date=(
                int(output["Download Date"]) if "Download Date" in output else None
            ),
            firmware=output.get("Firmware", None),
            height=float(output["Height"]) if "Height" in output else None,
            last_sample_time=int(output.get("Last Sample Time", 0)),
            limb=output.get("Limb", None),
            mass=float(output["Mass"]) if "Mass" in output else None,
            race=output.get("Race", None),
            sample_rate=int(output.get("Sample Rate", 0)),
            serial_numer=output.get("Serial Number", None),
            sex=output.get("Sex", None),
            side=output.get("Side", None),
            start_date=int(output.get("Start Date", 0)),
            stop_date=int(output.get("Stop Date", 0)),
            subject_name=output.get("Subject Name", None),
            timezone=output.get("TimeZone", None),
            unexpected_resets=output.get("Unexpected Resets", 0),
        )
