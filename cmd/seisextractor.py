import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression
from scipy.interpolate import RegularGridInterpolator
import time

sys.path.append("..")
from common.utils import load_segy_coords, load_well_coords, load_cube


GREETING_MSG = 'SeisExtractor v. 0.1: cmd tool for extracting seismic data from multiple SEG-Y files along wells with given X, Y, Z coordinates'

if __name__ == "__main__":    

    print(GREETING_MSG)
    if len(sys.argv) < 4:
        print('You must provide a SEG-Y folder path!')
        os._exit(1)
    segy_foldername = Path(sys.argv[1])

    if not segy_foldername.exists() and segy_foldername.is_dir():
        print(f'Folder {segy_foldername} does not exist!')
        os._exit(1)
        
    segy_filenames = []    
    for fname in os.listdir(segy_foldername):
        if str(fname).endswith('.sgy'):
            
            segy_filenames.append(fname)

    if len(segy_filenames) == 0:
        print(f'Folder {segy_foldername} is empty!')
        os._exit(1)



    wellcoords_filename = Path(sys.argv[2])
    if not wellcoords_filename.exists():
        print(f'File {wellcoords_filename} does not exist!')
        os._exit(1)

    result_filename = Path(sys.argv[3])   

    start_depth = None

    if len(sys.argv) > 4:
            start_depth = int(sys.argv[4])         


    print('Scanning SEG-Y headers...')

    inline_fast = True   
    fast_string = "Inline"

    geo_c, grid_c, depth = load_segy_coords(os.path.join(segy_foldername, segy_filenames[0]))
        
    if grid_c[0,0] == grid_c[2,0]:
        inline_fast = False
        fast_string = "Crossline"
    inlines = np.unique(grid_c[:,0])
    xlines = np.unique(grid_c[:,1])
    print(f'SEG-Y headers scanned. Inlines:{min(inlines)}-{max(inlines)}, Crosslines:{min(xlines)}-{max(xlines)}, Fast Axis: {fast_string}')

    # Загрузка координат
    print('Загрузка координат скважины...')
    coords = load_well_coords(wellcoords_filename)
    if len(coords) == 0:
        os._exit(1)
    well_col = coords.columns[0]    
    x_col = coords.columns[1]
    y_col = coords.columns[2]
    z_col = coords.columns[3]

    # Вычисляем инлайны и кросслайны с помощью линейной регрессии
    rgr = LinearRegression()
    rgr.fit(geo_c, grid_c)

    ilxl = rgr.predict(coords[[x_col, y_col]].values)
    coords['IL'] = ilxl[:,0]
    coords['XL'] = ilxl[:,1]


    # обрезка точек, выходящих за пределы куба
    coords=coords[(coords.IL>=min(inlines))&(coords.IL<=max(inlines))]
    coords=coords[(coords.XL>=min(xlines))&(coords.XL<=max(xlines))]
    coords=coords[(coords[z_col]>=min(depth))&(coords[z_col]<=max(depth))].reset_index(drop=True)

   
    for i, name in enumerate(segy_filenames):
        data = load_cube(os.path.join(segy_foldername, name))        
        if not inline_fast:
            data = data.reshape(len(inlines), len(xlines), data.shape[-1])
        else:
            data = data.reshape(len(xlines), len(inlines), data.shape[-1]).transpose((1,0,2))    

        interpolator = RegularGridInterpolator((inlines, xlines, depth), data)
        
        seismic_values = []
        for well in pd.unique(coords[well_col]):
         
            t = coords[coords[well_col]==well].reset_index(drop=True)
            
            well_grid_coords = np.column_stack((t.IL, t.XL, t[z_col]))          
            well_seismic = interpolator(well_grid_coords)          
            seismic_values.extend(well_seismic)

        coords[name] = seismic_values
        
    try:
        coords.to_csv(result_filename, index=None)
    except:
        print(f'There is a problem with saving to file {result_filename}!')    
        os._exit(1)
    print(f'File {result_filename} is successfully written')