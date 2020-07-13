import gt3x.Gt3xFileReader
import gt3x.Gt3xRawEvent
import gt3x.AccelerationSample

class Gt3xCalibratedReader:
    """
    Calibrated event reader. Will calibrate activity events as they are read.
    """

    def __init__(self, source: gt3x.Gt3xFileReader):
        self.source = source
    
    def read_info(self):
        """
        Returns info dictionary from source reader
        """
        return self.source.read_info()

    def calibrate_acceleration(self, raw_event: gt3x.Gt3xRawEvent):
        """
        Calibrates acceleration samples.

        Parameters:
            raw_event (Gt3xRawEvent): Activity event to calibrate.

        """
        payload = gt3x.Activity3Payload(raw_event.payload, raw_event.header.timestamp)
        info = self.read_info()
        accelScale = float(info["Acceleration Scale"])
        raw_event.CalibratedAcceleration = [gt3x.AccelerationSample(raw_event.header.timestamp, x=sample.x/accelScale, y=sample.y/accelScale, z=sample.z/accelScale) for sample in payload.AccelerationSamples]

    def read_events(self, num_rows: int = None):
        """
        Read events from source and calibrates activity.

        Parameters:
            num_rows (int): Optionally limits number or rows to return.

        """
        for raw_event in self.source.read_events(num_rows):
            self.calibrate_acceleration(raw_event)
            yield raw_event
        