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

    # if columns specified
    columns_str = sys.argv[3]
    column_names = columns_str.split(',')
    if len(column_names) != 3:
        print('ERROR: you must specify 3 column names for X, Y and Depth, delimited by comma!')
        sys.exit()

    start_depth_from_cmdline = 0
    bin_averaging_from_cmdline = False

    extra_params = []
    try:
        extra_params.append(sys.argv[5])
        extra_params.append(sys.argv[6])
    except:
        pass    

    print(extra_params)

    for param in extra_params:
        if param.isdigit():
            start_depth_from_cmdline = int(param)
            extractor.recalc_depth(start_depth_from_cmdline)
            print(f'recalculating depth with value {start_depth_from_cmdline}')
        elif param in ['true', 'false']:
            bin_averaging_from_cmdline = bool(param)
            print(f'Setting  Bin Averaging to {bin_averaging_from_cmdline}')
        else:
            print('ERROR: Unknown command line argument: {param}')       
        
    print('Loading well coordinates table...')
    if not extractor.load_table(sys.argv[2]):
        sys.exit()

    if not extractor.set_coord_columns_by_name(*column_names):
        sys.exit()

    print('Calculating well grid coordinates...')
    if not extractor.calc_well_grid_coords(bin_averaging_from_cmdline):
        sys.exit()       

    print('Extracting seismic data...')
    for fname in extractor.filenames:
        if not extractor.extract_attribute(fname):
            sys.exit()

    if not extractor.save_result_table(sys.argv[4]):
        sys.exit()

    print(f'Extraction data from folder {sys.argv[1]} using coordinates from table {sys.argv[2]} is complete. Resulting table {sys.argv[4]} is saved.')            
