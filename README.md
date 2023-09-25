# Seis Extractor - command line and GUI versions
## Command line version
usage: ```python seisextractor <seg-y_folder> <well_coords.csv> <result.csv> <start_depth>```

The program reads the first SEG-Y file of the given folder and scans headers for inlines, crosslines, 
cdp_x and cdp_y. The bytes for now are 189, 193, 181 and 185 respectievly. There will be an opportunity
to set arbitrary bytes in future. Start depth is taken from byte 105. If it is not properly filled,
one can set it as last command line argument. 

Then it calculates mapping function from coordinates to inlines and crosslines.

Well coordinate file must have 4 columns. The first is well identifier, the rest are X, Y, Depth.

After well coordinates are read, the program iterates SEG-Y files and using RegularGridInterpolator, 
extracts values from the cubes to new pandas table. Finally the resulting file is saved as CSV table.


## GUI version

Does literally the same, but with ability to interactively choose SEG-Y folder and well coordinates file,
as well as check out its content. Made with PyQt5.

