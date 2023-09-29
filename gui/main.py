import sys  # 
import os

from PyQt5 import QtWidgets, QtCore
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from scipy.interpolate import RegularGridInterpolator

import design  # PyQt Design file

sys.path.append("..")
from common.classeslib import *


class ExtractorApp(QtWidgets.QMainWindow, design.Ui_MainWindow):

    geo_c = []
    grid_c = []
    depth = []
    depth_step = 0    
    segy_foldername = ""
    segy_filenames = []
    well_filename = ""
    well_coords = pd.DataFrame()
    inlines = []
    xlines = []
    inline_fast = False

    def __init__(self):
        
        super().__init__()        
        self.setupUi(self)  

        self.extractor = Extractor(True)
        
        self.button_OpenSegyFolder.clicked.connect(self.chooseSegyFolder)
        self.button_ScanSegyFolder.clicked.connect(self.scanSegyFolder)

        self.button_OpenWellFile.clicked.connect(self.chooseWellFile)
        self.button_ScanWellFile.clicked.connect(self.scanWellFile)

        self.button_Extract.clicked.connect(self.extractData)
        

    def wait_start(self):
        self.group_Seismic.setProperty("enabled", False)
        self.group_Wells.setProperty("enabled", False)   
        QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)

    def wait_end(self):  
        QtWidgets.qApp.setOverrideCursor(QtCore.Qt.ArrowCursor)    
        self.group_Seismic.setProperty("enabled", True)
        self.group_Wells.setProperty("enabled", True)   
        
    def errorMessage(self, text):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(text)       
        msg.setWindowTitle("Error")
        msg.exec_()

    def successMessage(self, text):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText(text)
        msg.setWindowTitle("Success")
        msg.exec_()

    def fill_segyparams_table(self):
        self.table_SEGYParams.setItem(0, 1, design.create_non_editable_item(f'{np.min(self.extractor.inlines)}-{np.max(self.extractor.inlines)}'))
        self.table_SEGYParams.setItem(1, 1, design.create_non_editable_item(f'{np.min(self.extractor.xlines)}-{np.max(self.extractor.xlines)}'))
        fast_msg = "XLINE"
        if self.extractor.inline_fast:
            fast_msg = "INLINE"
        self.table_SEGYParams.setItem(2, 1, design.create_non_editable_item(fast_msg))
        self.table_SEGYParams.setItem(3, 1, design.create_non_editable_item(f'{np.min(self.extractor.geo_coords[:,0])}-{np.max(self.extractor.geo_coords[:,0])}'))
        self.table_SEGYParams.setItem(4, 1, design.create_non_editable_item(f'{np.min(self.extractor.geo_coords[:,1])}-{np.max(self.extractor.geo_coords[:,1])}'))        
        self.table_SEGYParams.setItem(5, 1, QtWidgets.QTableWidgetItem(f'{self.extractor.start_depth}')) # Changeable item!
        self.table_SEGYParams.setItem(6, 1, design.create_non_editable_item(f'{self.extractor.depth_step}'))
        self.table_SEGYParams.setItem(7, 1, design.create_non_editable_item(f'{self.extractor.depths[-1]}'))        


    def scanSegyFolder(self):        
        self.list_Filenames.clear()                
        self.wait_start()
        directory = self.edit_SEGYFolderName.text()
        if directory:                    
            if not self.extractor.scan_seismic_folder(directory):
                self.errorMessage('Check your SEG-Y folder!')
                return          
            self.fill_segyparams_table()                   
        self.list_Filenames.addItems(self.extractor.filenames)    
        self.wait_end()    
        print('Done.')    


    def chooseSegyFolder(self):
       
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose SEG-Y folder")
        if directory:
            self.edit_SEGYFolderName.setText(directory)
            #self.scanSegyFolder()

    def chooseWellFile(self):

        filename, check = QtWidgets.QFileDialog.getOpenFileName(self, "Choose well coordinates file", "", "CSV files (*.csv) ;; Excel files (*.xlsx)")
        if filename:
            self.edit_WellFileName.setText(filename)               

    def fill_wellTable(self):    
        self.table_WellData.setRowCount(len(self.extractor.table))
        self.table_WellData.setColumnCount(len(self.extractor.table.columns))
        self.table_WellData.setHorizontalHeaderLabels(self.extractor.table.columns)
        for i in range(len(self.extractor.table)):
            for j in range(len(self.extractor.table.columns)):
                self.table_WellData.setItem(i, j, design.create_non_editable_item(str(self.extractor.table.iloc[i, j])))                      

    def scanWellFile(self):          
        print(self.edit_WellFileName.text())
        self.wait_start()
        if not self.extractor.load_table(self.edit_WellFileName.text()):    
            self.errorMessage("Something wrong with your well coordinates table!")   
            return
        
        self.fill_wellTable()              
        self.combo_choose_Xcol.addItems(self.extractor.table.columns)
        self.combo_choose_Ycol.addItems(self.extractor.table.columns)
        self.combo_choose_Zcol.addItems(self.extractor.table.columns)
        self.combo_choose_Xcol.setCurrentIndex(0)
        self.combo_choose_Ycol.setCurrentIndex(1)
        self.combo_choose_Zcol.setCurrentIndex(2)
        self.wait_end()
         
    def updateDepth(self):
        try:
            self.depth_step = int(self.table_SEGYParams.item(6, 1).text())
        except:
            self.errorMessage("Check your parameters!")   
            return   
        try:                 
            self.depth_start = int(self.table_SEGYParams.item(5, 1).text())
        except:
            self.errorMessage("Check your parameters!")   
            return  
        self.depth = np.arange(self.depth_start, self.depth_start+self.depth_step*len(self.depth), self.depth_step)
        self.table_SEGYParams.setItem(7, 1, design.create_non_editable_item(f'{self.depth[-1]}'))
    
    def extractData(self):               
        try:
            depth_start = int(self.table_SEGYParams.item(5, 1).text())
        except:
            self.errorMessage("Start depth is invalid!")   
            return      

        self.extractor.recalc_depth(depth_start)    

        if not self.extractor.set_coord_columns_by_name(self.combo_choose_Xcol.currentText(), self.combo_choose_Ycol.currentText(), self.combo_choose_Zcol.currentText()):
            self.errorMessage("Something wrong with specified columns!")
            return
       
        if not self.extractor.calc_well_grid_coords(self.checkbox_bin_averaging.isChecked()):
            self.errorMessage("Cannot perform regression to calculate well grid coordinates!")
            return 

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Save File", ".", "CSV files (*.csv);; Excel files (*.xlsx)")

        if filename:
            for i, fname in enumerate(self.extractor.filenames):
                
                self.progressBar.setProperty("visible", True)
                self.wait_start()                    
                
                if not self.extractor.extract_attribute(fname):
                    self.errorMessage(f"Cannot process file {fname}!")
                    self.wait_end()
                    return                         
               
                progval = self.progressBar.value() + 100/len(self.extractor.filenames)
                if i == len(self.extractor.filenames)-1:
                    progval = 100
                self.progressBar.setProperty("value", progval)

            if not self.extractor.save_result_table(filename):
                self.errorMessage(f"Cannot save file {filename}!")
                self.wait_end()
                return                     

            self.progressBar.setProperty("visible", False)
            self.wait_end()
            self.successMessage(f'File {filename} successfully saved') 
              
            

                                           

def main():
    app = QtWidgets.QApplication(sys.argv)   
    window = ExtractorApp() 
    window.setWindowTitle("SeisExtractor GUI v.0.2")
    window.show() 
    app.exec_()  

if __name__ == '__main__':  
    main()  