# Seis Extractor - command line and GUI versions
## Command line version
usage: ```python seisextractor <seg-y_folder> <well_coords_table> <coord_columns> <result_table> <bin_averaging> <start_depth>```

```bin_averaging``` and ```start_depth``` are optional parameters and are provided as true/false and a number.
They can go in any order.
By default bin_averaging is false and start_depth is equal to the value from SEG-Y trace headers.

The program reads the first SEG-Y file of the given folder and scans headers for inlines, crosslines, 
cdp_x and cdp_y. The bytes for now are 189, 193, 181 and 185 respectievly. There will be an opportunity
to set arbitrary bytes in future. Start depth is taken from byte 105. If it is not properly filled,
one can set it as last command line argument. 

Then it calculates mapping function from coordinates to inlines and crosslines.

Well coordinate file must have at least 3 columns. In command line argument #3 column names corresponding 
to X coordinate, Y coordinate and Depth are specified separated by comma. The file can be CSV table with 
comma separator (.csv) or Excel table (.xlsx)

If ```bin_averaging``` is ```true```, then well coordinates are averaged according to seismic bin 
(unique inline, xline, sample), else well samples stays with its original coordinates and 
seismic data is sampled usign linear interpolation via scipy.interpolate.RegularGridInterpolator. 
Actually this interpolator is used anyway, but in case of bin_averaging seismic data is sampled 
from exact grid points.


After well coordinates are read, the program iterates SEG-Y files and using RegularGridInterpolator, 
extracts values from the cubes to new pandas table. Finally the resulting file is saved as CSV table.

Download repository and run on test data:
```git clone https://github.com/sergeevsn/seisextractor.git```

```pip install -r requirements.txt```

```cd cmd```

```python seisextractor.py ../test_data ../test_data/well_coords.csv x,y,TVD results.csv 2170 true```


## GUI version

Does literally the same, but with ability to interactively choose SEG-Y folder and well coordinates file,
as well as check out its content. Made with PyQt5.

You can edit START DEPTH value right inside table after scanning SEG-Y headers

To run with test data, just type in terminal:

```cd gui```

```python main.py```

Choose the ```test_data``` folder in ```SEISMIC``` section, then click ```Scan```.
Choose file ```test_data/well_coords.csv``` in ```WELLS``` section, then clicl ```Scan```
Then choose columns: "x" for X Coordinate, "y" for Y coordinate and "TVD" for Depth.

Finally, click ```Extract``` and choose the file to save results in, either CSV or Excel.

