class AccelerationSample:
    """
    Acceleration Sample Model

    """

    def __init__(self, timestamp, x, y, z):
        self.timestamp=timestamp
        self.x=x
        self.y=y
        self.z=z
    
    def __str__(self):
        return f"timestamp: {self.timestamp}, X: {self.x}, Y: {self.y}, Z: {self.z}"