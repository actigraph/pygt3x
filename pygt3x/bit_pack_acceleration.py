"""Class for unpacking activity."""
import numpy as np


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
        data = np.frombuffer(source, dtype=np.uint8)
        fst_uint8, mid_uint8, lst_uint8 = (
            np.reshape(data, (data.shape[0] // 3, 3)).astype(np.int16).T
        )
        fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
        snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
        concat = np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1)
        data = concat.reshape((-1, 3))
        data[data > 2047] = data[data > 2047] - 4095
        data = np.concatenate(
            (np.array(timestamp).repeat(len(data)).reshape(-1, 1), data), axis=1
        )
        if flip_xy:
            data = data[:, [1, 0, 2]]
        return data
