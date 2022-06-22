"""Class for unpacking activity."""
import numpy as np


class BitPackAcceleration:
    """Handle binary packed acceleration data."""

    @staticmethod
    def unpack(source: bytes):
        """
        Unpack activity stored as sets of 3, 12-bit integers.

        Parameters:
        -----------
        source:
            Activity payload bytes array

        Returns:
        --------
        Generator which produces acceleration samples as Int16 values

        """
        data = np.frombuffer(source, dtype=np.uint8)
        fst_uint8, mid_uint8, lst_uint8 = (
            np.reshape(data, (data.shape[0] // 3, 3)).astype(np.uint16).T
        )
        fst_uint12 = (fst_uint8 << 4) + (mid_uint8 >> 4)
        snd_uint12 = ((mid_uint8 % 16) << 8) + lst_uint8
        concat = np.concatenate((fst_uint12[:, None], snd_uint12[:, None]), axis=1)
        data = concat.reshape((-1, 3))
        data[data > 2047] = data[data > 2047] + 61440

        return data.astype(np.int16)
