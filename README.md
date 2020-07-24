# gt3x-py

Python module for reading GT3X/AGDC file format data

## Example Usage

```python
import gt3x

# Read raw data and calibrate
# Dump to pandas data frame
with gt3x.Gt3xFileReader("C:\\NovoUwfSteps\\UWF Steps Baselines 20200623\\WristBaselines\\RawLsb\\WRIST_rawLSB_032Hz.agdc") as gt3xReader:
    calibratedReader =  gt3x.Gt3xCalibratedReader(gt3xReader)
    df = calibratedReader.to_pandas()
    print(df.head(5))
```
