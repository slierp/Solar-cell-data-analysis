# -*- coding: utf-8 -*-
from __future__ import division
import numpy as np
import pandas as pd
import os, ntpath, pickle
from HelpDialog import HelpDialog
from PyQt4 import QtCore, QtGui
from IVMainPlot import CorrVocIsc, CorrEtaFF, CorrRshFF, DistLtoH, DensEta, DistWT, DistRM, IVBoxPlot, IVHistPlot, IVHistDenPlot      

        # To be implemented
        #for i in self.ad:
            # Export all filtered IV data to existing csv files - THIS WILL OVERWRITE YOUR EXISTING FILES
        #    filename = self.ad[i].index.name + '.csv'
        #    self.ad[i].to_csv(filename, index=False)

class IVMainGui(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(IVMainGui, self).__init__(parent)
        self.setWindowTitle(self.tr("SCiDA Pro"))
        self.setWindowIcon(QtGui.QIcon(":ScidaPro_icon.png"))
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint) # DISABLE BEFORE RELEASE

        ### Set initial geometry and center the window on the screen ###
        self.resize(1024, 576)
        frameGm = self.frameGeometry()
        centerPoint = QtGui.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft()) 

        ### Set default font size ###
        self.setStyleSheet('font-size: 12pt;')  

        self.clip = QtGui.QApplication.clipboard()
        self.series_list_model = QtGui.QStandardItemModel()
        self.filter_table_widget = QtGui.QTableWidget()
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
        self.prev_dir_path = ""
        self.wid = None
        
        self.create_menu()
        self.create_main_frame()
        self.set_default_filters()      

    def load_file(self, filename=None):   

        fileNames = QtGui.QFileDialog.getOpenFileNames(self,self.tr("Load files"), self.prev_dir_path, "Excel Files (*.csv)")
        empty_data_warning = False
        non_ascii_warning = False

        num = len(self.ad)
        for filename in fileNames:
            # Read all .csv files and insert selected columns into ad
            # Purge rows with empty or negative elements
            # Enter new data set names into ad and series list

            # Check for non-ASCII filenames, give warning and skip loading such files
            try: # try qstring first (windows)
                if not os.path.isfile(filename.toLatin1()):
                    non_ascii_warning = True
                    continue
            except AttributeError: # try unicode second (linux)
                if not os.path.isfile(filename.encode('ascii', 'ignore')):
                    non_ascii_warning = True
                    continue

            # Set working directory so that user can remain where they are
            self.prev_dir_path = ntpath.dirname(str(filename))

            # Try to load file and give error message if label format is not recognized
            try:
                self.ad[num] = pd.read_csv(str(filename))[self.label_formats[self.label_format]].dropna()
            except KeyError:
                try:
                    self.ad[num] = pd.read_csv(str(filename),sep=';')[self.label_formats[self.label_format]].dropna()
                except KeyError:
                    msg = self.tr("Error while reading data files.\n\nData labels were perhaps not recognized.")
                    QtGui.QMessageBox.about(self, self.tr("Warning"), msg) 

            # Try to apply default labels to columns; skip current file if unsuccessful
            try:
                self.ad[num].columns = self.label_formats[0]
            except KeyError:
                continue
            
            # Convert to numeric values if needed, reset size of ad
            self.ad[num] = self.ad[num].convert_objects(convert_numeric=True)
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
            str_a = ntpath.basename(str(filename)[0:-4])            
            self.ad[num].index.name = str_a[0:19] # data set name limited to 20 characters
            item = QtGui.QStandardItem(str_a[0:19])
            font = item.font()
            font.setBold(1)
            item.setFont(font)
            self.series_list_model.appendRow(item)                        
            num += 1

        if empty_data_warning:
            msg = self.tr("Empty data sets were found.\n\nThe application only accepts data entries with a value for Voc, Isc, FF, Eta, Rser, Rsh and Irev. All values also need to be non-negative.")
            QtGui.QMessageBox.about(self, self.tr("Warning"), msg)
            
        if non_ascii_warning:
            msg = self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames.")
            QtGui.QMessageBox.about(self, self.tr("Warning"), msg)            
                              
        if self.ad:
            self.statusBar().showMessage(self.tr("Ready"))
        else:
            self.statusBar().showMessage(self.tr("Please load data files"))

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
            self.reportname = QtGui.QFileDialog.getSaveFileName(self,self.tr("Save file"), self.prev_dir_path, "Excel Files (*.xlsx)")
            if self.reportname:
                self.statusBar().showMessage(self.tr("Making an Excel report..."))
            else:
                return
        else:
            self.statusBar().showMessage(self.tr("Please load data files"))
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

            self.smr[i1] = self.smr[i1].convert_objects(convert_numeric=True)
            self.smr[i1].iloc[:,2] = self.smr[i1].iloc[:,2]*1000
            self.smr[i1].iloc[:,3] = self.smr[i1].iloc[:,3]/1000
    
            roundinglist = [3,2,2,2,1,2,2]
    
            for i3, value in enumerate(roundinglist):
                self.smr[i1].iloc[:,i3] = np.round(self.smr[i1].iloc[:,i3],decimals=value)                                                                                                                                                 

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

            self.yloutput[i]['Data set'] = self.ad[i].index.name + ' (' + repr(self.yloutput[i].index.name) + ' cells)'
            self.yloutput[i].index.name = 'Data property'
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

        writer = pd.ExcelWriter(str(self.reportname), engine='xlsxwriter')
            
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
        
        if len(str(self.reportname)):
            self.statusBar().showMessage(self.tr("Opening report..."))
            if str(self.reportname)[0] != '/': # windows
                str_a = 'file:///' + str(self.reportname)
            else: # linux
                str_a = 'file://' + str(self.reportname)
            
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(str_a, QtCore.QUrl.StrictMode)) # Strict mode necessary for linux compatibility (spaces > %20) 
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
        elif (selected_plot_combo == 1): self.wid = DistWT(self,self.param_one_combo.currentText())
        elif (selected_plot_combo == 2): self.wid = DistRM(self,self.param_one_combo.currentText())
        elif (selected_plot_combo == 3): self.wid = DistLtoH(self)
        elif (selected_plot_combo == 4): self.wid = IVHistPlot(self) 
        elif (selected_plot_combo == 5): self.wid = DensEta(self) 
        elif (selected_plot_combo == 6): self.wid = IVHistDenPlot(self) 
        elif (selected_plot_combo == 7): self.wid = CorrVocIsc(self)
        elif (selected_plot_combo == 8): self.wid = CorrEtaFF(self)
        elif (selected_plot_combo == 9): self.wid = CorrRshFF(self)
        else: return
                        
        self.wid.show() 
        
        self.statusBar().showMessage(self.tr("Ready"))
        
    def set_default_filters(self):

        self.filter_table_widget.clearContents()

        for i, row in enumerate(self.default_filters):
            for j, column in enumerate(self.default_filters[i]):
                item = QtGui.QTableWidgetItem(str(column))
                self.filter_table_widget.setItem(i, j, item)

    def set_user_filters(self):

        self.filter_table_widget.clearContents()

        for i, row in enumerate(self.user_filters_plain_format):
            for j, column in enumerate(self.user_filters_plain_format[i]):
                item = QtGui.QTableWidgetItem(str(column))
                self.filter_table_widget.setItem(i, j, item)

    def load_filter_settings(self):

        filename = QtGui.QFileDialog.getOpenFileName(self,self.tr("Open file"), self.prev_dir_path, "Filter Settings Files (*.scda)")
        
        if (not filename):
            return

        if (not os.path.isfile(filename.toAscii())):
            msg = self.tr("Filenames with non-ASCII characters were found.\n\nThe application currently only supports ASCII filenames.")
            QtGui.QMessageBox.about(self, self.tr("Warning"), msg) 
            return
        
        self.prev_dir_path = ntpath.dirname(str(filename))
        
        with open(str(filename)) as f:
            self.user_filters_plain_format = pickle.load(f)

        self.set_user_filters()
            
        self.statusBar().showMessage(self.tr("New filter settings loaded"))

    def save_filter_settings(self):

        self.read_filter_table()
        self.convert_user_filters()

        filename = QtGui.QFileDialog.getSaveFileName(self,self.tr("Save file"), self.prev_dir_path, "Description Files (*.scda)")
        
        if (not filename):
            return

        # Check for non-ASCII here does not seem to work
        
        self.prev_dir_path = ntpath.dirname(str(filename))
        
        with open(str(filename), 'w') as f:
            pickle.dump(self.user_filters_plain_format, f)
            
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
                    item = QtGui.QTableWidgetItem(str(self.user_filters[i][j]))
                    self.filter_table_widget.setItem(i, j, item)
                else:
                    item = QtGui.QTableWidgetItem("")
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
                            self.filter_table_widget.setItem(first_row+r, first_col+c, QtGui.QTableWidgetItem(text))
 
            elif e.key() == QtCore.Qt.Key_C: # Copy
                s = ""
                for r in xrange(selected[0].topRow(),selected[0].bottomRow()+1):
                    for c in xrange(selected[0].leftColumn(),selected[0].rightColumn()+1):
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

    def set_data_format1(self):
        self.label_format = 1

    def set_data_format2(self):
        self.label_format = 2

    def set_data_format3(self):
        self.label_format = 3

    def langKor(self):
        if self.translator:
            QtGui.QApplication.removeTranslator(self.translator)
        
        self.translator = QtCore.QTranslator()
        self.translator.load(":IVMain_kr.qm")
        QtGui.QApplication.installTranslator(self.translator)

        self.menuBar().clear()
        self.create_menu()        
        self.main_frame.deleteLater()       
        self.create_main_frame()

    def langChin(self):
        if self.translator:
            QtGui.QApplication.removeTranslator(self.translator)
        
        self.translator = QtCore.QTranslator()
        self.translator.load(":IVMain_cn.qm")
        QtGui.QApplication.installTranslator(self.translator)

        self.menuBar().clear()
        self.create_menu()        
        self.main_frame.deleteLater()       
        self.create_main_frame()

    def langEngl(self):
        if self.translator:
            QtGui.QApplication.removeTranslator(self.translator)

        self.menuBar().clear()
        self.create_menu()        
        self.main_frame.deleteLater()        
        self.create_main_frame()

    def open_help_dialog(self):
        help_dialog = HelpDialog(self)
        help_dialog.setModal(True)
        help_dialog.show()

    def on_about(self):
        msg = self.tr("Solar cell data analysis\nAuthor: Ronald Naber\nContact: rnaber (AT) tempress (DOT) nl\nLicense: Public domain")
        QtGui.QMessageBox.about(self, self.tr("About the application"), msg)
    
    def create_main_frame(self):
        self.setWindowTitle(self.tr("Solar cell data analysis")) # do this again so that translator can catch it
        self.main_frame = QtGui.QWidget()        

        ##### left vbox #####     
        self.series_list_view = QtGui.QTreeView()
        self.series_list_view.setModel(self.series_list_model)
        self.series_list_model.setHorizontalHeaderLabels([self.tr('Data series')])
        self.series_list_view.setRootIsDecorated(False)
        self.series_list_view.setDragDropMode(QtGui.QAbstractItemView.NoDragDrop)
        self.series_list_view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.series_list_view.setSelectionMode(QtGui.QAbstractItemView.NoSelection)

        open_files_button = QtGui.QPushButton()
        open_files_button.clicked.connect(self.load_file)
        open_files_button.setIcon(QtGui.QIcon(":open.png"))
        open_files_button.setToolTip(self.tr("Load files"))
        open_files_button.setStatusTip(self.tr("Load files"))

        # To be implemented
        #save_files_button = QtGui.QPushButton()
        #self.connect(save_files_button, QtCore.SIGNAL('clicked()'), self.load_file)
        #save_files_button.setIcon(QtGui.QIcon(":save.png"))
        #save_files_button.setToolTip(self.tr("Save files"))
        #save_files_button.setStatusTip(self.tr("Save files"))
        
        combine_data_button = QtGui.QPushButton()
        self.connect(combine_data_button, QtCore.SIGNAL('clicked()'), self.combine_datasets)
        combine_data_button.clicked.connect(self.combine_datasets)
        combine_data_button.setIcon(QtGui.QIcon(":combine.png"))
        combine_data_button.setToolTip(self.tr("Combine data sets"))
        combine_data_button.setStatusTip(self.tr("Combine data sets"))        

        clear_data_button = QtGui.QPushButton()
        clear_data_button.clicked.connect(self.clear_data)
        clear_data_button.setIcon(QtGui.QIcon(":erase.png"))
        clear_data_button.setToolTip(self.tr("Remove all data sets"))
        clear_data_button.setStatusTip(self.tr("Remove all data sets"))

        buttonbox0 = QtGui.QDialogButtonBox()
        buttonbox0.addButton(open_files_button, QtGui.QDialogButtonBox.ActionRole)
        #buttonbox0.addButton(save_files_button, QtGui.QDialogButtonBox.ActionRole)
        buttonbox0.addButton(combine_data_button, QtGui.QDialogButtonBox.ActionRole)
        buttonbox0.addButton(clear_data_button, QtGui.QDialogButtonBox.ActionRole)

        left_vbox = QtGui.QVBoxLayout()
        left_vbox.addWidget(self.series_list_view)
        left_vbox.addWidget(buttonbox0)

        ##### middle vbox #####
        self.filter_table_widget.setRowCount(12)
        self.filter_table_widget.setColumnCount(3)
        self.filter_table_widget.setHorizontalHeaderLabels((self.tr('Parameter'),self.tr('< or >'),self.tr('Number')))
        self.filter_table_widget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.filter_table_widget.verticalHeader().setResizeMode(QtGui.QHeaderView.Stretch)       
        
        open_filters_button = QtGui.QPushButton()
        open_filters_button.clicked.connect(self.load_filter_settings)
        open_filters_button.setIcon(QtGui.QIcon(":open.png"))
        open_filters_button.setToolTip(self.tr("Load filter settings"))
        open_filters_button.setStatusTip(self.tr("Load filter settings"))

        save_filters_button = QtGui.QPushButton()
        save_filters_button.clicked.connect(self.save_filter_settings)        
        save_filters_button.setIcon(QtGui.QIcon(":save.png"))
        save_filters_button.setToolTip(self.tr("Save filter settings"))
        save_filters_button.setStatusTip(self.tr("Save filter settings"))        

        check_filters_button = QtGui.QPushButton()
        check_filters_button.clicked.connect(self.read_filter_table) 
        check_filters_button.setIcon(QtGui.QIcon(":check.png"))
        check_filters_button.setToolTip(self.tr("Check filters"))
        check_filters_button.setStatusTip(self.tr("Check filters"))
        
        execute_filters_button = QtGui.QPushButton()
        execute_filters_button.clicked.connect(self.filter_data) 
        execute_filters_button.setIcon(QtGui.QIcon(":filter.png"))
        execute_filters_button.setToolTip(self.tr("Execute filters"))
        execute_filters_button.setStatusTip(self.tr("Execute filters"))

        default_filters_button = QtGui.QPushButton()
        default_filters_button.clicked.connect(self.set_default_filters)
        default_filters_button.setIcon(QtGui.QIcon(":revert.png"))
        default_filters_button.setToolTip(self.tr("Reload default filters"))
        default_filters_button.setStatusTip(self.tr("Reload default filters"))

        buttonbox1 = QtGui.QDialogButtonBox()
        buttonbox1.addButton(open_filters_button, QtGui.QDialogButtonBox.ActionRole)
        buttonbox1.addButton(save_filters_button, QtGui.QDialogButtonBox.ActionRole)
        buttonbox1.addButton(check_filters_button, QtGui.QDialogButtonBox.ActionRole)
        buttonbox1.addButton(execute_filters_button, QtGui.QDialogButtonBox.ActionRole)
        buttonbox1.addButton(default_filters_button, QtGui.QDialogButtonBox.ActionRole)

        mid_vbox = QtGui.QVBoxLayout()
        mid_vbox.addWidget(self.filter_table_widget)                                                                                                                                                                                                           
        mid_vbox.addWidget(buttonbox1) 
        
        ##### top buttonbox #####
        report_button = QtGui.QPushButton()
        report_button.clicked.connect(self.make_report)
        report_button.setIcon(QtGui.QIcon(":report.png"))
        report_button.setToolTip(self.tr("Make report"))
        report_button.setStatusTip(self.tr("Make report"))

        openreport_button = QtGui.QPushButton()
        openreport_button.clicked.connect(self.open_report)
        openreport_button.setIcon(QtGui.QIcon(":link.png"))
        openreport_button.setToolTip(self.tr("Open report"))
        openreport_button.setStatusTip(self.tr("Open report"))

        plotselection_button = QtGui.QPushButton()
        plotselection_button.clicked.connect(self.open_plot_selection)
        plotselection_button.setIcon(QtGui.QIcon(":chart.png"))
        plotselection_button.setToolTip(self.tr("Plot selection"))
        plotselection_button.setStatusTip(self.tr("Plot selection"))

        top_buttonbox = QtGui.QDialogButtonBox()
        top_buttonbox.addButton(report_button, QtGui.QDialogButtonBox.ActionRole)
        top_buttonbox.addButton(openreport_button, QtGui.QDialogButtonBox.ActionRole)
        top_buttonbox.addButton(plotselection_button, QtGui.QDialogButtonBox.ActionRole)

        self.plot_selection_combo_list = []
        self.plot_selection_combo_list.append(self.tr('Boxplot'))
        self.plot_selection_combo_list.append(self.tr('Walk-through'))
        self.plot_selection_combo_list.append(self.tr('Rolling mean'))
        self.plot_selection_combo_list.append(self.tr('Low to high'))
        self.plot_selection_combo_list.append(self.tr('Histogram'))
        self.plot_selection_combo_list.append(self.tr('Density'))
        self.plot_selection_combo_list.append(self.tr('Histogram + density'))
        self.plot_selection_combo_list.append(self.tr('Voc-Isc'))
        self.plot_selection_combo_list.append(self.tr('Eta-FF'))
        self.plot_selection_combo_list.append(self.tr('Rsh-FF'))

        self.param_one_combo = QtGui.QComboBox(self)
        for i in self.plot_selection_list:
            self.param_one_combo.addItem(i)               
        self.param_one_combo.setCurrentIndex(4)

        self.plot_selection_combo = QtGui.QComboBox(self)
        for i in self.plot_selection_combo_list:
            self.plot_selection_combo.addItem(i)
        
        toolbar_hbox = QtGui.QHBoxLayout()
        toolbar_hbox.addWidget(top_buttonbox)
        toolbar_hbox.addWidget(self.param_one_combo) 
        toolbar_hbox.addWidget(self.plot_selection_combo)

        ##### main layout settings #####
        top_hbox = QtGui.QHBoxLayout()
        top_hbox.addLayout(left_vbox)
        top_hbox.addLayout(mid_vbox)
  
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(toolbar_hbox) 
        vbox.addLayout(top_hbox)           
                                       
        self.main_frame.setLayout(vbox)

        self.setCentralWidget(self.main_frame)

        self.status_text = QtGui.QLabel("")        
        self.statusBar().addWidget(self.status_text,1)
        self.statusBar().showMessage(self.tr("Please load data files"))

    def create_menu(self):
        self.file_menu = self.menuBar().addMenu(self.tr("File"))

        tip = self.tr("Open file")        
        load_action = QtGui.QAction(self.tr("Open..."), self)
        load_action.setIcon(QtGui.QIcon(":open.png"))
        load_action.triggered.connect(self.load_file) 
        load_action.setToolTip(tip)
        load_action.setStatusTip(tip)
        load_action.setShortcut('Ctrl+O')    

        tip = self.tr("Quit")        
        quit_action = QtGui.QAction(self.tr("Quit"), self)
        quit_action.setIcon(QtGui.QIcon(":quit.png"))
        quit_action.triggered.connect(self.close) 
        quit_action.setToolTip(tip)
        quit_action.setStatusTip(tip)
        quit_action.setShortcut('Ctrl+Q')

        self.file_menu.addAction(load_action)       
        self.file_menu.addAction(quit_action)

        self.edit_menu = self.menuBar().addMenu(self.tr("Data labels"))
        
        tip = "Uoc0,Isc0,Rseries_multi_level,Rshunt_SC,Fill0*100,Eff0*100,Ireverse_2"
        format_action1 = QtGui.QAction(self.tr("Custom labels") + " D", self)
        format_action1.setIcon(QtGui.QIcon(":label.png"))
        format_action1.triggered.connect(self.set_data_format1)
        format_action1.setToolTip(tip)
        format_action1.setStatusTip(tip)      

        tip = "Uoc,Isc,RserIEC891,RshuntDfDr,FF,Eta,IRev1"
        format_action2 = QtGui.QAction(self.tr("Custom labels") + " C", self)
        format_action2.setIcon(QtGui.QIcon(":label.png"))
        format_action2.triggered.connect(self.set_data_format2) 
        format_action2.setToolTip(tip)
        format_action2.setStatusTip(tip)

        tip = "Uoc,Isc,Rs,Rsh,FF,NCell*100,Irev2"
        format_action3 = QtGui.QAction(self.tr("Custom labels") + " B", self)
        format_action3.setIcon(QtGui.QIcon(":label.png"))
        format_action3.triggered.connect(self.set_data_format3) 
        format_action3.setToolTip(tip)
        format_action3.setStatusTip(tip)

        tip = "Uoc,Isc,RserLfDfIEC,Rsh,FF,Eta,IRev1"
        format_action0 = QtGui.QAction(self.tr("Custom labels") + " A", self)
        format_action0.setIcon(QtGui.QIcon(":label.png"))
        format_action0.triggered.connect(self.set_data_format0)         
        format_action0.setToolTip(tip)
        format_action0.setStatusTip(tip)
        
        self.edit_menu.addAction(format_action1)
        self.edit_menu.addAction(format_action2)
        self.edit_menu.addAction(format_action3)        
        self.edit_menu.addAction(format_action0)

        self.lang_menu = self.menuBar().addMenu(self.tr("Language"))
        
        tip = self.tr("Switch to Chinese language")
        cn_action = QtGui.QAction(self.tr("Chinese"), self)
        cn_action.setIcon(QtGui.QIcon(":lang.png"))
        cn_action.triggered.connect(self.langChin)        
        cn_action.setToolTip(tip)
        cn_action.setStatusTip(tip)       

        tip = self.tr("Switch to Korean language")
        kr_action = QtGui.QAction(self.tr("Korean"), self)
        kr_action.setIcon(QtGui.QIcon(":lang.png"))
        kr_action.triggered.connect(self.langKor)
        kr_action.setToolTip(tip)
        kr_action.setStatusTip(tip)  

        tip = self.tr("Switch to English language")
        en_action = QtGui.QAction(self.tr("English"), self)
        en_action.setIcon(QtGui.QIcon(":lang.png"))
        en_action.triggered.connect(self.langEngl)
        en_action.setToolTip(tip)
        en_action.setStatusTip(tip) 

        self.lang_menu.addAction(cn_action)
        self.lang_menu.addAction(kr_action)
        self.lang_menu.addAction(en_action)

        self.help_menu = self.menuBar().addMenu(self.tr("Help"))

        tip = self.tr("Help information")        
        help_action = QtGui.QAction(self.tr("Help..."), self)
        help_action.setIcon(QtGui.QIcon(":help.png"))
        help_action.triggered.connect(self.open_help_dialog)         
        help_action.setToolTip(tip)
        help_action.setStatusTip(tip)
        help_action.setShortcut('H')

        tip = self.tr("About the application")
        about_action = QtGui.QAction(self.tr("About..."), self)
        about_action.setIcon(QtGui.QIcon(":info.png"))
        about_action.triggered.connect(self.on_about)
        about_action.setToolTip(tip)
        about_action.setStatusTip(tip)
        about_action.setShortcut('F1')

        self.help_menu.addAction(help_action)
        self.help_menu.addAction(about_action)