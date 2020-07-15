import gt3x.Gt3xFileReader
import gt3x.Gt3xRawEvent
import gt3x.AccelerationSample
import gt3x.Gt3xEventTypes
import numpy as np

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
    
    def read_calibration(self):
        return self.source.read_calibration()

    def calibrate_acceleration(self, raw_event: gt3x.Gt3xRawEvent):
        """
        Calibrates acceleration samples.

        Parameters:
            raw_event (Gt3xRawEvent): Activity event to calibrate.

        """
        if gt3x.Gt3xEventTypes(raw_event.header.eventType) == gt3x.Gt3xEventTypes.Activity3:
            payload = gt3x.Activity3Payload(raw_event.payload, raw_event.header.timestamp)
        else:
            payload = gt3x.Activity2Payload(raw_event.payload, raw_event.header.timestamp)

        calibration = self.source.read_calibration()
        info = self.read_info()

        if calibration is None or calibration['isCalibrated'] == True:
            accelScale = info.get_acceleration_scale()
            raw_event.CalibratedAcceleration = [gt3x.AccelerationSample(raw_event.header.timestamp, x=sample.x/accelScale, y=sample.y/accelScale, z=sample.z/accelScale) for sample in payload.AccelerationSamples]
        else:
            sampleRate = info.get_sample_rate()
            raw_event.CalibratedAcceleration = self.calibrate_v2(payload.AccelerationSamples, calibration, sampleRate)

    def calibrate_v2(self, samples, calibration: dict, sampleRate: int):
        offsetX = float(calibration[f'offsetX_{sampleRate}'])
        offsetY = float(calibration[f'offsetY_{sampleRate}'])
        offsetZ = float(calibration[f'offsetZ_{sampleRate}'])

        sensitivityXX = float(calibration[f'sensitivityXX_{sampleRate}'])
        sensitivityYY = float(calibration[f'sensitivityYY_{sampleRate}'])
        sensitivityZZ = float(calibration[f'sensitivityZZ_{sampleRate}'])

        sensitivityXY = float(calibration[f'sensitivityXY_{sampleRate}'])
        sensitivityXZ = float(calibration[f'sensitivityXZ_{sampleRate}'])
        sensitivityYZ = float(calibration[f'sensitivityYZ_{sampleRate}'])

        s11 = (sensitivityXX * 0.01) ** -1.0
        s12 = ((sensitivityXY * 0.01 + 250) ** -1.0) - 0.004
        s13 = ((sensitivityXZ * 0.01 + 250) ** -1.0) - 0.004

        s21 = ((sensitivityXY * 0.01 + 250) ** -1.0) - 0.004
        s22 = (sensitivityYY * 0.01) ** -1.0
        s23 = ((sensitivityYZ * 0.01 + 250) ** -1.0) - 0.004


        s31 = ((sensitivityXZ * 0.01 + 250) ** -1.0) - 0.004
        s32 = ((sensitivityYZ * 0.01 + 250) ** -1.0) - 0.004
        s33 = (sensitivityZZ * 0.01) ** -1.0


        O = np.array([[offsetX, offsetY, offsetZ]])
        S = np.array([[s11,s21,s31],[s12,s22,s32],[s13,s23,s33]])
        
        for sample in samples:
            calibratedSample = np.matmul(S, (np.array([[sample.x,sample.y,sample.z]]) - O).transpose()).transpose()
            yield gt3x.AccelerationSample(sample.timestamp, calibratedSample[0][0], calibratedSample[0][1], calibratedSample[0][2])

    def read_events(self, num_rows: int = None):
        """
        Read events from source and calibrates activity.

        Parameters:
            num_rows (int): Optionally limits number or rows to return.

        """
        for raw_event in self.source.read_events(num_rows):
            if not gt3x.Gt3xEventTypes(raw_event.header.eventType) in [gt3x.Gt3xEventTypes.Activity, gt3x.Gt3xEventTypes.Activity2, gt3x.Gt3xEventTypes.Activity3]:
                continue
            self.calibrate_acceleration(raw_event)
            yield raw_event
        