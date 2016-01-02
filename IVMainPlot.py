from __future__ import division
import numpy as np
import pandas as pd
import matplotlib, Tkinter, FileDialog
import matplotlib.pyplot as plt
from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams
from PlotSettingsDialog import PlotSettingsDialog
rcParams.update({'figure.autolayout': True})

font = {'family' : 'sans-serif',
        'size'   : 14}

matplotlib.rc('font', **font)

cl = ['#4F81BD', '#C0504D', '#9BBB59','#F79646','#8064A2','#4BACC6','0','0.5'] # colour

plot_selection_list = ['Uoc','Isc','Voc*Isc','FF','Eta','RserLfDfIEC','Rsh','IRev1']
irev_axis_label = r'$\mathrm{\mathsf{I_{REV}\ [A]}}$'
rser_axis_label = r'$\mathrm{\mathsf{R_{SERIES}\ [mOhm \cdot cm^{2}]}}$'
rshunt_axis_label = r'$\mathrm{\mathsf{R_{SHUNT}\ [kOhm]}}$'
eta_axis_label = r'$\mathrm{\mathsf{Eta\ [\%]}}$'
voc_axis_label = r'$\mathrm{\mathsf{V_{OC}\ [V]}}$'
isc_axis_label = r'$\mathrm{\mathsf{I_{SC}\ [A]}}$'
ff_axis_label = r'$\mathrm{\mathsf{FF\ [\%]}}$'
vocisc_axis_label = r'$\mathrm{\mathsf{V_{OC}\ *\ I_{SC}\ [V*A]}}$'
plot_label_list = [voc_axis_label, isc_axis_label, vocisc_axis_label, ff_axis_label, eta_axis_label, rser_axis_label, rshunt_axis_label, irev_axis_label]

########## Main class - only for inheriting ##########

class IVMainPlot(QtGui.QMainWindow):  
    
    def __init__(self, parent=None):
        pass          
        
    def on_draw(self):
        pass
    
    def create_main_frame(self,two_axes=False):
        self.main_frame = QtGui.QWidget()
        
        # Create the mpl Figure and FigCanvas objects
        self.dpi = 100
        self.fig = Figure((10.0, 10.0), dpi=self.dpi, facecolor='White')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        self.axes = self.fig.add_subplot(111, axisbg='White')
        
        if two_axes:
            self.axes2 = self.axes.twinx()        
 
        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Other GUI controls               
        show_button = QtGui.QPushButton()
        show_button.clicked.connect(self.plot_settings_view)
        show_button.setIcon(QtGui.QIcon(":gear.png"))
        show_button.setToolTip(self.tr("Plot settings"))
        show_button.setStatusTip(self.tr("Plot settings"))

        buttonbox0 = QtGui.QDialogButtonBox()
        buttonbox0.addButton(show_button, QtGui.QDialogButtonBox.ActionRole)               

        self.mpl_toolbar.addWidget(show_button)                      
                                
        vbox = QtGui.QVBoxLayout()        
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
        
        self.status_text = QtGui.QLabel("")        
        self.statusBar().addWidget(self.status_text,1) 
        
    def create_menu(self):

        self.file_menu = self.menuBar().addMenu(self.tr("File"))
        tip = self.tr("Quit")
        quit_action = QtGui.QAction(tip, self)
        quit_action.setIcon(QtGui.QIcon(":quit.png"))
        quit_action.triggered.connect(self.close) 
        quit_action.setToolTip(tip)
        quit_action.setStatusTip(tip)
        quit_action.setShortcut('Ctrl+Q')
       
        self.file_menu.addAction(quit_action)        

    def plot_settings_view(self):
        settings_dialog = PlotSettingsDialog(self)
        settings_dialog.setModal(True)
        settings_dialog.show()       

########## IVMainPlot sub class - Voc Isc ##########

