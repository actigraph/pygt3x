"""Read data from files."""

import json
import logging
from zipfile import ZipFile

from collections import Counter

import numpy as np
import pandas as pd

from pygt3x import Types
from pygt3x.activity_payload import (
    read_activity1_payload,
    read_activity2_payload,
    read_activity3_payload,
    read_nhanse_payload,
    read_temperature_payload,
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
        self.acceleration = np.empty((0, 4))
        self.temperature = np.empty((0, 3))

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
        self.info = Info.read_zip(self.zipfile)
        self.calibration = self.read_json("calibration.json")
        self.temperature_calibration = self.read_json("temperature_calibration.json")

        return self

    def __exit__(self, typ, value, traceback):
        """Close file descriptors."""
        self.logfile.__exit__(typ, value, traceback)
        self.zipfile.__exit__(typ, value, traceback)

    def read_json(self, file_name):
        """Read calibration info from file."""
        if file_name not in self.zipfile.namelist():
            return None
        with self.zipfile.open(file_name) as f:
            calibration = json.load(f)
            return calibration

    def _fill_ism(self, idle_sleep_mode_started, idle_sleep_mode_ended, last_values):
        """Fill in gaps created by idle sleep mode."""
        timestamps = (
            np.arange(idle_sleep_mode_started, idle_sleep_mode_ended)
            .repeat(self.info.sample_rate)
            .reshape(-1, 1)
        )
        values = last_values.reshape((1, 3)).repeat(timestamps.shape[0], axis=0)

        result = np.concatenate((timestamps, values), axis=1).reshape((-1, 30, 4))
        return result

    def _validate_payload(self, payload):
        shape = payload.shape
        expected_shape = (self.info.sample_rate, 4)
        if shape[1:] != expected_shape and shape != expected_shape:
            logging.warning(f"Unexpected payload shape {shape}")
        return payload

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

    def _get_data_nhanse(self):
        """Yield NHANSE acceleration data."""
        payload = read_nhanse_payload(
            self.activity_file,
            self.info.start_date,
            self.info.sample_rate,
        )
        return [payload], []

    def _get_data_default(self, num_rows=None):
        """Yield acceleration data.

        Parameters:
        -----------
        num_rows
            Number of events to read.
        """
        acceleration = []
        temperature = []
        idle_sleep_mode_started = None
        # This is used for filling in gaps created by idle sleep mode
        last_values = None
        last_idsm_ts = 0
        for evt in self.read_events(num_rows):
            try:
                type = Types(evt.header.event_type)
            except ValueError:
                logging.warning(f"Unsupported event type {evt.header.event_type}")
                continue

            # dt is time delta w.r.t. last valid acceleration datapoint
            try:
                last_second = acceleration[-1][0, 0]
            except IndexError:
                dt = 0
            else:
                dt = evt.header.timestamp - last_second

            # Time travel dt is relative to last event,
            # no matter whether it had valid data
            # or was e.g. ISM start/end
            time_travel_dt = last_idsm_ts - evt.header.timestamp
            if time_travel_dt > 0:
                logging.debug(
                    f"{evt.header.timestamp} --> {dt} time drift by {time_travel_dt}s"
                )

            # Idle sleep mode is encoded as an event with payload 8 when entering
            # and 09 when leaving.
            if type == Types.Event and evt.payload == b"\x08":
                last_idsm_ts = evt.header.timestamp
                dt_idm = dt
                if dt >= 2:
                    ts = pd.to_datetime(evt.header.timestamp, unit="s")
                    logging.debug(f"Missed {dt}s before {ts}")

                if idle_sleep_mode_started is not None:
                    logging.warning(
                        f"Idle sleep mode was already active at"
                        f" {idle_sleep_mode_started}"
                    )
                idle_sleep_mode_started = evt.header.timestamp
                continue
            if type == Types.Event and evt.payload == b"\x09":
                if idle_sleep_mode_started is not None and last_values is not None:
                    last_idsm_ts = evt.header.timestamp
                    # Fill in missing data for dt past payloads
                    fill_start = idle_sleep_mode_started - (dt_idm - 1)

                    payload = self._validate_payload(
                        self._fill_ism(fill_start, evt.header.timestamp, last_values)
                    )
                    idle_sleep_mode_started = None
                    acceleration.extend(payload)
                    continue
                else:
                    logging.warning(
                        f"Idle sleep mode was not active at {evt.header.timestamp}"
                    )
                    continue

            # An 'Activity' (id: 0x00) log record type with a 1-byte payload is
            # captured on a USB connection event (and does not represent a reading
            # from the activity monitor's accelerometer). This event is captured
            # upon docking the activity monitor (via USB) to a PC or CentrePoint
            # Data Hub (CDH) device. Therefore, such records cannot be parsed as the
            # traditional activity log records and can be ignored.
            if type in [Types.Activity, Types.Activity3]:
                if evt.header.payload_size == 1:
                    continue

            if type == Types.Activity3:
                payload = read_activity3_payload(evt.payload, evt.header.timestamp)
            elif type == Types.Activity2:
                payload = read_activity2_payload(evt.payload, evt.header.timestamp)
            elif type == Types.Activity:
                payload = read_activity1_payload(evt.payload, evt.header.timestamp)
            elif type == Types.TemperatureRecord:
                temperature.append(
                    read_temperature_payload(evt.payload, evt.header.timestamp)
                )
                continue
            else:
                continue
            if payload.shape[0] > 0:
                last_values = payload[-1, 1:]
                # Without the next line, if we miss an ISM stop event, we would
                # think we are in ISM even when receiving accelerometer data.
                idle_sleep_mode_started = None
            if payload.shape[0] != 0:
                if time_travel_dt > 0:
                    logging.debug(
                        f"{evt.header.timestamp}>{dt} time drift by {time_travel_dt}s"
                    )
                    logging.debug(f"Last valid second: {acceleration[-1][0, 0]}")
                    assert dt == 0, f"Expected dt=0 for time travelling, but dt={dt}"
                    acceleration[-1 - dt] = self._validate_payload(payload)
                else:
                    acceleration.append(self._validate_payload(payload))

        if idle_sleep_mode_started is not None:
            # Idle sleep mode was started but not finished before the recording
            # ended. This means that we might be missing some records at the end of
            # the file.
            idle_sleep_mode_ended = evt.header.timestamp
            payload = self._validate_payload(
                self._fill_ism(
                    idle_sleep_mode_started - (dt_idm - 1),
                    idle_sleep_mode_ended,
                    last_values,
                )
            )
            acceleration.extend(payload)
        logging.debug(f"last ts {evt.header.timestamp}")
        return acceleration, temperature

    def get_data(self, num_rows=None):
        """Yield acceleration data.

        Parameters:
        -----------
        num_rows
            Number of events to read.
        """
        if not self.logreader:
            acceleration, temperature = self._get_data_nhanse()
        else:
            acceleration, temperature = self._get_data_default(num_rows=num_rows)

        if len(acceleration) > 0:
            self.acceleration = np.concatenate(acceleration)
        if len(temperature) > 0:
            self.temperature = np.concatenate(temperature)

        # Make sure each second appears sample rate times
        counter = Counter(self.acceleration[:, 0].astype(int))
        wrong_freq_cases = [c for c in counter.values() if c != self.info.sample_rate]
        if len(wrong_freq_cases) > 0:
            logging.warning(f"Wrong freq cases: {wrong_freq_cases}")

    def to_pandas(self):
        """Return acceleration data as pandas data frame."""
        col_names = ["Timestamp", "X", "Y", "Z"]
        if len(self.acceleration) == 0:
            self.get_data()
        df = pd.DataFrame(self.acceleration, columns=col_names)
        df.set_index("Timestamp", drop=True, inplace=True)
        return df

    def temperature_to_pandas(self):
        """Return temperature data as pandas data frame."""
        col_names = ["Timestamp", "TemperatureMCU", "TemperatureADXL"]
        if len(self.temperature) == 0:
            assert len(self.acceleration) == 0
            self.get_data()
        df = pd.DataFrame(self.temperature, columns=col_names)
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
        try:
            raw_event = RawEvent(header, payload_bytes, checksum)
        except ValueError:
            return None
        return raw_event
