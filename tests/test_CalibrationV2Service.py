from gt3x.CalibrationV2Service import CalibrationV2Service
from gt3x.AccelerationSample import AccelerationSample

test_calibration = {
    "positiveZeroGOffsetX_32": 256,
    "positiveZeroGOffsetY_32": 256,
    "positiveZeroGOffsetZ_32": 256,
    "negativeZeroGOffsetX_32": -256,
    "negativeZeroGOffsetY_32": -256,
    "negativeZeroGOffsetZ_32": -256,
    "zeroGOffsetX_32": 0,
    "zeroGOffsetY_32": 0,
    "zeroGOffsetZ_32": 0,
    "offsetX_32": 37,
    "offsetY_32": 13,
    "offsetZ_32": 46,
    "sensitivityXX_32": 24804,
    "sensitivityYY_32": 26621,
    "sensitivityZZ_32": 24304,
    "sensitivityXY_32": -615,
    "sensitivityXZ_32": -222,
    "sensitivityYZ_32": -28
}


def test_calibrate_32hz(calibrated_dataframe, wrist_dataframe):
    service = CalibrationV2Service(test_calibration, 32)
    baseline_df = calibrated_dataframe
    baseline_samples = list(
        [AccelerationSample(
            index, row["Accelerometer X"],
            row["Accelerometer Y"], row["Accelerometer Z"]) for
            index, row in baseline_df.iterrows()])
    input_df = wrist_dataframe
    input_samples = [
        AccelerationSample(
            index, row["Accelerometer X"],
            row["Accelerometer Y"], row["Accelerometer Z"]) for
        index, row in input_df.iterrows()]
    output_samples = list(service.calibrate_samples(input_samples))

    baseline_epsilon = 1e-14

    for i in range(0, len(baseline_samples)):
        comparison = abs(output_samples[i] - baseline_samples[i])
        assert comparison.x < baseline_epsilon
        assert comparison.y < baseline_epsilon
        assert comparison.z < baseline_epsilon