class CorrVocIsc(IVMainPlot):
    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr("Correlation"))
        
        self.ad = parent.ad
        self.plot_selection = []
        for i in range(len(self.ad)):
            self.plot_selection.append(i)
        
        self.single_dataset = False
        self.title_enabled = False
        self.grid_enabled = True
        self.grid_selection = True
        self.legend_enabled = True
        self.legend_selection = True
        self.dotsize_enabled = True
        self.dotsize_selection = 20
        self.linewidth_enabled = False
        
        IVMainPlot.create_menu(self)
        IVMainPlot.create_main_frame(self)          
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_selection)

        self.axes.set_xlabel(r'$\mathrm{\mathsf{V_{OC}\ [V]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{I_{SC}\ [A]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8)
        
        for i in self.plot_selection:
            self.axes.scatter(self.ad[i]['Uoc'],self.ad[i]['Isc'],c=cl[i % len(cl)],edgecolors='white',linewidths=0.3,s=self.dotsize_selection,label=self.ad[i].index.name)

        if self.legend_selection:
            self.axes.legend(loc='lower left',scatterpoints=1,markerscale=3,frameon=False)

        self.canvas.draw()
        
########## IVMainPlot sub class - Eta FF ##########

class CorrEtaFF(IVMainPlot):
    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr("Correlation"))
        
        self.ad = parent.ad
        self.plot_selection = []
        for i in range(len(self.ad)):
            self.plot_selection.append(i)

        self.single_dataset = False            
        self.title_enabled = False
        self.grid_enabled = True
        self.grid_selection = True
        self.legend_enabled = True
        self.legend_selection = True
        self.dotsize_enabled = True
        self.dotsize_selection = 20
        self.linewidth_enabled = False        
        
        IVMainPlot.create_menu(self)
        IVMainPlot.create_main_frame(self)          
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_selection)

        self.axes.set_xlabel(r'$\mathrm{\mathsf{FF\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Eta\ [\%]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8)               
        
        for i in self.plot_selection:
            self.axes.scatter(self.ad[i]['FF'],self.ad[i]['Eta'],c=cl[i % len(cl)],edgecolors='white',linewidths=0.3,s=self.dotsize_selection,label=self.ad[i].index.name)
        
        if self.legend_selection:
            self.axes.legend(loc='lower left',scatterpoints=1,markerscale=3,frameon=False)

        self.canvas.draw() 
        
########## IVMainPlot sub class - Rsh FF ##########

class CorrRshFF(IVMainPlot):
    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr("Correlation"))
        
        self.ad = parent.ad
        self.plot_selection = []
        for i in range(len(self.ad)):
            self.plot_selection.append(i)

        self.single_dataset = False
        self.title_enabled = False           
        self.grid_enabled = True
        self.grid_selection = True
        self.legend_enabled = True
        self.legend_selection = True
        self.dotsize_enabled = True
        self.dotsize_selection = 20
        self.linewidth_enabled = False          
        
        IVMainPlot.create_menu(self)
        IVMainPlot.create_main_frame(self)          
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_selection)

        self.axes.set_xlabel(r'$\mathrm{\mathsf{FF\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Rsh\ [kOhm]}}$', fontsize=24, weight='black')
        self.axes.semilogy()
        self.axes.tick_params(pad=8)              
        
        for i in self.plot_selection:
            self.axes.scatter(self.ad[i]['FF'],self.ad[i]['Rsh'],c=cl[i % len(cl)],edgecolors='white',linewidths=0.3,s=self.dotsize_selection,label=self.ad[i].index.name)
        
        if self.legend_selection:
            self.axes.legend(loc='lower left',scatterpoints=1,markerscale=3,frameon=False)

        self.canvas.draw()      

########## IVMainPlot sub class - Distribution ##########

