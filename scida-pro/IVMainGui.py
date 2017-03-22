# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import os, ntpath, pickle
from HelpDialog import HelpDialog
from PyQt5 import QtCore, QtGui, QtWidgets
from IVMainPlot import CorrVocIsc, CorrEtaFF, CorrRshFF, DistLtoH, DensEta, DistWT, DistRM, IVBoxPlot, IVHistPlot, IVHistDenPlot, ViolinPlot

class IVMainGui(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(IVMainGui, self).__init__(parent)
        self.setWindowTitle(self.tr("SCiDA Pro"))
        self.setWindowIcon(QtGui.QIcon(":ScidaPro_icon.png"))
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint) # DISABLE BEFORE RELEASE

        ### Set initial geometry and center the window on the screen ###
        self.resize(1024, 576)
        frameGm = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft()) 

        ### Set default font size ###
        self.setStyleSheet('font-size: 12pt;')  

        self.clip = QtWidgets.QApplication.clipboard()
        self.series_list_model = QtGui.QStandardItemModel()
        self.series_list_model.itemChanged.connect(self.rename_dataset)
        self.filter_table_widget = QtWidgets.QTableWidget()
        self.default_filters = [
            ["IRev1",">",3],["FF","<",70],["Eta","<",16],
            ["FF","<",75],["Rsh","<",20],["Eta","<",18]
            ]
        self.user_filters = []
        self.user_filters_plain_format = []
        self.ad = {} # all data
        self.adindex = ['Uoc','Isc','RserLfDfIEC','Rsh','FF','Eta','IRev1']
        
        self.label_formats = {}
        self.label_formats[0] = ['Uoc','Isc','RserLfDfIEC','Rsh','FF','Eta','IRev1']
        self.label_formats[1] = ['Uoc0','Isc0','Rseries_multi_level','Rshunt_SC','Fill0','Eff0','Ireverse_2']
        self.label_formats[2] = ['Uoc','Isc','RserIEC891','RshuntDfDr','FF','Eta','IRev1']
        self.label_formats[3] = ['Uoc','Isc','Rs','Rsh','FF','NCell','Irev2']        
        self.label_format = 0
        self.label_text = QtWidgets.QLabel("Data label set A")
        self.first_run = True

        self.status_text = QtWidgets.QLabel("")

        self.yl = [] # yield loss
        self.smr = [] # summaries                     
        self.smrindex = ['Best cell','Median','Average','Std.dev.']
        self.smrcolumns = ['Voc [V]','Isc [A]','Rser [mOhm*cm2]','Rshunt [kOhm]','FF [%]','Eta [%]','Irev [A]']      
        self.ct = [] # correlation table
        self.reportname = ''
        self.yloutput = []
        self.translator = None
        self.plot_selection_list = ['Uoc','Isc','Voc*Isc','FF','Eta','RserLfDfIEC','Rsh','IRev1']
        self.plot_selection_combo_list = []
        self.plot_selection_combo_list.append(self.tr('Boxplot'))
        self.plot_selection_combo_list.append(self.tr('Violinplot'))
        self.plot_selection_combo_list.append(self.tr('Walk-through'))
        self.plot_selection_combo_list.append(self.tr('Rolling mean'))
        self.plot_selection_combo_list.append(self.tr('Low to high'))
        self.plot_selection_combo_list.append(self.tr('Histogram'))
        self.plot_selection_combo_list.append(self.tr('Density'))
        self.plot_selection_combo_list.append(self.tr('Histogram + density'))
        self.plot_selection_combo_list.append(self.tr('Voc-Isc'))
        self.plot_selection_combo_list.append(self.tr('Eta-FF'))
        self.plot_selection_combo_list.append(self.tr('Rsh-FF'))     
        self.param_one_combo = QtWidgets.QComboBox(self)
        self.plot_selection_combo = QtWidgets.QComboBox(self)
        self.plot_selection_combo.currentIndexChanged.connect(self.plot_selection_changed)        
        
        self.prev_dir_path = ""
        self.wid = None
        
        self.create_menu()
        self.create_main_frame()
        self.set_default_filters()      

    @QtCore.pyqtSlot(int)
    def plot_selection_changed(self, index):
        
        if index < 3:
            self.param_one_combo.setEnabled(True)
        elif index > 2 and index < 7:
            self.param_one_combo.setCurrentIndex(4)
            self.param_one_combo.setDisabled(True)
        else:
            self.param_one_combo.setDisabled(True)
            
    @QtCore.pyqtSlot(QtGui.QStandardItem)
    def rename_dataset(self,item):
        entered_name = str(item.text())
        
        keepcharacters = (' ','.','_')
        valid_filename = "".join(c for c in entered_name if c.isalnum() or c in keepcharacters).rstrip()


        if len(valid_filename) > 0:
            self.ad[self.series_list_model.indexFromItem(item).row()].index.name = valid_filename
            item.setText(valid_filename)
        else:
            item.setText(self.ad[self.series_list_model.indexFromItem(item).row()].index.name)

    def load_file(self, filename=None):   

        #fileNames = QtWidgets.QFileDialog.getOpenFileNames(self,self.tr("Load files"), self.prev_dir_path, "Excel Files (*.csv)")
        fileNames = QtWidgets.QFileDialog.getOpenFileNames(self,self.tr("Load files"), self.prev_dir_path, "Excel Files (*.csv *.xls *.xlsx)")
        fileNames = fileNames[0]
        
        if (not fileNames):
            return        
        
        empty_data_warning = False
        non_ascii_warning = False
        read_error_warning = False

        num = len(self.ad)

        for filename in fileNames:
            # Read all .csv files and insert selected columns into ad
            # Purge rows with empty or negative elements
            # Enter new data set names into ad and series list

            # Check for non-ASCII filenames, give warning and skip loading such files
            try:
                filename.encode('ascii')
            except:
                non_ascii_warning = True
                continue
        
            # Set working directory so that user can remain where they are
            self.prev_dir_path = ntpath.dirname(filename)

            # Try to load file and give error message if label format is not recognized
            _, file_extension = ntpath.splitext(filename)
            if file_extension == ".csv":
                try:
                    self.ad[num] = pd.read_csv(filename)[self.label_formats[self.label_format]].dropna()
                except KeyError:
                    try:
                        self.ad[num] = pd.read_csv(filename,sep=';')[self.label_formats[self.label_format]].dropna()
                    except KeyError:
                        read_error_warning = True
            else:
                try:
                    xl_file = pd.read_excel(filename)
                    self.ad[num] = xl_file[self.label_formats[self.label_format]].dropna()
                except KeyError:
                    read_error_warning = True
            
            # Try to apply default labels to columns; skip current file if unsuccessful
            try:
                self.ad[num].columns = self.label_formats[0]
            except KeyError:
                continue
          
            # Convert to numeric values if needed, reset size of ad            
            self.ad[num].apply(pd.to_numeric)
            self.ad[num] = self.ad[num][self.ad[num] > 0]
           
            # If data set is empty give warning and remove from ad
            if self.ad[num].empty:
                empty_data_warning = True
                self.ad.pop(num)
                continue                

            # Apply conversion to number sets
            if self.label_format == 1:
                self.ad[num].loc[:,'Eta'] *= 100
                self.ad[num].loc[:,'FF'] *= 100
            elif self.label_format == 3:
                self.ad[num].loc[:,'Eta'] *= 100
            
            ### add list view item ###
            str_a = ntpath.splitext(ntpath.basename(filename))[0]
            self.ad[num].index.name = str_a[0:39] # data set name limited to 40 characters
            item = QtGui.QStandardItem(str_a[0:39])
            font = item.font()
            font.setBold(1)
            item.setFont(font)
            self.series_list_model.appendRow(item)                        
            num += 1
            
        if read_error_warning:
            msg = self.tr("Error while reading data files.\n\nData labels were perhaps not recognized.")
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), msg)

        if empty_data_warning:
            msg = self.tr("Empty data sets were found.\n\nThe application only accepts data entries with a value for Voc, Isc, FF, Eta, Rser, Rsh and Irev. All values also need to be non-negative.")
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), msg)
            
        if non_ascii_warning:
            msg = self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames.")
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), msg)            
                              
        if self.ad:
            self.statusBar().showMessage(self.tr("Ready"))
        else:
            self.statusBar().showMessage(self.tr("Please load data files"))

    def save_files(self):
        dest_dir = QtWidgets.QFileDialog.getExistingDirectory(None, self.tr('Open directory'), self.prev_dir_path, QtWidgets.QFileDialog.ShowDirsOnly)
        
        if not dest_dir:
            return
        
        if len(self.ad) == 0:
            self.statusBar().showMessage(self.tr("Please load data files"))
            return

        self.prev_dir_path = dest_dir
            
        yes_to_all = False
        
        for i in self.ad:
            # Export all filtered IV data to existing csv files
            filename = self.ad[i].index.name + '.csv'
            check_overwrite = False
            save_path = ""
            
            # check if file exists and then ask if overwrite is oke
            if os.name == 'nt': # if windows
                save_path = dest_dir + '\\' + filename
                if os.path.isfile(save_path):
                    check_overwrite = True
            else: # if not windows
                save_path = dest_dir + '\/' + filename
                if os.path.isfile(save_path):
                    check_overwrite = True

            if check_overwrite and not yes_to_all:
                reply = QtWidgets.QMessageBox.question(self, self.tr("Message"), "Overwrite \'" + filename + "\'?", QtWidgets.QMessageBox.YesToAll | QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.No)

                if reply == QtWidgets.QMessageBox.No:                    
                    save_path = QtWidgets.QFileDialog.getSaveFileName(self,self.tr("Save file"), dest_dir, "CSV File (*.csv)")
                    
                    if not save_path:
                        continue

                if reply == QtWidgets.QMessageBox.YesToAll:
                    yes_to_all = True
                    
                if reply == QtWidgets.QMessageBox.Cancel:
                    return
                           
            self.ad[i].to_csv(save_path, index=False)
        
        self.statusBar().showMessage(self.tr("Files saved")) 
                   
    def combine_datasets(self):

        if len(self.ad) > 1:
            self.statusBar().showMessage(self.tr("Combining data sets..."))
        else:
            self.statusBar().showMessage(self.tr("Please load data files"))
            return     

        # Clearing associated data sets
        self.yl = []
        self.yloutput = []
        self.smr = [] 
        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels(['Data series'])

        num = len(self.ad)
        if num > 1:
            i = 1
            while i < num:
                self.ad[0] = pd.concat([self.ad[0],self.ad[i]], ignore_index=True)
                self.ad.pop(i)
                i += 1

        self.ad[0].index.name = 'Combined data set'

        # Update list view
        item = QtGui.QStandardItem(self.ad[0].index.name)
        font = item.font()
        font.setBold(1)
        item.setFont(font)
        self.series_list_model.appendRow(item) 
                
        self.statusBar().showMessage(self.tr("Ready"))

    def filter_data(self):

        if self.ad:
            self.statusBar().showMessage(self.tr("Filtering data..."))
        else:
            self.statusBar().showMessage(self.tr("Please load data files"))
            return            

        self.read_filter_table()

        ylcolumns = []
        for i in np.arange(0,12):
            ylcolumns.append('Filter ' + str(i+1))
        
        ylindex = ['Filter','Loss count']
        
        for j in np.arange(len(self.yl),len(self.ad)):
            
            self.yl.append(pd.DataFrame(index=ylindex, columns=ylcolumns))
            self.yl[j].index.name = len(self.ad[j].index) # count number before filtering and store in index name
            
            for i in np.arange(0,12):
                if self.filter_table_widget.item(i,0).text():
                    filter_part1 = str(self.filter_table_widget.item(i,0).text())
                    filter_part2 = str(self.filter_table_widget.item(i,1).text())
                    filter_part3 = str(self.filter_table_widget.item(i,2).text())
                    self.yl[j].ix[0,i] = filter_part1 + filter_part2 + filter_part3 # insert filter information
                
                    if filter_part2 == ">":
                        self.yl[j].ix[1,i] = (self.ad[j][filter_part1] > float(filter_part3)).sum() # count yield loss cells
                        self.ad[j] = self.ad[j][self.ad[j][filter_part1] <= float(filter_part3)]
                    elif filter_part2 == "<":
                        self.yl[j].ix[1,i] = (self.ad[j][filter_part1] < float(filter_part3)).sum()
                        self.ad[j] = self.ad[j][self.ad[j][filter_part1] >= float(filter_part3)]

            name = self.ad[j].index.name
            self.ad[j] = self.ad[j].reset_index(drop=True) # renumber index due to removed yield loss cells
            self.ad[j].index.name = name                              

        for i in self.ad: # number of series_list items is same as for self.ad, but not nice
            item = self.series_list_model.item(i)
            font = item.font()
            font.setBold(0)
            item.setFont(font)

        self.statusBar().showMessage(self.tr("Ready"))                                    

    def make_report(self):

        if self.ad:
            self.reportname = QtWidgets.QFileDialog.getSaveFileName(self,self.tr("Save file"), self.prev_dir_path, "Excel Files (*.xlsx)")
            self.reportname = self.reportname[0]
            
            if not self.reportname:
                return

            if self.reportname:
                self.statusBar().showMessage(self.tr("Making an Excel report..."))
            else:
                return
        else:
            self.statusBar().showMessage(self.tr("Please load data files"))
            return

        try:
            self.reportname.encode('ascii')
        except:
            msg = self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames.")
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), msg) 
            self.reportname = None
            return
                        
        ########## Generate summary tables ##########   

        self.smr = [] # empty any existing table                                        
                                                   
        for i in self.ad:
            self.smr.append(pd.DataFrame(index=self.smrindex, columns=self.smrcolumns))
            self.smr[i].index.name = 'Data property'
            self.smr[i]['Data set'] = self.ad[i].index.name + ' (' + repr(len(self.ad[i])) + ' cells)'
            self.smr[i] = self.smr[i].set_index('Data set', append=True).swaplevel(0,1)

        for i1 in self.ad:
            for i2, value in enumerate(self.ad[i1].max()):
                self.smr[i1].ix[0,i2] = self.ad[i1].ix[self.ad[i1].idxmax()[5]][i2]
                self.smr[i1].ix[1,i2] = self.ad[i1].median()[i2]
                self.smr[i1].ix[2,i2] = self.ad[i1].mean()[i2]            
        
                paramlist = [0,1,4,5]
                if i2 in paramlist:
                    self.smr[i1].ix[3,i2] = self.ad[i1].std()[i2]
                else:
                    self.smr[i1].ix[3,i2] = np.nan

            self.smr[i1].apply(pd.to_numeric)

            self.smr[i1].iloc[:,2] = self.smr[i1].iloc[:,2]*1000
            self.smr[i1].iloc[:,3] = self.smr[i1].iloc[:,3]/1000

    
            roundinglist = [3,2,2,2,1,2,2]            
            for i3, value in enumerate(roundinglist):
                self.smr[i1].iloc[:,i3] = np.round(self.smr[i1].iloc[:,i3].astype(np.double),decimals=value)

        ########## Generate yield loss tables for output ##########

        self.yloutput = self.yl[:] # [:] is there so that it makes a copy and not a reference
        
        for i, value in enumerate(self.yloutput):
            # enter total columns with total counts           
            self.yloutput[i]['Total'] = np.nan
            self.yloutput[i].ix[1,12] = self.yloutput[i].ix[1,:].sum()

        for i, value in enumerate(self.yloutput):             
            # add percentages row
            self.yloutput[i].loc['Loss %'] = np.nan 
            
            for j in np.arange(0,len(self.yloutput[i].columns)):
                if not self.yloutput[i].ix[1,j] == np.nan:
                    self.yloutput[i].ix[2,j] = np.round(100 * self.yloutput[i].ix[1,j] / self.yloutput[i].index.name,decimals=2)
                    
            self.yloutput[i] = self.yloutput[i].dropna(1,'all') # drop completely empty filter columns in output
            
            # Bugfix; pandas recommends using .loc here
            self.yloutput[i].index.name = 'Data property'
            self.yloutput[i]['Data set'] = self.ad[i].index.name + ' (' + repr(self.yloutput[i].index.name) + ' cells)'
            self.yloutput[i] = self.yloutput[i].set_index('Data set', append=True).swaplevel(0,1)
                           
        ########## Generate correlation tables ##########

        self.ct = [] # empty any existing table
        
        for i in self.ad:
            self.ct.append(np.round(self.ad[i].corr(), decimals=2))
            self.ct[i].iloc[:,2:4] = np.nan
            self.ct[i].iloc[2:4,:] = np.nan
            self.ct[i].iloc[6,:] = np.nan
            self.ct[i].iloc[:,6] = np.nan
            self.ct[i] = self.ct[i].dropna(0,'all').T.dropna(0,'all')
            self.ct[i].index.name = 'Data property'
            self.ct[i]['Data set'] = self.ad[i].index.name + ' (' + repr(len(self.ad[i])) + ' cells)'
            self.ct[i] = self.ct[i].set_index('Data set', append=True).swaplevel(0,1) 
   
        ########## Export all summary and yield loss data to an Excel file ##########

        writer = pd.ExcelWriter(self.reportname, engine='xlsxwriter')
        
        if self.smr: # make sure tables are not empty to avoid any exceptions
            output1 = pd.concat(self.smr)
            output1.to_excel(writer,str(self.tr('Summary'))) # str() because xlsxwriter does not accept QString
            
        if self.yloutput:
            output2 = pd.concat(self.yloutput)            
            output2.to_excel(writer,str(self.tr('Yield loss')))
               
        if self.ct:                
            output3 = pd.concat(self.ct)
            output3.to_excel(writer,str(self.tr('Correlation')))
                
        writer.save()       
      
        self.statusBar().showMessage(self.tr("Ready"))

    def open_report(self):
        
        if len(self.reportname):
            self.statusBar().showMessage(self.tr("Opening report..."))
            if self.reportname[0] != '/': # windows
                str_a = 'file:///' + self.reportname
            else: # linux
                str_a = 'file://' + self.reportname
            
            # Strict mode necessary for linux compatibility (spaces > %20)
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(str_a, QtCore.QUrl.StrictMode)) 

            self.statusBar().showMessage(self.tr("Ready"))
        else:
            self.statusBar().showMessage(self.tr("Please make report"))
                                    
    def clear_data(self):        
        self.ad = {}
        self.yl = []
        self.yloutput = []
        self.smr = [] 
        self.series_list_model.clear()
        self.series_list_model.setHorizontalHeaderLabels(['Data series'])
        self.reportname = ''
        self.statusBar().showMessage(self.tr("All data has been cleared"))           

    def open_plot_selection(self):
        
        if self.ad:
             self.statusBar().showMessage(self.tr("Creating plot window..."))
        else:
            self.statusBar().showMessage(self.tr("Please load data files"))
            return

        selected_plot_combo = 0
        for i, value in enumerate(self.plot_selection_combo_list):
            if (self.plot_selection_combo.currentText() == self.plot_selection_combo_list[i]):
                selected_plot_combo = i        

        if (self.wid):
            if (self.wid.isWindow()):
                # close previous instances of child windows to save system memory                
                self.wid.close()                

        if (selected_plot_combo == 0): self.wid = IVBoxPlot(self,self.param_one_combo.currentText())
        elif (selected_plot_combo == 1): self.wid = ViolinPlot(self,self.param_one_combo.currentText())
        elif (selected_plot_combo == 2): self.wid = DistWT(self,self.param_one_combo.currentText())
        elif (selected_plot_combo == 3): self.wid = DistRM(self,self.param_one_combo.currentText())
        elif (selected_plot_combo == 4): self.wid = DistLtoH(self)
        elif (selected_plot_combo == 5): self.wid = IVHistPlot(self) 
        elif (selected_plot_combo == 6): self.wid = DensEta(self) 
        elif (selected_plot_combo == 7): self.wid = IVHistDenPlot(self) 
        elif (selected_plot_combo == 8): self.wid = CorrVocIsc(self)
        elif (selected_plot_combo == 9): self.wid = CorrEtaFF(self)
        elif (selected_plot_combo == 10): self.wid = CorrRshFF(self)
        else: return

        self.wid.show() 
        
        self.statusBar().showMessage(self.tr("Ready"))
        
    def set_default_filters(self):

        self.filter_table_widget.clearContents()

        for i, row in enumerate(self.default_filters):
            for j, column in enumerate(self.default_filters[i]):
                item = QtWidgets.QTableWidgetItem(str(column))
                self.filter_table_widget.setItem(i, j, item)

    def set_user_filters(self):

        self.filter_table_widget.clearContents()

        for i, row in enumerate(self.user_filters_plain_format):
            for j, column in enumerate(self.user_filters_plain_format[i]):
                item = QtWidgets.QTableWidgetItem(str(column))
                self.filter_table_widget.setItem(i, j, item)

    def load_filter_settings(self):

        filename = QtWidgets.QFileDialog.getOpenFileName(self,self.tr("Open file"), self.prev_dir_path, "Filter Settings Files (*.scda)")
        filename = filename[0]
        
        if (not filename):
            return

        try:
            filename.encode('ascii')
        except:
            msg = self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames.")
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), msg) 
            return
        
        self.prev_dir_path = ntpath.dirname(filename)

        try:
            with open(filename,'rb') as f:
                self.user_filters_plain_format = pickle.load(f)
        except:
            msg = self.tr("Could not read file \"" + ntpath.basename(filename) + "\"")
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), msg) 
            return

        self.set_user_filters()
            
        self.statusBar().showMessage(self.tr("New filter settings loaded"))

    def save_filter_settings(self):

        self.read_filter_table()
        self.convert_user_filters()

        filename = QtWidgets.QFileDialog.getSaveFileName(self,self.tr("Save file"), self.prev_dir_path, "Description Files (*.scda)")
        filename = filename[0]
        
        if (not filename):
            return

        try:
            filename.encode('ascii')
        except:
            msg = self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames.")
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), msg) 
            return
        
        self.prev_dir_path = ntpath.dirname(filename)

        try:        
            with open(filename, 'wb') as f:
                pickle.dump(self.user_filters_plain_format, f)
        except:
            msg = self.tr("Could not save file \"" + ntpath.basename(filename) + "\"")
            QtWidgets.QMessageBox.about(self, self.tr("Warning"), msg) 
            return            
            
        self.statusBar().showMessage(self.tr("File saved"))  

    def read_filter_table(self):
        
        self.statusBar().showMessage(self.tr("Checking filters..."))
        self.user_filters = []       
        
        for i in np.arange(0,12):
            # read contents of filter table and skip rows with odd input
            if self.filter_table_widget.item(i,0):
                str_a = self.remove_whitespace(self.filter_table_widget.item(i,0).text())
                if str_a in self.adindex:
                    str_b = self.remove_whitespace(self.filter_table_widget.item(i,1).text())
                    if str_b in ['<','>']:
                        str_c = self.remove_whitespace(self.filter_table_widget.item(i,2).text())
                        if self.is_number(str_c):
                            self.user_filters.append([str_a,str_b,str_c])
        
        # enter checked filters back into table
        for i in np.arange(0,12):
            for j in np.arange(0,3):
                if i < len(self.user_filters):
                    item = QtWidgets.QTableWidgetItem(str(self.user_filters[i][j]))
                    self.filter_table_widget.setItem(i, j, item)
                else:
                    item = QtWidgets.QTableWidgetItem("")
                    self.filter_table_widget.setItem(i, j, item)

        self.statusBar().showMessage(self.tr("Ready"))

    def convert_user_filters(self):
        self.user_filters_plain_format = []
        
        for i, value in enumerate(self.user_filters):
            filter_setting = []
            filter_setting.append(str(self.user_filters[i][0]))
            filter_setting.append(str(self.user_filters[i][1]))
            if (float(self.user_filters[i][2]) % 1 == 0):
                filter_setting.append(int(self.user_filters[i][2]))
            else:                
                filter_setting.append(float(self.user_filters[i][2]))
        
            self.user_filters_plain_format.append(filter_setting)        

    def is_number(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def remove_whitespace(self,s):
        str = s.replace(" ", "")
        str = str.replace("\t", "")
        return str

    def keyPressEvent(self, e):
        if (e.modifiers() & QtCore.Qt.ControlModifier): # Ctrl
            selected = self.filter_table_widget.selectedRanges()
                 
            if e.key() == QtCore.Qt.Key_V: # Paste
                first_row = selected[0].topRow()
                first_col = selected[0].leftColumn()
                 
                #copied text is split by '\n' and '\t' to paste to the cells
                for r, row in enumerate(self.clip.text().split('\n')):
                    for c, text in enumerate(row.split('\t')):
                        if len(text): # fixes bug where elements below pasted element are deleted
                            self.filter_table_widget.setItem(first_row+r, first_col+c, QtWidgets.QTableWidgetItem(text))
 
            elif e.key() == QtCore.Qt.Key_C: # Copy
                s = ""
                for r in range(selected[0].topRow(),selected[0].bottomRow()+1):
                    for c in range(selected[0].leftColumn(),selected[0].rightColumn()+1):
                        try:
                            s += str(self.filter_table_widget.item(r,c).text()) + "\t"
                        except AttributeError:
                            s += "\t"
                    s = s[:-1] + "\n" #eliminate last '\t'
                self.clip.setText(s)

    def set_data_format0(self):
    # defining one function with a numerical argument does not work, strangely
    # it sets the parameter prematurely
        self.label_format = 0
        
        self.statusBar().removeWidget(self.label_text)
        self.label_text = QtWidgets.QLabel("Data label set A")
        self.statusBar().addPermanentWidget(self.label_text)        

    def set_data_format1(self):
        self.label_format = 1

        self.statusBar().removeWidget(self.label_text)        
        self.label_text = QtWidgets.QLabel("Data label set B")      
        self.statusBar().addPermanentWidget(self.label_text)        

    def set_data_format2(self):
        self.label_format = 2

        self.statusBar().removeWidget(self.label_text)        
        self.label_text = QtWidgets.QLabel("Data label set C")  
        self.statusBar().addPermanentWidget(self.label_text)        

    def set_data_format3(self):
        self.label_format = 3

        self.statusBar().removeWidget(self.label_text)        
        self.label_text = QtWidgets.QLabel("Data label set D") 
        self.statusBar().addPermanentWidget(self.label_text)        

    def langKor(self):
        if self.translator:
            QtWidgets.QApplication.removeTranslator(self.translator)
        
        self.translator = QtCore.QTranslator()
        self.translator.load(":IVMain_kr.qm")
        QtWidgets.QApplication.installTranslator(self.translator)

        self.menuBar().clear()
        self.create_menu()        
        self.main_frame.deleteLater()       
        self.create_main_frame()

    def langChin(self):
        if self.translator:
            QtWidgets.QApplication.removeTranslator(self.translator)
        
        self.translator = QtCore.QTranslator()
        self.translator.load(":IVMain_cn.qm")
        QtWidgets.QApplication.installTranslator(self.translator)

        self.menuBar().clear()
        self.create_menu()        
        self.main_frame.deleteLater()       
        self.create_main_frame()

    def langEngl(self):
        if self.translator:
            QtWidgets.QApplication.removeTranslator(self.translator)

        self.menuBar().clear()
        self.create_menu()        
        self.main_frame.deleteLater()        
        self.create_main_frame()

    def open_help_dialog(self):
        help_dialog = HelpDialog(self)
        help_dialog.setModal(True)
        help_dialog.show()

    def on_about(self):
        msg = self.tr("Solar cell data analysis\nAuthor: Ronald Naber\nLicense: Public domain")
        QtWidgets.QMessageBox.about(self, self.tr("About the application"), msg)
    
    def create_main_frame(self):
        self.setWindowTitle(self.tr("Solar cell data analysis")) # do this again so that translator can catch it
        self.main_frame = QtWidgets.QWidget()        

        ##### left vbox #####     
        self.series_list_view = QtWidgets.QTreeView()
        self.series_list_view.setModel(self.series_list_model)
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        self.series_list_view.setRootIsDecorated(False)
        self.series_list_view.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.series_list_view.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        open_files_button = QtWidgets.QPushButton()
        open_files_button.clicked.connect(self.load_file)
        open_files_button.setIcon(QtGui.QIcon(":open.png"))
        open_files_button.setToolTip(self.tr("Load files"))
        open_files_button.setStatusTip(self.tr("Load files"))

        save_files_button = QtWidgets.QPushButton()
        save_files_button.clicked.connect(self.save_files)        
        save_files_button.setIcon(QtGui.QIcon(":save.png"))
        save_files_button.setToolTip(self.tr("Save files"))
        save_files_button.setStatusTip(self.tr("Save files"))
        
        combine_data_button = QtWidgets.QPushButton()
        combine_data_button.clicked.connect(self.combine_datasets)
        combine_data_button.setIcon(QtGui.QIcon(":combine.png"))
        combine_data_button.setToolTip(self.tr("Combine data sets"))
        combine_data_button.setStatusTip(self.tr("Combine data sets"))

        clear_data_button = QtWidgets.QPushButton()
        clear_data_button.clicked.connect(self.clear_data)
        clear_data_button.setIcon(QtGui.QIcon(":erase.png"))
        clear_data_button.setToolTip(self.tr("Remove all data sets"))
        clear_data_button.setStatusTip(self.tr("Remove all data sets"))

        buttonbox0 = QtWidgets.QDialogButtonBox()
        buttonbox0.addButton(open_files_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox0.addButton(save_files_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox0.addButton(combine_data_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox0.addButton(clear_data_button, QtWidgets.QDialogButtonBox.ActionRole)

        left_vbox = QtWidgets.QVBoxLayout()
        left_vbox.addWidget(self.series_list_view)
        left_vbox.addWidget(buttonbox0)

        ##### middle vbox #####
        self.filter_table_widget.setRowCount(12)
        self.filter_table_widget.setColumnCount(3)
        self.filter_table_widget.setHorizontalHeaderLabels((self.tr('Parameter'),self.tr('< or >'),self.tr('Number')))
        self.filter_table_widget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.filter_table_widget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)       
        
        open_filters_button = QtWidgets.QPushButton()
        open_filters_button.clicked.connect(self.load_filter_settings)
        open_filters_button.setIcon(QtGui.QIcon(":open.png"))
        open_filters_button.setToolTip(self.tr("Load filter settings"))
        open_filters_button.setStatusTip(self.tr("Load filter settings"))

        save_filters_button = QtWidgets.QPushButton()
        save_filters_button.clicked.connect(self.save_filter_settings)        
        save_filters_button.setIcon(QtGui.QIcon(":save.png"))
        save_filters_button.setToolTip(self.tr("Save filter settings"))
        save_filters_button.setStatusTip(self.tr("Save filter settings"))        

        check_filters_button = QtWidgets.QPushButton()
        check_filters_button.clicked.connect(self.read_filter_table) 
        check_filters_button.setIcon(QtGui.QIcon(":check.png"))
        check_filters_button.setToolTip(self.tr("Check filters"))
        check_filters_button.setStatusTip(self.tr("Check filters"))
        
        execute_filters_button = QtWidgets.QPushButton()
        execute_filters_button.clicked.connect(self.filter_data) 
        execute_filters_button.setIcon(QtGui.QIcon(":filter.png"))
        execute_filters_button.setToolTip(self.tr("Execute filters"))
        execute_filters_button.setStatusTip(self.tr("Execute filters"))

        default_filters_button = QtWidgets.QPushButton()
        default_filters_button.clicked.connect(self.set_default_filters)
        default_filters_button.setIcon(QtGui.QIcon(":revert.png"))
        default_filters_button.setToolTip(self.tr("Reload default filters"))
        default_filters_button.setStatusTip(self.tr("Reload default filters"))

        buttonbox1 = QtWidgets.QDialogButtonBox()
        buttonbox1.addButton(open_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox1.addButton(save_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox1.addButton(check_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox1.addButton(execute_filters_button, QtWidgets.QDialogButtonBox.ActionRole)
        buttonbox1.addButton(default_filters_button, QtWidgets.QDialogButtonBox.ActionRole)

        mid_vbox = QtWidgets.QVBoxLayout()
        mid_vbox.addWidget(self.filter_table_widget)                                                                                                                                                                                                           
        mid_vbox.addWidget(buttonbox1) 
        
        ##### top buttonbox #####
        report_button = QtWidgets.QPushButton()
        report_button.clicked.connect(self.make_report)
        report_button.setIcon(QtGui.QIcon(":report.png"))
        report_button.setToolTip(self.tr("Make report"))
        report_button.setStatusTip(self.tr("Make report"))

        openreport_button = QtWidgets.QPushButton()
        openreport_button.clicked.connect(self.open_report)
        openreport_button.setIcon(QtGui.QIcon(":link.png"))
        openreport_button.setToolTip(self.tr("Open report"))
        openreport_button.setStatusTip(self.tr("Open report"))

        plotselection_button = QtWidgets.QPushButton()
        plotselection_button.clicked.connect(self.open_plot_selection)
        plotselection_button.setIcon(QtGui.QIcon(":chart.png"))
        plotselection_button.setToolTip(self.tr("Plot selection"))
        plotselection_button.setStatusTip(self.tr("Plot selection"))

        top_buttonbox = QtWidgets.QDialogButtonBox()
        top_buttonbox.addButton(report_button, QtWidgets.QDialogButtonBox.ActionRole)
        top_buttonbox.addButton(openreport_button, QtWidgets.QDialogButtonBox.ActionRole)
        top_buttonbox.addButton(plotselection_button, QtWidgets.QDialogButtonBox.ActionRole)

        for i in self.plot_selection_list:
            self.param_one_combo.addItem(i)               
        self.param_one_combo.setCurrentIndex(4)

        for i in self.plot_selection_combo_list:
            self.plot_selection_combo.addItem(i)
        
        toolbar_hbox = QtWidgets.QHBoxLayout()
        toolbar_hbox.addWidget(top_buttonbox)
        toolbar_hbox.addWidget(self.param_one_combo) 
        toolbar_hbox.addWidget(self.plot_selection_combo)

        ##### main layout settings #####
        top_hbox = QtWidgets.QHBoxLayout()
        top_hbox.addLayout(left_vbox)
        top_hbox.addLayout(mid_vbox)
  
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(toolbar_hbox) 
        vbox.addLayout(top_hbox)           
                                       
        self.main_frame.setLayout(vbox)

        self.setCentralWidget(self.main_frame)
        
        self.statusBar().addWidget(self.status_text,1)
        
        if self.first_run:
            # need to remove it when changing language as this calls this function again
            self.statusBar().removeWidget(self.label_text)
            self.first_run = False
            
        self.statusBar().addPermanentWidget(self.label_text)

    def create_menu(self):
        self.file_menu = self.menuBar().addMenu(self.tr("File"))

        tip = self.tr("Open file")        
        load_action = QtWidgets.QAction(self.tr("Open..."), self)
        load_action.setIcon(QtGui.QIcon(":open.png"))
        load_action.triggered.connect(self.load_file) 
        load_action.setToolTip(tip)
        load_action.setStatusTip(tip)
        load_action.setShortcut('Ctrl+O')    

        tip = self.tr("Quit")        
        quit_action = QtWidgets.QAction(self.tr("Quit"), self)
        quit_action.setIcon(QtGui.QIcon(":quit.png"))
        quit_action.triggered.connect(self.close) 
        quit_action.setToolTip(tip)
        quit_action.setStatusTip(tip)
        quit_action.setShortcut('Ctrl+Q')

        self.file_menu.addAction(load_action)       
        self.file_menu.addAction(quit_action)

        self.edit_menu = self.menuBar().addMenu(self.tr("Data labels"))

        tip = "Uoc,Isc,RserLfDfIEC,Rsh,FF,Eta,IRev1"
        format_action0 = QtWidgets.QAction(self.tr("Custom labels") + " A", self)
        format_action0.setIcon(QtGui.QIcon(":label.png"))
        format_action0.triggered.connect(self.set_data_format0)         
        format_action0.setToolTip(tip)
        format_action0.setStatusTip(tip)
        
        tip = "Uoc0,Isc0,Rseries_multi_level,Rshunt_SC,Fill0*100,Eff0*100,Ireverse_2"
        format_action1 = QtWidgets.QAction(self.tr("Custom labels") + " B", self)
        format_action1.setIcon(QtGui.QIcon(":label.png"))
        format_action1.triggered.connect(self.set_data_format1)
        format_action1.setToolTip(tip)
        format_action1.setStatusTip(tip)      

        tip = "Uoc,Isc,RserIEC891,RshuntDfDr,FF,Eta,IRev1"
        format_action2 = QtWidgets.QAction(self.tr("Custom labels") + " C", self)
        format_action2.setIcon(QtGui.QIcon(":label.png"))
        format_action2.triggered.connect(self.set_data_format2) 
        format_action2.setToolTip(tip)
        format_action2.setStatusTip(tip)

        tip = "Uoc,Isc,Rs,Rsh,FF,NCell*100,Irev2"
        format_action3 = QtWidgets.QAction(self.tr("Custom labels") + " D", self)
        format_action3.setIcon(QtGui.QIcon(":label.png"))
        format_action3.triggered.connect(self.set_data_format3) 
        format_action3.setToolTip(tip)
        format_action3.setStatusTip(tip)

        self.edit_menu.addAction(format_action0)        
        self.edit_menu.addAction(format_action1)
        self.edit_menu.addAction(format_action2)
        self.edit_menu.addAction(format_action3)        

        self.lang_menu = self.menuBar().addMenu(self.tr("Language"))
        
        tip = self.tr("Switch to Chinese language")
        cn_action = QtWidgets.QAction(self.tr("Chinese"), self)
        cn_action.setIcon(QtGui.QIcon(":lang.png"))
        cn_action.triggered.connect(self.langChin)        
        cn_action.setToolTip(tip)
        cn_action.setStatusTip(tip)       

        tip = self.tr("Switch to Korean language")
        kr_action = QtWidgets.QAction(self.tr("Korean"), self)
        kr_action.setIcon(QtGui.QIcon(":lang.png"))
        kr_action.triggered.connect(self.langKor)
        kr_action.setToolTip(tip)
        kr_action.setStatusTip(tip)  

        tip = self.tr("Switch to English language")
        en_action = QtWidgets.QAction(self.tr("English"), self)
        en_action.setIcon(QtGui.QIcon(":lang.png"))
        en_action.triggered.connect(self.langEngl)
        en_action.setToolTip(tip)
        en_action.setStatusTip(tip) 

        self.lang_menu.addAction(cn_action)
        self.lang_menu.addAction(kr_action)
        self.lang_menu.addAction(en_action)

        self.help_menu = self.menuBar().addMenu(self.tr("Help"))

        tip = self.tr("Help information")        
        help_action = QtWidgets.QAction(self.tr("Help..."), self)
        help_action.setIcon(QtGui.QIcon(":help.png"))
        help_action.triggered.connect(self.open_help_dialog)         
        help_action.setToolTip(tip)
        help_action.setStatusTip(tip)
        help_action.setShortcut('H')

        tip = self.tr("About the application")
        about_action = QtWidgets.QAction(self.tr("About..."), self)
        about_action.setIcon(QtGui.QIcon(":info.png"))
        about_action.triggered.connect(self.on_about)
        about_action.setToolTip(tip)
        about_action.setStatusTip(tip)
        about_action.setShortcut('F1')

        self.help_menu.addAction(help_action)
        self.help_menu.addAction(about_action)