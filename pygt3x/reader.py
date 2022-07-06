"""Read data from files."""

import json
from zipfile import ZipFile

import numpy as np
import pandas as pd

from pygt3x import Types
from pygt3x.activity_payload import (
    Activity1Payload,
    Activity2Payload,
    Activity3Payload,
    NHANESPayload,
)
from pygt3x.components import Header, Info, RawEvent


class FileReader:
    """Read GT3X/AGDC files.

    Parameters:
    -----------
    file_name:
        Input file name
    """

    def __init__(self, file_name: str):
        """Initialise."""
        self.file_name = file_name

    def __enter__(self):
        """Open zipped file and ret up readers."""
        self.zipfile = ZipFile(self.file_name)
        try:
            self.logfile = self.zipfile.open("log.bin", "r")
            self.logreader = LogReader(self.logfile)
        except KeyError:
            # V1 file
            self.logreader = None
            self.logfile = self.zipfile.open("log.txt", "r")
            self.activity_file = self.zipfile.open("activity.bin", "r")
        self.info = Info(self.zipfile)
        self.calibration = self.read_calibration()

        return self

    def __exit__(self, typ, value, traceback):
        """Close file descriptors."""
        self.logfile.__exit__(typ, value, traceback)
        self.zipfile.__exit__(typ, value, traceback)

    def read_calibration(self):
        """Read calibration info from file."""
        if "calibration.json" not in self.zipfile.namelist():
            return None
        with self.zipfile.open("calibration.json") as f:
            calibration = json.load(f)
            return calibration

    def read_events(self, num_rows=None):
        """Read events from file.

        Parameters:
        -----------
        num_rows
            Number of events to read.
        """
        if num_rows is None:
            raw_event = self.logreader.read_event()
            while raw_event is not None:
                yield raw_event
                raw_event = self.logreader.read_event()
        else:
            for _ in range(0, num_rows):
                raw_event = self.logreader.read_event()
                yield raw_event

    def get_acceleration(self, num_rows=None):
        """Yield acceleration data.

        Parameters:
        -----------
        num_rows
            Number of events to read.
        """
        if self.logreader:
            for evt in self.read_events(num_rows):
                # An 'Activity' (id: 0x00) log record type with a 1-byte payload is
                # captured on a USB connection event (and does not represent a reading
                # from the activity monitor's accelerometer). This event is captured
                # upon docking the activity monitor (via USB) to a PC or CentrePoint
                # Data Hub (CDH) device. Therefore, such records cannot be parsed as the
                # traditional activity log records and can be ignored.
                if (
                    Types(evt.header.event_type) == Types.Activity
                    and evt.header.payload_size == 1
                ):
                    continue

                if Types(evt.header.event_type) == Types.Activity3:
                    payload = Activity3Payload(evt.payload, evt.header.timestamp)
                elif Types(evt.header.event_type) == Types.Activity2:
                    payload = Activity2Payload(evt.payload, evt.header.timestamp)
                elif Types(evt.header.event_type) == Types.Activity:
                    payload = Activity1Payload(evt.payload, evt.header.timestamp)
                else:
                    continue
                yield payload.AccelerationSamples
        else:
            payload = NHANESPayload(
                self.activity_file,
                self.info.start_date,
                self.info.sample_rate,
            )
            yield payload.AccelerationSamples

    def to_pandas(self):
        """Return acceleration data as pandas data frame."""
        col_names = ["Timestamp", "X", "Y", "Z"]
        data = np.concatenate(list(self.get_acceleration()))
        df = pd.DataFrame(data, columns=col_names)
        df.set_index("Timestamp", drop=True, inplace=True)
        return df


class LogReader:
    """
    Handle reading GT3X/AGDC log events.

    Parameters:
        -----------
            source: IO stream for log.bin file data
    """

    def __init__(self, source):
        """Initialise reader."""
        self.source = source

    def read_event(self):
        """Parse an event."""
        header_bytes = self.source.read(8)
        if len(header_bytes) != 8:
            return None
        header = Header(header_bytes)
        payload_bytes = self.source.read(header.payload_size)
        if len(payload_bytes) != header.payload_size:
            return None
        checksum = self.source.read(1)
        if not checksum:
            return None
        raw_event = RawEvent(header, payload_bytes, checksum)
        return raw_event