class DistLtoH(IVMainPlot):
    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr("Distribution"))
        
        self.ad = parent.ad
        self.plot_selection = []
        for i in range(len(self.ad)):
            self.plot_selection.append(i)

        self.single_dataset = False
        self.title_enabled = False            
        self.grid_enabled = True
        self.grid_selection = True
        self.legend_enabled = True
        self.legend_selection = True
        self.dotsize_enabled = True
        self.dotsize_selection = 200        
        self.linewidth_enabled = False        
        
        IVMainPlot.create_menu(self)
        IVMainPlot.create_main_frame(self)          
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_selection)

        xmin = 1e4
        xmax = 0
        ymin = -1
        
        self.axes.set_xlabel(r'$\mathrm{\mathsf{Eta\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8) 
        
        for i in self.plot_selection:
            se = pd.DataFrame(np.sort(self.ad[i]['Eta'])) # Sorted Eta
            if se.ix[:,0].min() <= xmin : xmin = se.ix[:,0].min()
            if se.ix[:,0].max() >= xmax : xmax = se.ix[:,0].max()
            if np.log10(1/len(se)) < ymin : ymin = np.log10(1/len(se))
            se.index = (se.index+1)/len(se)
            self.axes.scatter(se,se.index,c=cl[i % len(cl)],edgecolor=cl[i % len(cl)],marker=r'$\circ$',s=self.dotsize_selection,label=self.ad[i].index.name)
  
        self.axes.set_xlim((np.floor(xmin), np.ceil(xmax)))
        self.axes.semilogy(10 ** np.floor(ymin))
        self.axes.set_ylim((10 ** np.floor(ymin), 2))
            
        if self.legend_selection:
            self.axes.legend(loc='upper left',scatterpoints=1,markerscale=1,frameon=False)

        self.canvas.draw() 

########## IVMainPlot sub class - Density ##########

class DensEta(IVMainPlot):
    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr("Density"))
        
        self.ad = parent.ad
        self.plot_selection = []
        for i in range(len(self.ad)):
            self.plot_selection.append(i)

        self.single_dataset = False
        self.title_enabled = False           
        self.grid_enabled = True
        self.grid_selection = True
        self.legend_enabled = True
        self.legend_selection = True
        self.dotsize_enabled = False
        self.linewidth_enabled = True
        self.linewidth_selection = 3
        
        IVMainPlot.create_menu(self)
        IVMainPlot.create_main_frame(self)          
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()
        
        xmin = 1e4
        xmax = 0        
        
        for i in self.plot_selection:
            se = self.ad[i]['Eta']
            if se.min() <= xmin : xmin = se.min()
            if se.max() >= xmax : xmax = se.max()
            se.plot(kind='kde',c=cl[i % len(cl)],lw=self.linewidth_selection,label=self.ad[i].index.name,ax=self.axes)
                
        self.axes.set_xlabel(r'$\mathrm{\mathsf{Eta\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Density\ [a.u.]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8) 
        
        self.axes.grid(self.grid_selection) # set grid preferences here (after calling pandas internal function)
        self.axes.set_xlim((np.floor(xmin), np.ceil(xmax)))
            
        if self.legend_selection:
            self.axes.legend(loc='upper left',scatterpoints=1,markerscale=1,frameon=False)

        self.canvas.draw() 

########## IVMainPlot sub class - Walk-through ##########

class DistWT(IVMainPlot):
    def __init__(self, parent, param_one_combo):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr("Walkthrough"))
        
        self.ad = parent.ad

        self.plot_selection = []
        for i in range(len(self.ad)):
            self.plot_selection.append(i)

        self.single_dataset = False
        self.title_enabled = False            
        self.grid_enabled = True
        self.grid_selection = True
        self.legend_enabled = True
        self.legend_selection = True
        self.dotsize_enabled = True
        self.dotsize_selection = 20
        self.linewidth_enabled = False        
        
        if str(param_one_combo) in plot_selection_list:
            self.param_one_combo = str(param_one_combo)        
        IVMainPlot.create_menu(self)
        IVMainPlot.create_main_frame(self)
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_selection)

        self.axes.set_xlabel(r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$', fontsize=24, weight='black')
        
        for i, value in enumerate(plot_selection_list):
            if self.param_one_combo == value:
                self.axes.set_ylabel(plot_label_list[i], fontsize=24, weight='black')

        self.axes.tick_params(pad=8) 
        
        for i in self.plot_selection:                
            if (self.param_one_combo == 'Voc*Isc'):
                se = pd.DataFrame(self.ad[i]['Uoc'] * self.ad[i]['Isc'])
            elif (self.param_one_combo == 'RserLfDfIEC'):
                se = pd.DataFrame(1000*self.ad[i][self.param_one_combo])
            elif (self.param_one_combo == 'Rsh'):
                se = pd.DataFrame(0.001*self.ad[i][self.param_one_combo])
            else:
                se = pd.DataFrame(self.ad[i][self.param_one_combo])
            
            se.index = (se.index+1)/len(se)
            self.axes.scatter(se.index,se,c=cl[i % len(cl)],edgecolors='white',linewidths=0.3,s=self.dotsize_selection,label=self.ad[i].index.name)

        self.axes.set_xlim((0, 1))
    
        if self.legend_selection:
            self.axes.legend(loc='lower left',scatterpoints=1,markerscale=3,frameon=True)

        self.canvas.draw()  

########## IVMainPlot sub class - Rolling mean ##########

class DistRM(IVMainPlot):
    def __init__(self, parent, param_one_combo):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr("Rolling mean"))
       
        self.ad = parent.ad
        
        self.plot_selection = []
        for i in range(len(self.ad)):
            self.plot_selection.append(i)

        self.single_dataset = False
        self.title_enabled = False            
        self.grid_enabled = True
        self.grid_selection = True
        self.legend_enabled = True
        self.legend_selection = True
        self.dotsize_enabled = False        
        self.linewidth_enabled = True
        self.linewidth_selection = 3        
        
        if str(param_one_combo) in plot_selection_list:
            self.param_one_combo = str(param_one_combo)         
        IVMainPlot.create_menu(self)
        IVMainPlot.create_main_frame(self)
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_selection)        

        self.axes.set_xlabel(r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$', fontsize=24, weight='black')        
        for i, value in enumerate(plot_selection_list):
            if self.param_one_combo == value:
                self.axes.set_ylabel(plot_label_list[i], fontsize=24, weight='black')        
        self.axes.tick_params(pad=8) 
        
        for i in self.plot_selection:
            if (self.param_one_combo == 'Voc*Isc'):
                se = pd.DataFrame(self.ad[i]['Uoc'] * self.ad[i]['Isc'])
            elif (self.param_one_combo == 'RserLfDfIEC'):
                se = pd.DataFrame(1000*self.ad[i][self.param_one_combo])
            elif (self.param_one_combo == 'Rsh'):
                se = pd.DataFrame(0.001*self.ad[i][self.param_one_combo])                    
            else:
                se = pd.DataFrame(self.ad[i][self.param_one_combo])
                
            se.index = (se.index+1)/len(se)
            rm = pd.rolling_mean(se, np.floor(len(se)*.1) if len(se) > 100 else 1,center=True) # rolling mean
            self.axes.plot(rm.index, rm,c=cl[i % len(cl)],lw=self.linewidth_selection,label=self.ad[i].index.name)
    
        if self.legend_selection:
            self.axes.legend(loc='lower left',scatterpoints=1,markerscale=3,frameon=True)

        self.canvas.draw() 

########## IVMainPlot sub class - Boxplot ##########
       
class IVBoxPlot(IVMainPlot):
    def __init__(self, parent, param_one_combo):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr("Boxplot"))

        self.ad = parent.ad
        
        self.plot_selection = []
        for i in range(len(self.ad)):
            self.plot_selection.append(i)

        self.single_dataset = False
        self.title_enabled = False        
        self.grid_enabled = False
        self.legend_enabled = False
        self.dotsize_enabled = False
        self.linewidth_enabled = False        
        
        if str(param_one_combo) in plot_selection_list:
            self.param_one_combo = str(param_one_combo)
        IVMainPlot.create_menu(self)
        IVMainPlot.create_main_frame(self)
        self.on_draw()                     
        
    def on_draw(self):

        # Clear previous and re-draw everything
        self.axes.clear()

        for i, value in enumerate(plot_selection_list):
            if self.param_one_combo == value:
                self.axes.set_ylabel(plot_label_list[i], fontsize=24, weight='black')
        self.axes.tick_params(pad=8)

        if len(self.plot_selection) == 0:
            self.canvas.draw()
            return
        
        data = []
        labels = []
        for i in self.plot_selection:
            if (self.param_one_combo == 'Voc*Isc'):
                data.append(self.ad[i]['Uoc'] * self.ad[i]['Isc'])                    
            elif (self.param_one_combo == 'RserLfDfIEC'):
                data.append(1000*self.ad[i][str(self.param_one_combo)])
            elif (self.param_one_combo == 'Rsh'):
                data.append(0.001*self.ad[i][str(self.param_one_combo)])                    
            else:
                data.append(self.ad[i][str(self.param_one_combo)])
                
            labels.append(self.ad[i].index.name)
        self.axes.set_xticklabels(labels, rotation=0)
        bp = self.axes.boxplot(data,0,'')
        plt.setp(bp['boxes'], color='black',lw=2)
        plt.setp(bp['whiskers'], color='black',lw=2,ls='-')
        plt.setp(bp['caps'], color='black', lw=2)

        self.canvas.draw()
    
