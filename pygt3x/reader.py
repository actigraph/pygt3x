import io
import json
from zipfile import ZipFile

import numpy as np
import pandas as pd
from pygt3x.activity_payload import Activity1Payload
from pygt3x.activity_payload import Activity2Payload
from pygt3x.activity_payload import Activity3Payload
from pygt3x.componenets import Info, RawEvent, Header
from pygt3x.events import Types


class FileReader:
    """
    Class for Gt3x file reader

    Reads GT3X/AGDC files
    """

    def __init__(self, file_name):
        self.file_name = file_name

    def __enter__(self):
        self.zipfile = ZipFile(self.file_name)
        self.logfile = self.zipfile.open("log.bin", "r")
        self.logreader = LogReader(self.logfile)
        self.info = self.read_info()
        self.calibration = self.read_calibration()

        return self

    def __exit__(self, typ, value, traceback):
        self.logfile.__exit__(typ, value, traceback)
        self.zipfile.__exit__(typ, value, traceback)

    def read_info(self):
        """
        Parses info.txt and returns dictionary with key/value pairs
        """
        output = dict()
        with io.TextIOWrapper(
            self.zipfile.open("info.txt", "r"), encoding="utf-8-sig"
        ) as infoFile:
            for line in infoFile.readlines():
                values = line.split(":")
                if len(values) == 2:
                    output[values[0].strip()] = values[1].strip()

        return Info(output)

    def read_calibration(self):
        if "calibration.json" not in self.zipfile.namelist():
            return None
        with self.zipfile.open("calibration.json") as calibrationFile:
            calibration = json.load(calibrationFile)
            return calibration

    def read_events(self, num_rows=None):
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
        for evt in self.read_events(num_rows):
            if Types(evt.header.eventType) == Types.Activity3:
                payload = Activity3Payload(evt.payload, evt.header.timestamp)
            elif Types(evt.header.eventType) == Types.Activity2:
                payload = Activity2Payload(evt.payload, evt.header.timestamp)
            elif Types(evt.header.eventType) == Types.Activity:
                payload = Activity1Payload(evt.payload, evt.header.timestamp)
            else:
                continue

            yield payload.AccelerationSamples

    def to_pandas(self):
        """
        Returns acceleration data as pandas data frame
        """
        col_names = ["Timestamp", "X", "Y", "Z"]
        data = np.concatenate(list(self.get_acceleration()))
        df = pd.DataFrame(data, columns=col_names)
        df.index = df["Timestamp"]
        del df["Timestamp"]
        return df


class LogReader:
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
        header = Header(header_bytes)
        payload_bytes = self.source.read(header.payload_size)
        if len(payload_bytes) != header.payload_size:
            return None
        checksum = self.source.read(1)
        if not checksum:
            return None
        raw_event = RawEvent(header, payload_bytes, checksum)
        return raw_event
