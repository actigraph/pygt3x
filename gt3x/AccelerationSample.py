class AccelerationSample:
    """
    Acceleration Sample Model

    """

    def __init__(self, timestamp, x, y, z):
        self.timestamp = timestamp
        self.x = x
        self.y = y
        self.z = z
    
    def __str__(self):
        return f"Timestamp: {self.timestamp}, X: {self.x}, Y: {self.y}, Z: {self.z}"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.timestamp == other.timestamp and self.x == other.x and self.y == other.y and self.z == other.z
        else:
            return False

    def __sub__(self, other):
        return AccelerationSample(self.timestamp, self.x-other.x, self.y-other.y, self.z-other.z)

    def __abs__(self):
        return AccelerationSample(self.timestamp, abs(self.x), abs(self.y), abs(self.z))
