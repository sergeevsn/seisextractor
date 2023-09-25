import sys  # sys нужен для передачи argv в QApplication
import os

from PyQt5 import QtWidgets, QtCore
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from scipy.interpolate import RegularGridInterpolator

import design  # дизайн окна PyQt

sys.path.append("..")
from common.utils import load_segy_coords, load_well_coords, load_cube


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
        
        self.button_OpenSegyFolder.clicked.connect(self.chooseSegyFolder)
        self.button_ScanSegyFolder.clicked.connect(self.scanSegyFolder)

        self.button_OpenWellFile.clicked.connect(self.chooseWellFile)
        self.button_ScanWellFile.clicked.connect(self.scanWellFile)

        self.button_Extract.clicked.connect(self.extractData)
        

    def errorMessage(self, text):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(text)
        #msg.setInformativeText(text)
        msg.setWindowTitle("Error")
        msg.exec_()

    def successMessage(self, text):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText(text)
        msg.setWindowTitle("Success")
        msg.exec_()

    def scanSegyFolder(self):
        self.list_Filenames.clear()
        self.segy_filenames = []
        directory = self.edit_SEGYFolderName.text()
        if directory:  
            for file_name in os.listdir(directory): 
                if file_name.endswith('.sgy') or file_name.endswith('.segy'):
                    self.list_Filenames.addItem(file_name)
                    self.segy_filenames.append(file_name)
        
        self.segy_foldername = directory
        
        if not os.path.exists(self.segy_foldername)  or not os.path.isdir(self.segy_foldername) or len(self.segy_filenames) == 0:
            self.errorMessage('Check your SEG-Y folder!')
            return                 


        self.geo_c, self.grid_c, self.depth = load_segy_coords(os.path.join(directory, self.segy_filenames[0]))
        self.inlines = np.unique(self.grid_c[:, 0])
        self.xlines = np.unique(self.grid_c[:, 1])       
        
        if self.grid_c[0,0] == self.grid_c[2,0]:
            self.inline_fast = False
            self.table_SEGYParams.setItem(2, 1, design.create_non_editable_item(f'Crossline'))
        else:
            self.inline_fast = True
            self.table_SEGYParams.setItem(2, 1, design.create_non_editable_item(f'Inline'))

        self.depth_step = self.depth[1] - self.depth[0]   

        self.table_SEGYParams.setItem(0, 1, design.create_non_editable_item(f'{np.min(self.inlines)}-{np.max(self.inlines)}'))
        self.table_SEGYParams.setItem(1, 1, design.create_non_editable_item(f'{np.min(self.xlines)}-{np.max(self.xlines)}'))
        self.table_SEGYParams.setItem(3, 1, design.create_non_editable_item(f'{np.min(self.geo_c[:,0])}-{np.max(self.geo_c[:,0])}'))
        self.table_SEGYParams.setItem(4, 1, design.create_non_editable_item(f'{np.min(self.geo_c[:,1])}-{np.max(self.geo_c[:,1])}'))        
        self.table_SEGYParams.setItem(5, 1, QtWidgets.QTableWidgetItem(f'{np.min(self.depth)}'))
        self.table_SEGYParams.setItem(6, 1, QtWidgets.QTableWidgetItem(f'{self.depth_step}'))
        self.table_SEGYParams.setItem(7, 1, design.create_non_editable_item(f'{self.depth[-1]}'))         

        

    def calc_well_grid_coords(self):
        rgr = LinearRegression()
        rgr.fit(self.geo_c, self.grid_c)
        df = self.well_coords.copy()
        ilnxln = rgr.predict(np.column_stack((self.well_coords.iloc[:,1].values, self.well_coords.iloc[:,2].values)))
        df['INL'] = ilnxln[:,0]
        df['XLN'] = ilnxln[:,1]
       
        # обрезка точек, выходящих за пределы куба
        df=df[(df.INL>=min(self.inlines))&(df.INL<=max(self.inlines))]
        df=df[(df.XLN>=min(self.xlines))&(df.XLN<=max(self.xlines))]
        df=df[(df[df.columns[3]]>=min(self.depth))&(df[df.columns[3]]<=max(self.depth))].reset_index(drop=True)
    
        return df


    def chooseSegyFolder(self):
       
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose SEG-Y folder")
        if directory:
            self.edit_SEGYFolderName.setText(directory)
            self.scanSegyFolder()

    def scanWellFile(self):

        self.well_filename = self.edit_WellFileName.text() 

        if not os.path.exists(self.well_filename) or not os.path.isfile(self.well_filename):
            self.errorMessage("Speciefied well coordinates file doesn't exist!")   
            return     
        
        self.well_coords = load_well_coords(self.well_filename)
        if self.well_coords.empty:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage("Something wrong with your well coordinates table!")   
            return
        
        self.table_WellData.setRowCount(len(self.well_coords))
        for i in range(len(self.well_coords)):
            for j in range(4):
                self.table_WellData.setItem(i, j, design.create_non_editable_item(str(self.well_coords.iloc[i, j])))                
         
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
        
        self.updateDepth()
       
        if len(self.geo_c)==0 or len(self.grid_c)==0 or len(self.depth)==0 or self.depth_step<0 or len(self.well_coords)==0:
            self.errorMessage("Check your parameters!")   
            return   
       
        df = self.calc_well_grid_coords()   
        #df.to_excel('temp_coords_gui.xlsx')
        
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Save File", ".", "CSV files (*.csv);;All Files (*)")

        if filename:
            for i, name in enumerate(self.segy_filenames):
                
                self.progressBar.setProperty("visible", True)
                self.group_Seismic.setProperty("enabled", False)
                self.group_Wells.setProperty("enabled", False)               
                
                QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)

                data = load_cube(os.path.join(self.segy_foldername, name))
                
                if not self.inline_fast:
                    data = data.reshape(len(self.inlines), len(self.xlines), data.shape[-1])
                else:
                    data = data.reshape(len(self.xlines), len(self.inlines), data.shape[-1]).transpose((1,0,2))    
                
                interpolator = RegularGridInterpolator((self.inlines, self.xlines, self.depth), data)

                seismic_values = []
             
                for well in pd.unique(df[df.columns[0]]):                  
                    t = df[df[df.columns[0]]==well].reset_index(drop=True)                            
                    well_grid_coords = np.column_stack((t.INL, t.XLN, t[t.columns[3]]))                   
                    well_seismic = interpolator(well_grid_coords)                     
                    seismic_values.extend(well_seismic)

                df[name] = seismic_values
                progval = self.progressBar.value() + 100/len(self.segy_filenames)
                if i == len(self.segy_filenames)-1:
                    progval = 100
                self.progressBar.setProperty("value", progval)

            try:
                df.to_csv(filename, index=None)
            except:
                self.errorMessage(f'There is a problem with saving result to file {filename}!')
                return

            self.successMessage(f'File {filename} successfully saved') 
            self.progressBar.setProperty("visible", False)   
            self.group_Seismic.setProperty("enabled", True)
            self.group_Wells.setProperty("enabled", True)   
            QtWidgets.qApp.restoreOverrideCursor() 


    def chooseWellFile(self):

        filename, check = QtWidgets.QFileDialog.getOpenFileName(self, "Choose well coordinates file")
        if filename:
            self.edit_WellFileName.setText(filename)             
            self.scanWellFile()                          

def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication    
    window = ExtractorApp()  # Создаём объект класса ExampleApp
    window.setWindowTitle("SeisExtractor GUI v.0.1")
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()