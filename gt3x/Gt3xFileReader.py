import io
from zipfile import ZipFile
import gt3x.Gt3xLogReader
import gt3x.Activity3Payload
import pandas as pd

__all__ = ['Gt3xFileReader']

class Gt3xFileReader:
    """
    Class for Gt3x file reader
    
    Reads GT3X/AGDC files
    """

    def __init__(self, file_name):
        self.file_name = file_name
    
    def __enter__(self):
        self.zipfile = ZipFile(self.file_name)
        self.logfile = self.zipfile.open("log.bin", "r")
        self.logreader = gt3x.Gt3xLogReader(self.logfile)
        return self
        
    def __exit__(self, type, value, traceback):
        self.logfile.__exit__(type, value, traceback)
        self.zipfile.__exit__(type, value, traceback)

    def read_info(self):
        """
        Parses info.txt and returns dictionary with key/value pairs
        """
        output = dict()
        with io.TextIOWrapper(self.zipfile.open("info.txt", "r"), encoding="utf-8-sig") as infoFile:
            for line in infoFile.readlines():
                values = line.split(':')
                if len(values)==2:
                    output[values[0].strip()] = values[1].strip()
        return output
                    
        
    def read_events(self, num_rows=None):
        if num_rows is None:
            raw_event = self.logreader.read_event()
            while raw_event is not None:
                yield raw_event
                raw_event = self.logreader.read_event()
        else:    
            for _ in range(0,num_rows):
                raw_event = self.logreader.read_event()
                yield raw_event
    
    def get_acceleration(self):
        for evt in self.read_events():
            payload = gt3x.Activity3Payload(evt.payload, evt.header.timestamp)
            for sample in payload.AccelerationSamples:
                yield sample

     
    def to_pandas(self):
        """
        Returns acceleration data as pandas data frame
        """
        col_names = ['Timestamp','X','Y','Z']
        data = self.get_acceleration()
        df = pd.DataFrame(data, columns=col_names) 
        df.index = df["Timestamp"]
        del df["Timestamp"]
        return df