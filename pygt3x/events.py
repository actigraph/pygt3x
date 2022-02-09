from enum import Enum, unique


@unique
class Types(Enum):
    Activity = 0
    AntPlus = 1
    Battery = 2
    Event = 3
    HeartRateBpm = 4
    Lux = 5
    MetaData = 6
    Tag = 7
    Temperature = 8
    Epoch = 9
    DailySummary = 10
    HeartRateAnt = 11
    Epoch2 = 12
    Capsense = 13
    HeartRateBle = 14
    Epoch3 = 15
    Epoch4 = 16
    Imu9dof = 17
    Magnetometer = 18
    FifoError = 19
    FifoDump = 20
    Params = 21
    ImuAccelerometer = 22
    Debug = 23
    SensorSchema = 24
    SensorData = 25
    Activity2 = 26
    Activity3 = 27
    LongPress = 28
    ButtonEvent = 29
