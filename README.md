# Seis Extractor - command line and GUI versions
### Extracting seismic data from a set of seismic cubes in SEG-Y format 
### along the given well coordinates for future machine learning purposes

## Command line version
usage: ```python seisextractor <params_file>```

params_file must have keys:

```SEIS_FOLDER``` - folder with seismic cubes to read data from

```WELL_TABLE``` - a table with well coordinates. It must have columns for well id, X and Y coords and depth (TVD)
Can be either *.csv or *.xlsx file.

```COLUMNS``` - names of columns, corresponding to well id, X, Y coords and depth (TVD). Names separated by comma

```START_DEPTH``` - depth corresponding to zero in SEG-Y files

```BIN_AVERAGING```
If ```bin_averaging``` is ```true```, then well coordinates are averaged according to seismic bin 
(unique inline, xline, sample), else well samples stays with its original coordinates and 
seismic data is sampled usign linear interpolation via scipy.interpolate.RegularGridInterpolator. 
Actually this interpolator is used anyway, but in case of bin_averaging seismic data is sampled 
from exact grid points.

```EXPANSION```
Data expansion radius. Works only if ```bin_averaging``` is true. Adds neighbouring inlines and xlines, falling in the 
area of give expansion radius for current well sample. Set in meters, then the program recalculates it 
to number of inlines/xlines.

The program reads the first SEG-Y file of the given folder and scans headers for inlines, crosslines, 
cdp_x and cdp_y. The bytes for now are 189, 193, 181 and 185 respectievly. There will be an opportunity
to set arbitrary bytes in future. 

Then it calculates mapping function from coordinates to inlines and crosslines.

After well coordinates are read, the program iterates SEG-Y files and using RegularGridInterpolator, 
extracts values from the cubes to new pandas table. Finally the resulting file is saved as CSV table.

Download repository and run on test data:
```git clone https://github.com/sergeevsn/seisextractor.git```

```pip install -r requirements.txt```

```cd cmd```

```python seisextractor.py ../test_data/params.txt```


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