########## IVMainPlot sub class - Histogram ##########
       
class IVHistPlot(IVMainPlot):
    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr("Histogram"))
        
        self.ad = parent.ad

        self.plot_selection = [0]
        self.title_enabled = True
        self.title_selection = True
        self.single_dataset = True
        self.grid_enabled = False
        self.legend_enabled = False
        self.dotsize_enabled = False
        self.linewidth_enabled = False
        
        IVMainPlot.create_menu(self)
        IVMainPlot.create_main_frame(self)
        self.on_draw()                     
        
    def on_draw(self):

        # Clear previous and re-draw everything
        self.axes.clear()

        se = self.ad[self.plot_selection[0]]['Eta'].round(1)
        freq = se.value_counts()
        freq = 100*freq/len(se)
        freq = freq.sort_index()
        freq.plot(kind='bar',color=cl[self.plot_selection[0] % len(cl)],ax=self.axes)
        if self.title_selection:
            self.axes.set_title(self.ad[self.plot_selection[0]].index.name)
                
        self.axes.set_xlabel(r'$\mathrm{\mathsf{Eta\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Frequency\ [\%]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8)
        self.axes.grid(False)            

        self.canvas.draw()
      
########## IVMainPlot sub class - Histogram and density ##########
       
class IVHistDenPlot(IVMainPlot):
    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr("Histogram and density"))
        
        self.ad = parent.ad
        
        self.plot_selection = [0]
        self.title_enabled = True
        self.title_selection = True
        self.single_dataset = True
        self.grid_enabled = False
        self.legend_enabled = False
        self.dotsize_enabled = False        
        self.linewidth_enabled = True
        self.linewidth_selection = 3        
        
        IVMainPlot.create_menu(self)
        IVMainPlot.create_main_frame(self,True)
        self.on_draw()                     
        
    def on_draw(self):

        # Clear previous and re-draw everything
        self.axes.clear()
        self.axes2.clear()

        xmin = 1e4
        xmax = 0

        for i in self.ad: 
            ser = self.ad[i]['Eta']
            if ser.min() <= xmin : xmin = ser.min()
            if ser.max() >= xmax : xmax = ser.max()

        den = self.ad[self.plot_selection[0]]['Eta']
        bn = self.ad[self.plot_selection[0]]['Eta'].round(1)
        freq = bn.value_counts()
        freq = 100*freq/len(bn)
        freq = freq.sort_index()
        self.axes.bar(freq.index, freq.values, 0.1, color=cl[self.plot_selection[0] % len(cl)],align='center')
        den.plot(kind='kde',c='white',lw=self.linewidth_selection+3,ax=self.axes2)
        den.plot(kind='kde',c='black',lw=self.linewidth_selection+1,ax=self.axes2)
        den.plot(kind='kde',c='r',lw=self.linewidth_selection,ax=self.axes2)
        if self.title_selection:
            self.axes.set_title(self.ad[self.plot_selection[0]].index.name)
                
        self.axes.set_xlim((np.floor(xmin), np.ceil(xmax)))
        self.axes2.set_xlim((np.floor(xmin), np.ceil(xmax)))
                
        self.axes.set_xlabel(r'$\mathrm{\mathsf{Eta\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Frequency\ [\%]}}$', fontsize=24, weight='black')
        self.axes2.set_ylabel(r'$\mathrm{\mathsf{Density\ [a.u.]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8)            
        self.axes2.tick_params(pad=8)
        self.axes.grid(False)
        self.axes2.grid(False)

        self.canvas.draw()       