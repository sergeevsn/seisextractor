import sys
sys.path.append("..")
from common.classeslib import *

GREETING_MSG = 'SeisExtractor v. 0.4: cmd tool for extracting seismic data from multiple SEG-Y files along wells with given X, Y, Z coordinates'

PARAM_KEYS = {'SEIS_FOLDER', 'WELL_TABLE', 'COLUMNS', 'RESULT_TABLE', 'START_DEPTH', 'BIN_AVERAGING', 'EXPANSION'}

def read_params(fname):
    try:
        with open(fname) as f:
            lines = f.readlines()
    except:
        print(f'ERROR: Cannot open file {fname}!')
        sys.exit()
                
    param_keys_raw = [line.strip().split('=')[0] for line in lines]
    param_values_raw = [line.strip().split('=')[1] for line in lines]
    param_keys = [p.strip() for p in param_keys_raw]
    param_values = [p.strip() for p in param_values_raw]
   

    if set(param_keys) != set(PARAM_KEYS):
        print(f'ERROR: Wrong parameters in file {fname}!')
        
        sys.exit()

    return  {k: v for k, v in zip(param_keys, param_values)}


if __name__ == "__main__":    

    print(GREETING_MSG)
    if len(sys.argv) < 2:
        print('ERROR: You must provide a parameters file!')
        sys.exit()

    params = read_params(sys.argv[1])       

    extractor = Extractor(True)    
    print('Scanning seismic folder...')
    if not extractor.scan_seismic_folder(params['SEIS_FOLDER']):
        sys.exit()    

    # if columns specified
    columns_str = params['COLUMNS']
    column_names = columns_str.split(',')
    if len(column_names) != 4:
        print('ERROR: you must specify 4 column names for Well, X, Y and Depth, delimited by comma!')
        sys.exit()

    try:
        start_depth = int(params['START_DEPTH'])
    except:
        print('ERROR: Wrong START_DEPTH parameter!')
        sys.exit()
    extractor.recalc_depth(start_depth)   

    print(f'Starting depth is {start_depth}')

    if not params['BIN_AVERAGING'] in ['true', 'false', 'True', 'False']:
        print('ERROR: Wrong BIN_AVERAGING parameter!')
        sys.exit()

    if params['BIN_AVERAGING'] in ['true', 'True']:
        bin_averaging = True
    else:
        bin_averaging = False    
    print(f'Setting  Bin Averaging to {bin_averaging}')

    try:
        expansion = int(params['EXPANSION'])
    except:
        print('ERROR: Wrong EXPANSION parameter!')
        sys.exit()    
            
        
    print('Loading well coordinates table...')
    if not extractor.load_table(params['WELL_TABLE']):
        sys.exit()

    if not extractor.set_columns_by_name(*column_names):
        sys.exit()

    print('Calculating well grid coordinates...')

    # meters to samples
    expansion = int(np.round(expansion/extractor.bin_size)) 
    if not extractor.calc_well_grid_coords(bin_averaging, expansion):
        sys.exit()       

    print('Extracting seismic data...')
    for fname in extractor.filenames:
        if not extractor.extract_attribute(fname):
            sys.exit()

    if not extractor.save_result_table(params['RESULT_TABLE']):
        sys.exit()      

