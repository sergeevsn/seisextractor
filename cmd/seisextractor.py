import sys
sys.path.append("..")
from common.classeslib import *

GREETING_MSG = 'SeisExtractor v. 0.2: cmd tool for extracting seismic data from multiple SEG-Y files along wells with given X, Y, Z coordinates'

if __name__ == "__main__":    

    print(GREETING_MSG)
    if len(sys.argv) < 5:
        print('ERROR: You must provide a SEG-Y folder path, well coordinates table, columns for coordinates and results file name!')
        sys.exit()

    extractor = Extractor(True)    
    print('Scanning seismic folder...')
    if not extractor.scan_seismic_folder(sys.argv[1]):
        sys.exit()
    new_depth = 0    

    # if columns specified
    columns_str = sys.argv[3]
    column_names = columns_str.split(',')
    if len(column_names) != 3:
        print('ERROR: you must specify 3 column names for X, Y and Depth, delimited by comma!')
        sys.exit()

    if len(sys.argv) == 6:
        try:
            new_depth = int(sys.argv[5])
        except:
            print('Starting depth must be a number!')      
            sys.exit()
    extractor.recalc_depth(new_depth)
    print('Loading well coordinates table...')
    if not extractor.load_table(sys.argv[2]):
        sys.exit()

    if not extractor.set_coord_columns_by_name(*column_names):
        sys.exit()

    print('Calculating well grid coordinates...')
    if not extractor.calc_well_grid_coords():
        sys.exit()       

    print('Extracting seismic data...')
    for fname in extractor.filenames:
        if not extractor.extract_attribute(fname):
            sys.exit()

    if not extractor.save_result_table(sys.argv[4]):
        sys.exit()

    print(f'Extraction data from folder {sys.argv[1]} using coordinates from table {sys.argv[2]} is complete. Resulting table {sys.argv[3]} is saved.')            
