import segyio
import numpy as np
import pandas as pd
import time

# Чтение заголовков SEG-Y 
def load_segy_coords(name):    
    geo_c = []
    grid_c = []
    traces = []    
    with segyio.open(name, ignore_geometry=True) as f:
        for i in range(f.tracecount):
            geo_c.append([f.header[i][181], f.header[i][185]])
            grid_c.append([f.header[i][189], f.header[i][193]])            
        depth_step = f.bin[segyio.BinField.Interval]//1000
        total_samples = f.bin[segyio.BinField.Samples]
        start_depth = f.header[0][segyio.TraceField.LagTimeA]
    grid_c = np.array(grid_c)   
    geo_c = np.array(geo_c)          

    return geo_c, grid_c, np.arange(start_depth, start_depth+total_samples*depth_step, depth_step)

# Чтение координат скважин из CSV
def load_well_coords(name):    
    well_df = pd.read_csv(name)
    if len(well_df.columns) < 4:
        print('Number of columns must be not less than 4!')
        return pd.DataFrame()

    if len(well_df) == 0:
        print('Empty table!')   
        return pd.DataFrame()

    return well_df

# Загрузка данных из SEG-Y куба
def load_cube(name):
    start = time.time()
    with segyio.open(name, ignore_geometry=True) as f:
        traces = [f.trace[i] for i in range(f.tracecount)]
    print(f'File {name} is read for {(time.time()-start):.2f} seconds')    
    return np.array(traces)