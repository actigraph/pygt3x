class Gt3xInfo(dict):
    
    def get_sample_rate(self):
        return int(self["Sample Rate"])
    
    def get_acceleration_scale(self):
        return float(self["Acceleration Scale"])