"""Class for unpacking activity."""
from pygt3x.componenets import AccelerationSample


class BitPackAcceleration:
    @staticmethod
    def unpack_activity(source, timestamp: int, flip_xy: bool):
        """
        Unpacks activity stored as sets of 3, 12-bit integers

        Parameters:
        source (byte array): Activity payload bytes array
        flipXY (bool): If true sample is extracted in Y,X,Z order.
         Otherwise X,Y,Z order.

        Returns:
        Generator which produces acceleration samples as Int16 values

        """
        offset = 0
        index = -1
        sample = [0, 0, 0]

        def get_next_byte():
            nonlocal index
            index += 1
            if index == len(source):
                return None
            return source[index]

        current = 0
        while True:
            for axis in range(0, 3):
                if (offset & 0x7) == 0:
                    current = get_next_byte()
                    if current is None:
                        return

                    shifter = (current & 0xFF) << 4
                    offset += 8

                    current = get_next_byte()
                    if current is None:
                        return

                    shifter |= (current & 0xF0) >> 4
                    offset += 4
                else:
                    shifter = (current & 0x0F) << 8
                    offset += 4
                    current = get_next_byte()
                    if current is None:
                        return

                    shifter |= current & 0xFF
                    offset += 8

                if 0 != (shifter & 0x0800):
                    shifter |= 0xF000

                if shifter > 32767:
                    shifter -= 65535
                sample[axis] = shifter
            if flip_xy:
                yield AccelerationSample(
                    timestamp, x=sample[1], y=sample[0], z=sample[2]
                )
            else:
                yield AccelerationSample(
                    timestamp, x=sample[0], y=sample[1], z=sample[2]
                )
