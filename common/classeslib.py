import segyio
import numpy as np
import pandas as pd
import os
import sys
import time

from sklearn.linear_model import LinearRegression, RidgeCV
from scipy.interpolate import RegularGridInterpolator

def error_msg(msg):
    print(f"Error: {msg}")        

class Extractor:

    def __init__(self, is3D) -> None:
        self.is3D = is3D
        self.geo_coords = []
        self.grid_coords = []  
        self.inline_fast = False
        self.inlines = []
        self.xlines = []    
        self.start_depth = 0
        self.depth_step = 0
        self.depths = []
        self.seis_folder  = ""
        self.table_file_name = ""
        self.table = pd.DataFrame()  
        self.table_old = pd.DataFrame()             
        self.filenames = []
        self.total_samples = 0
        self.x_col = 0
        self.y_col = 1
        self.z_col = 2
        self.current_traces = []
        

    def scan_seismic_folder(self, folder_name, cdpx_byte=181, cdpy_byte=185, inline_byte=189, xline_byte=193):
        if not os.path.exists(folder_name) or not os.path.isdir(folder_name):
            error_msg(f"Folder {folder_name} does not exist!")
            return False
        self.seis_folder = folder_name                
        print(f'Scanning SEG-Y headers of first file in folder {self.seis_folder}...')
        self.filenames = [fname for fname in os.listdir(self.seis_folder) if fname.endswith('.sgy') or fname.endswith('.segy')]
        if len(self.filenames) == 0:
            error_msg(f'No SEG-Y files in folder {self.seisfolder}!')
            return False

        with segyio.open(os.path.join(self.seis_folder, self.filenames[0]), ignore_geometry=True) as f:
            for i in range(f.tracecount):
                self.geo_coords.append([f.header[i][cdpx_byte], f.header[i][cdpy_byte]])
                if self.is3D:
                    self.grid_coords.append([f.header[i][inline_byte], f.header[i][xline_byte]])            
                else:
                    self.grid_coords.append([1, i]) # in case of 2D, inline is constant and xline = trace number
            self.depth_step = f.bin[segyio.BinField.Interval]//1000
            self.total_samples = f.bin[segyio.BinField.Samples]
            self.start_depth = f.header[0][segyio.TraceField.LagTimeA]
        self.depths = np.arange(self.start_depth, self.start_depth+self.depth_step*self.total_samples, self.depth_step)
        self.grid_coords = np.array(self.grid_coords)
        self.geo_coords = np.array(self.geo_coords)
        self.inlines = np.unique(self.grid_coords[:, 0])
        self.xlines = np.unique(self.grid_coords[:, 1])
        if self.grid_coords[0,0] != self.grid_coords[2,0]:
            self.inline_fast = True
        return True    

    def recalc_depth(self, new_start_depth):
        if new_start_depth >= 0:
            self.start_depth = new_start_depth
            self.depths = np.arange(self.start_depth, self.start_depth+self.depth_step*self.total_samples, self.depth_step)

    def load_table(self, table_file_name):
        self.table_file_name = table_file_name
        if not os.path.exists(self.table_file_name) or not os.path.isfile(self.table_file_name):
            error_msg(f'File {self.table_file_name} does not exist!')
            return False
         
        self.table_file_name = table_file_name
        if self.table_file_name.endswith('.xlsx'):
            try:
                self.table = pd.read_excel(self.table_file_name)
            except:
                error_msg(f'Cannot read Excel file {self.table_file_name}')
                return False
        else:
            try:
                self.table = pd.read_csv(self.table_file_name)        
            except:
                error_msg(f'Cannot read CSV table file {self.table_file_name}')
                return False

        if len(self.table.columns) < 3:
            error_msg(f'Number of columns in file {self.table_file_name} must be not less than 3!')
            return False

        if len(self.table) == 0:
            error_msg(f'Empty table in file {self.table_file_name}!')   
            return False

        self.table_old = self.table.copy()    

        return True    

    def restore_table(self):
        self.table = self.table_old.copy()    

    def set_coord_columns_by_name(self, new_x_col, new_y_col, new_z_col):
        if not {new_x_col, new_y_col, new_z_col}.issubset(set(self.table.columns)):
            error_msg('Column names are not present in loaded table!')
            return False
        self.x_col = new_x_col
        self.y_col = new_y_col
        self.z_col = new_z_col
        return True

    def calc_well_grid_coords(self, bin_averaging):
    # Finds dependecy between geo coordinates and grid coordinates using regression and then calculates well grid coordinates
        
        if len(self.table)==0 or len(self.geo_coords)==0 or len(self.grid_coords)==0 or len(self.depths)==0:
            error_msg('For calculation of well grid coordinates, seismic geo and grid coordinates and well geo coordinates must be present!')
            return False
        rgr = LinearRegression()
        if not self.is3D:
            rgr = RidgeCV() # For 3D case linear regression is sufficient, but for curved 2D lines there must be something more complicated    
        try:            
            rgr.fit(self.geo_coords, self.grid_coords)
            self.well_grid_coords = rgr.predict(np.column_stack((self.table.loc[:, self.x_col].values, self.table.loc[:, self.y_col].values)))
        except:
            error_msg('Cannot perform regression to calculate well grid coordinates!')
            return False            
        self.table['inline'] = self.well_grid_coords[:, 0]
        self.table['xline'] = self.well_grid_coords[:, 1]
        if bin_averaging:
            self.table_bin_average()
        self.crop_table()
        return True

    def table_bin_average(self):
    # well samples averaging inside a bin corresponding to seismic cube sampling
        
        inl_step = np.round(np.mean(np.diff(self.inlines)))    
        xln_step = np.round(np.mean(np.diff(self.inlines)))    
        self.table['inline'] = np.round(self.table['inline']/inl_step)*inl_step
        self.table['xline'] = np.round(self.table['xline']/inl_step)*xln_step
        self.table[self.z_col] = np.round(self.table[self.z_col]/self.depth_step)*self.depth_step
        #
        #self.table.to_csv('temp.csv', index=None)
        self.table = self.table.groupby(['inline', 'xline', self.z_col]).mean().reset_index()      


    def crop_table(self):
    # Crops table according to seismic data extent        
        self.table=self.table[(self.table.inline>=min(self.inlines))&(self.table.inline<=max(self.inlines))]
        self.table=self.table[(self.table.xline>=min(self.xlines))&(self.table.xline<=max(self.xlines))]        
        self.table=self.table[(self.table.loc[:, self.z_col]>=min(self.depths))&(self.table.loc[:, self.z_col]<=max(self.depths))].reset_index(drop=True)
        return True

    def load_cube(self, filename):
    # simply reads trace data from file    
        start = time.time()
        try:
            with segyio.open(filename, ignore_geometry=True) as f:
                self.current_traces = np.array([f.trace[i] for i in range(f.tracecount)])
        except:
            error_msg('Cannot load file {filename}')        
            return False
        print(f'File {filename} is read for {(time.time()-start):.2f} seconds')    
        return True
        

    def extract_attribute(self, fname):
    # extracts attribute values from current_traces along well coordinates            
        if not fname in self.filenames:
            error_msg('Invalid file name!')
            return False        
        if not self.load_cube(os.path.join(self.seis_folder, fname)):
            error_msg('Cannot load seismic files!')
            return False      
        data = []                          
        if not self.inline_fast:
            data = self.current_traces.reshape(len(self.inlines), len(self.xlines), self.total_samples)
        else:
            data = self.current_traces.reshape(len(self.xlines), len(self.inlines), self.total_samples).transpose((1,0,2))        
        interpolator = RegularGridInterpolator((self.inlines, self.xlines, self.depths), data)    
        seismic_values = []               
        well_grid_coords = np.column_stack((self.table.inline, self.table.xline, self.table.loc[:, self.z_col]))          
        well_seismic = interpolator(well_grid_coords)          
        seismic_values.extend(well_seismic)
        attribute_name = os.path.splitext(fname)[0]
        self.table[attribute_name] = seismic_values
        return True    

    def save_result_table(self, fname):
    # saves table with extracted data
        if fname.endswith('.xlsx'):
            try:
                self.table.to_excel(fname)
            except:
                error_msg(f'Cannot save Excel file {fname}!')
                return False
        else:
            try:
                self.table.to_csv(fname, index=False)
            except:
                error_msg(f'Cannot save CSV table file {fname}')
                return False
        return True        

        
        

        