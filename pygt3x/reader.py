"""Read data from files."""

import json
import logging
from collections import Counter
from typing import Optional
from zipfile import ZipFile

import numpy as np
import pandas as pd

from pygt3x import Types
from pygt3x.activity_payload import (
    read_activity1_payload,
    read_activity2_payload,
    read_activity3_payload,
    read_nhanes_payload,
    read_temperature_payload,
)
from pygt3x.calibration import CalibrationV2Service
from pygt3x.components import Header, Info, RawEvent

logger = logging.getLogger(__name__)


class FileReader:
    """Read GT3X/AGDC files.

    Parameters:
    -----------
    file_name:
        Input file name
    """

    def __init__(self, file_name: str, num_rows: Optional[int] = None):
        """Initialise."""
        self.file_name = file_name
        self.acceleration = np.empty((0, 4))
        self.temperature = np.empty((0, 3))
        self.idle_sleep_mode_activated = None
        self.num_rows = num_rows
        self.nhanes = None

    def __enter__(self):
        """Open zipped file and ret up readers."""
        self.zipfile = ZipFile(self.file_name)
        try:
            self.logfile = self.zipfile.open("log.bin", "r")
            self.logreader = LogReader(self.logfile)
            self.nhanes = False
        except KeyError:
            # V1 file
            self.logreader = None
            self.logfile = self.zipfile.open("log.txt", "r")
            self.activity_file = self.zipfile.open("activity.bin", "r")
            self.nhanes = True
        self.info = Info.read_zip(self.zipfile)
        self.calibration = self.read_json("calibration.json")
        self.temperature_calibration = self.read_json("temperature_calibration.json")
        self._get_data(self.num_rows)
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
        add = np.tile(
            ((np.ones((self.info.sample_rate, 1))).cumsum() - 1)
            / self.info.sample_rate,
            timestamps.shape[0] // self.info.sample_rate,
        )
        timestamps += add.reshape((-1, 1))
        values = last_values.reshape((1, 4)).repeat(timestamps.shape[0], axis=0)

        result = np.concatenate((timestamps, values), axis=1).reshape(
            (-1, self.info.sample_rate, 5), order="C"
        )
        result[:, :, 4] = 1
        return result

    def _validate_payload(self, payload):
        shape = payload.shape
        expected_shape = (self.info.sample_rate, 5)
        if shape[1:] != expected_shape and shape != expected_shape:
            logger.warning("Unexpected payload shape %s", shape)
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

    def _get_data_nhanes(self):
        """Yield NHANES acceleration data."""
        payload = read_nhanes_payload(
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
        # Initialize evt in case there are no events in the GT3x file
        evt = None
        for evt in self.read_events(num_rows):

            if not evt.is_checksum_valid:
                logger.warning(
                    "Event checksum does not match at %s .", evt.header.timestamp
                )
                continue

            try:
                type = Types(evt.header.event_type)
            except ValueError:
                logger.warning("Unsupported event type %s", evt.header.event_type)
                continue

            if type == Types.Params:
                params = np.frombuffer(evt.payload, dtype="<u8")
                for param in params:
                    buffer = param.tobytes()
                    address = np.frombuffer(buffer, dtype="<u1")
                    if address[2] == 0x02:
                        self.idle_sleep_mode_activated = (
                            np.bitwise_and(address[4], 4) == 4
                        )

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
                logger.debug(
                    "%s --> %s time drift by %s s",
                    evt.header.timestamp,
                    dt,
                    time_travel_dt,
                )

            # Idle sleep mode is encoded as an event with payload 8 when entering
            # and 09 when leaving.
            if type == Types.Event and evt.payload == b"\x08":
                if not self.idle_sleep_mode_activated:
                    logger.error(
                        "Found activation of idle sleep mode in the data, but idle "
                        "sleep mode was not activated in the device. This is probably a"
                        "bug in the parser."
                    )
                last_idsm_ts = evt.header.timestamp
                dt_idm = dt
                if dt >= 2:
                    ts = pd.to_datetime(evt.header.timestamp, unit="s")
                    logger.debug("Missed %s s before %s", dt, ts)

                if idle_sleep_mode_started is not None:
                    logger.warning(
                        "Idle sleep mode was already active at %s",
                        idle_sleep_mode_started,
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
                    logger.warning(
                        "Idle sleep mode was not active at %s", evt.header.timestamp
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
                payload = read_activity3_payload(
                    evt.payload, evt.header.timestamp, self.info.sample_rate
                )
            elif type == Types.Activity2:
                payload = read_activity2_payload(
                    evt.payload, evt.header.timestamp, self.info.sample_rate
                )
            elif type == Types.Activity:
                payload = read_activity1_payload(
                    evt.payload, evt.header.timestamp, self.info.sample_rate
                )
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
                    logger.debug(
                        "%s>%s time drift by %s s",
                        evt.header.timestamp,
                        dt,
                        time_travel_dt,
                    )
                    logger.debug("Last valid second: %s", acceleration[-1][0, 0])
                    acceleration[-1 + int(dt)] = self._validate_payload(payload)
                else:
                    acceleration.append(self._validate_payload(payload))

        if idle_sleep_mode_started is not None:
            # Idle sleep mode was started but not finished before the recording
            # ended. This means that we might be missing some records at the end of
            # the file.
            assert evt is not None
            idle_sleep_mode_ended = evt.header.timestamp
            payload = self._validate_payload(
                self._fill_ism(
                    idle_sleep_mode_started - (dt_idm - 1),
                    idle_sleep_mode_ended,
                    last_values,
                )
            )
            acceleration.extend(payload)
        if evt is not None:
            logger.debug("last ts %s", evt.header.timestamp)
        return acceleration, temperature

    def _get_data(self, num_rows=None):
        """Yield acceleration data.

        Parameters:
        -----------
        num_rows
            Number of events to read.
        """
        if not self.logreader:
            acceleration, temperature = self._get_data_nhanes()
        else:
            acceleration, temperature = self._get_data_default(num_rows=num_rows)

        # Check for and remove identical samples
        if len(acceleration) > 1:
            assert len(acceleration[0].shape) == 2
            acceleration, counts = np.unique(acceleration, axis=0, return_counts=True)
            duplicates_removed = acceleration[counts > 1]
            if duplicates_removed.size > 0:
                logger.warning(
                    "%s duplicate accelerometer records removed.",
                    duplicates_removed.shape[0],
                )
                for d in duplicates_removed:
                    logger.debug(
                        "Duplicate accelerometer record removed: %s", d.tolist()
                    )

        if len(acceleration) > 0:
            self.acceleration = np.concatenate(acceleration)
        if len(temperature) > 0:
            self.temperature = np.concatenate(temperature)

        # Make sure each second appears sample rate times
        counter = Counter(self.acceleration[:, 0].astype(int))
        wrong_freq_cases = [
            (k, v) for k, v in counter.items() if v != self.info.sample_rate
        ]
        for w in wrong_freq_cases:
            logger.warning(
                "Timestamp (second) %s has %s samples instead of %s.",
                w[0],
                w[1],
                self.info.sample_rate,
            )

    def calibrate_acceleration(self, acceleration):
        """Calibrates acceleration samples."""
        calibration = self.calibration
        info = self.info

        if (
            calibration is None
            or ("isCalibrated" not in calibration)
            or calibration["isCalibrated"]
        ):
            # Data is already calibrated, so just return unscaled values
            accel_scale = info.acceleration_scale
            calibrated_acceleration = acceleration / accel_scale
        elif calibration["calibrationMethod"] == 2:
            # Use calibration method 2 to calibrate activity
            sample_rate = info.sample_rate
            calibration_service = CalibrationV2Service(calibration, sample_rate)
            calibrated_acceleration = calibration_service.calibrate_samples(
                acceleration
            )
        else:
            raise NotImplementedError(
                f"Unknown calibration method: " f"{calibration['calibrationMethod']}"
            )
        return calibrated_acceleration

    def calibrate_temperature(self):
        """Calibrates acceleration samples."""
        calibration = self.temperature_calibration
        temperature = self.temperature

        if calibration is None or calibration["isCalibrated"]:
            # Data is already calibrated, so just return
            calibrated_temperature = temperature
        elif calibration["calibrationMethod"] == 1:
            # Use calibration method 1 to calibrate temperature
            calibrated_temperature = temperature
            adxl_temp = temperature[:, 2]
            adxl_gain = (calibration["tempHigh"] - calibration["tempLow"]) / (
                calibration["adxlTempHigh"] - calibration["adxlTempLow"]
            )
            adxl_temp = (
                adxl_temp - calibration["adxlTempLow"]
            ) * adxl_gain + calibration["tempLow"]
            calibrated_temperature[:, 2] = adxl_temp
            mcu_temp = temperature[:, 1]
            mcu_gain = (calibration["tempHigh"] - calibration["tempLow"]) / (
                calibration["mcuTempHigh"] - calibration["mcuTempLow"]
            )
            mcu_temp = (mcu_temp - calibration["mcuTempLow"]) * mcu_gain + calibration[
                "tempLow"
            ]
            calibrated_temperature[:, 1] = mcu_temp

        else:
            raise NotImplementedError(
                f"Unknown calibration method: " f"{calibration['calibrationMethod']}"
            )
        return calibrated_temperature

    def to_pandas(self, calibrate: bool = True):
        """Return acceleration data as pandas data frame."""
        col_names = ["Timestamp", "X", "Y", "Z", "IdleSleepMode"]
        df = pd.DataFrame(self.acceleration, columns=col_names)
        if calibrate and not self.nhanes:
            df[["X", "Y", "Z"]] = self.calibrate_acceleration(
                df[["X", "Y", "Z"]].values
            )
        df.IdleSleepMode = df.IdleSleepMode == 1
        df.set_index("Timestamp", drop=True, inplace=True)
        df = df.apply(lambda x: pd.to_numeric(x, downcast="float"))  # type: ignore
        df.sort_index(kind="stable", inplace=True)
        return df

    def temperature_to_pandas(self, calibrate: bool = True):
        """Return temperature data as pandas data frame."""
        col_names = ["Timestamp", "TemperatureMCU", "TemperatureADXL"]
        if calibrate:
            data = self.calibrate_temperature()
        else:
            data = self.temperature
        df = pd.DataFrame(data, columns=col_names)
        df.set_index("Timestamp", drop=True, inplace=True)
        df = df.apply(lambda x: pd.to_numeric(x, downcast="float"))  # type: ignore
        df.sort_index(kind="stable", inplace=True)
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
