from __future__ import division
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
#from matplotlib.ticker import FuncFormatter
from PyQt4 import QtCore, QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})

font = {'family' : 'sans-serif',
        'size'   : 14}

matplotlib.rc('font', **font)

cl = ['#4F81BD', '#C0504D', '#9BBB59','#F79646','#8064A2','#4BACC6','0','0.5'] # colour

import Required_resources
icon_name = ":Logo_Tempress.ico"

plot_selection_list = ['Uoc','Isc','Voc*Isc','FF','Eta']
eta_axis_label = r'$\mathrm{\mathsf{Eta\ [\%]}}$'
voc_axis_label = r'$\mathrm{\mathsf{V_{OC}\ [V]}}$'
isc_axis_label = r'$\mathrm{\mathsf{I_{SC}\ [A]}}$'
ff_axis_label = r'$\mathrm{\mathsf{FF\ [\%]}}$'
vocisc_axis_label = r'$\mathrm{\mathsf{V_{OC}\ *\ I_{SC}\ [V*A]}}$'
plot_label_list = [voc_axis_label, isc_axis_label, vocisc_axis_label, ff_axis_label, eta_axis_label]

########## Main class - only for inheriting ##########

class IVMainPlot(QtGui.QMainWindow):  
    
    def __init__(self, ad, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr( "Solar cell data analysis - Matplotlib graph"))
        self.setWindowIcon(QtGui.QIcon(icon_name))
        self.translator = None 

        self.ad = ad
        self.create_menu()
        self.create_main_frame()
        self.on_draw()           
    
    def on_about(self):
        msg = self.tr("Solar cell data analysis\n\n- Author: Ronald Naber (rnaber@tempress.nl)\n- License: Public domain")
        QtGui.QMessageBox.about(self, self.tr("About the application"), msg)      
        
    def on_draw(self):
        pass
    
    def create_main_frame(self):
        pass
        
    def create_menu(self):        
        self.file_menu = self.menuBar().addMenu("&File")
        
        quit_action = self.create_action("&Quit", slot=self.close, 
            shortcut="Ctrl+Q", tip="Close the application")
        
        self.add_actions(self.file_menu,(None,quit_action))
        
        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip=self.tr("About the application"))
        
        self.add_actions(self.help_menu, (about_action,))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QtGui.QAction(text, self)
        if icon is not None:
            action.setIcon(QtGui.QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, QtCore.SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action 
        
########## Main scatter plot class - only for inheriting ##########

class IVScatterPlot(IVMainPlot):
    def __init__(self, ad, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Matplotlib graph")
        self.setWindowIcon(QIcon(icon_name))

        self.ad = ad
        self.fig = ''
        self.canvas = ''
        self.axes = ''
        IVMainPlot.create_menu()
        self.create_main_frame()
        self.on_draw()  

    def create_main_frame(self):
        self.main_frame = QtGui.QWidget()
        
        # Create the mpl Figure and FigCanvas objects
        self.dpi = 100
        self.fig = Figure((10.0, 10.0), dpi=self.dpi, facecolor='White')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        self.axes = self.fig.add_subplot(111, axisbg='White')        
 
        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Other GUI controls        
        self.grid_cb = QtGui.QCheckBox("&Grid")
        self.grid_cb.setChecked(True)

        self.legend_cb = QtGui.QCheckBox("L&egend")
        self.legend_cb.setChecked(True)               
        
        self.dataset_cb = {}
        for i in self.ad:
            self.dataset_cb[i] = QtGui.QCheckBox(self.ad[i].index.name)
            self.dataset_cb[i].setChecked(True)         

        self.show_button = QtGui.QPushButton("&Show")
        self.connect(self.show_button, QtCore.SIGNAL('clicked()'), self.on_draw)                
            
        hbox = QtGui.QHBoxLayout()
        
        hbox.addWidget(self.grid_cb)
        hbox.addWidget(self.legend_cb)
        
        for i in self.ad:
            hbox.addWidget(self.dataset_cb[i])

        hbox.addWidget(self.show_button)            
                                
        vbox = QtGui.QVBoxLayout()        
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addLayout(hbox)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

########## Scatter plot sub class - Voc Isc ##########

class CorrVocIsc(IVScatterPlot):
    def __init__(self, ad, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Voc-Isc correlation")
        self.setWindowIcon(QtGui.QIcon(icon_name))
        
        self.ad = ad
        IVMainPlot.create_menu(self)
        IVScatterPlot.create_main_frame(self)
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_cb.isChecked())

        self.axes.set_xlabel(r'$\mathrm{\mathsf{V_{OC}\ [V]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{I_{SC}\ [A]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8)
        
        #def form3(x, pos): return '%.3f' % x
        #formatter = FuncFormatter(form3)
        #self.axes.xaxis.set_major_formatter(FuncFormatter(formatter))        
        
        #def form2(x, pos): return '%.2f' % x
        #formatter = FuncFormatter(form2)
        #self.axes.yaxis.set_major_formatter(FuncFormatter(formatter))        
        
        for i in self.ad:
            if(self.dataset_cb[i].isChecked()):
                self.axes.scatter(self.ad[i]['Uoc'],self.ad[i]['Isc'],c=cl[i % len(cl)],edgecolors='white',linewidths=0.3,s=20,label=self.ad[i].index.name)
        
        if self.legend_cb.isChecked():
            self.axes.legend(loc='lower left',scatterpoints=1,markerscale=3,frameon=False)

        self.canvas.draw()
        
########## Scatter plot sub class - Eta FF ##########

class CorrEtaFF(IVScatterPlot):
    def __init__(self, ad, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Eta-FF correlation")
        self.setWindowIcon(QtGui.QIcon(icon_name))
        
        self.ad = ad
        IVMainPlot.create_menu(self)
        IVScatterPlot.create_main_frame(self)
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_cb.isChecked())

        self.axes.set_xlabel(r'$\mathrm{\mathsf{FF\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Eta\ [\%]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8)               
        
        for i in self.ad:
            if(self.dataset_cb[i].isChecked()):
                self.axes.scatter(self.ad[i]['FF'],self.ad[i]['Eta'],c=cl[i % len(cl)],edgecolors='white',linewidths=0.3,s=20,label=self.ad[i].index.name)
        
        if self.legend_cb.isChecked():
            self.axes.legend(loc='lower left',scatterpoints=1,markerscale=3,frameon=False)

        self.canvas.draw() 
        
########## Scatter plot sub class - Rsh FF ##########

class CorrRshFF(IVScatterPlot):
    def __init__(self, ad, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Rsh-FF correlation")
        self.setWindowIcon(QtGui.QIcon(icon_name))
        
        self.ad = ad
        IVMainPlot.create_menu(self)
        IVScatterPlot.create_main_frame(self)
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_cb.isChecked())

        self.axes.set_xlabel(r'$\mathrm{\mathsf{FF\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Rsh\ [kOhm]}}$', fontsize=24, weight='black')
        self.axes.semilogy()
        self.axes.tick_params(pad=8)              
        
        for i in self.ad:
            if(self.dataset_cb[i].isChecked()):
                self.axes.scatter(self.ad[i]['FF'],self.ad[i]['Rsh'],c=cl[i % len(cl)],edgecolors='white',linewidths=0.3,s=20,label=self.ad[i].index.name)
        
        if self.legend_cb.isChecked():
            self.axes.legend(loc='lower left',scatterpoints=1,markerscale=3,frameon=False)

        self.canvas.draw()      

########## Scatter plot sub class - Distribution ##########

class DistLtoH(IVScatterPlot):
    def __init__(self, ad, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Eta distribution")
        self.setWindowIcon(QtGui.QIcon(icon_name))
        
        self.ad = ad
        IVMainPlot.create_menu(self)
        IVScatterPlot.create_main_frame(self)
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_cb.isChecked())

        xmin = 1e4
        xmax = 0
        ymin = -1
        
        self.axes.set_xlabel(r'$\mathrm{\mathsf{Eta\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8) 
        
        for i in self.ad:
            if(self.dataset_cb[i].isChecked()):
                se = pd.DataFrame(np.sort(self.ad[i]['Eta'])) # Sorted Eta
                if se.ix[:,0].min() <= xmin : xmin = se.ix[:,0].min()
                if se.ix[:,0].max() >= xmax : xmax = se.ix[:,0].max()
                if np.log10(1/len(se)) < ymin : ymin = np.log10(1/len(se))
                se.index = (se.index+1)/len(se)
                self.axes.scatter(se,se.index,c=cl[i % len(cl)],edgecolor=cl[i % len(cl)],marker=r'$\circ$',s=200,label=self.ad[i].index.name)
  
        self.axes.set_xlim((np.floor(xmin), np.ceil(xmax)))
        self.axes.semilogy(10 ** np.floor(ymin))
        self.axes.set_ylim((10 ** np.floor(ymin), 2))
        #self.axes.set_xlim((np.floor(xmin), np.ceil(xmax)))
        #self.axes.set_ylim((-0.2, 1.2))
            
        if self.legend_cb.isChecked():
            self.axes.legend(loc='upper left',scatterpoints=1,markerscale=1,frameon=False)

        self.canvas.draw() 

########## Scatter plot sub class - Density ##########

class DensEta(IVScatterPlot):
    def __init__(self, ad, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Density Eta")
        self.setWindowIcon(QtGui.QIcon(icon_name))
        
        self.ad = ad
        IVMainPlot.create_menu(self)
        IVScatterPlot.create_main_frame(self)
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        #self.axes.grid(self.grid_cb.isChecked())
        
        xmin = 1e4
        xmax = 0        
        
        for i in self.ad:
            if(self.dataset_cb[i].isChecked()):
                se = self.ad[i]['Eta']
                if se.min() <= xmin : xmin = se.min()
                if se.max() >= xmax : xmax = se.max()
                se.plot(kind='kde',c=cl[i % len(cl)],lw=3,label=self.ad[i].index.name,ax=self.axes)
                
        self.axes.set_xlabel(r'$\mathrm{\mathsf{Eta\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Density\ [a.u.]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8) 
        
        self.axes.grid(self.grid_cb.isChecked()) # set grid preferences here (after calling pandas internal function)
        self.axes.set_xlim((np.floor(xmin), np.ceil(xmax)))
            
        if self.legend_cb.isChecked():
            self.axes.legend(loc='upper left',scatterpoints=1,markerscale=1,frameon=False)

        self.canvas.draw() 

########## Scatter plot sub class - Walk-through ##########

class DistWT(IVScatterPlot):
    def __init__(self, ad, plot_selection, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Eta stability")
        self.setWindowIcon(QtGui.QIcon(icon_name))
        
        self.ad = ad
        if str(plot_selection) in plot_selection_list:
            self.plot_selection = str(plot_selection)        
        IVMainPlot.create_menu(self)
        IVScatterPlot.create_main_frame(self)
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_cb.isChecked())

        self.axes.set_xlabel(r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$', fontsize=24, weight='black')
        for i, value in enumerate(plot_selection_list):
            if self.plot_selection == value:
                self.axes.set_ylabel(plot_label_list[i], fontsize=24, weight='black')
        self.axes.tick_params(pad=8) 
        
        for i in self.ad:
            if(self.dataset_cb[i].isChecked()):                
                if not self.plot_selection == 'Voc*Isc':
                    se = pd.DataFrame(self.ad[i][self.plot_selection])
                else:
                    se = pd.DataFrame(self.ad[i]['Uoc'] * self.ad[i]['Isc'])                
                
                se.index = (se.index+1)/len(se)
                self.axes.scatter(se.index,se,c=cl[i % len(cl)],edgecolors='white',linewidths=0.3,s=20,label=self.ad[i].index.name)

        self.axes.set_xlim((0, 1))
    
        if self.legend_cb.isChecked():
            self.axes.legend(loc='lower left',scatterpoints=1,markerscale=3,frameon=True)

        self.canvas.draw()  

########## Scatter plot sub class - Rolling mean ##########

class DistRM(IVScatterPlot):
    def __init__(self, ad, plot_selection, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Rolling mean")
        self.setWindowIcon(QtGui.QIcon(icon_name))
       
        self.ad = ad
        if str(plot_selection) in plot_selection_list:
            self.plot_selection = str(plot_selection)         
        IVMainPlot.create_menu(self)
        IVScatterPlot.create_main_frame(self)
        self.on_draw()
        
    def on_draw(self):
        # Clear previous and re-draw everything
        self.axes.clear()   
        self.axes.grid(self.grid_cb.isChecked())
        
        spot_size = 20 # number of pixels for each data point

        self.axes.set_xlabel(r'$\mathrm{\mathsf{Normalized\ cell\ number\ [a.u.]}}$', fontsize=24, weight='black')        
        for i, value in enumerate(plot_selection_list):
            if self.plot_selection == value:
                self.axes.set_ylabel(plot_label_list[i], fontsize=24, weight='black')        
        self.axes.tick_params(pad=8) 
        
        for i in self.ad:
            if(self.dataset_cb[i].isChecked()):

                if not self.plot_selection == 'Voc*Isc':
                    se = pd.DataFrame(self.ad[i][self.plot_selection])
                else:
                    se = pd.DataFrame(self.ad[i]['Uoc'] * self.ad[i]['Isc'])                
                se.index = (se.index+1)/len(se)
                rm = pd.rolling_mean(se, np.floor(len(se)*.1) if len(se) > 100 else 1,center=True) # rolling mean
                self.axes.plot(rm.index, rm,c=cl[i % len(cl)],lw=3,label=self.ad[i].index.name)

        #plt.xlim((0, 1))
    
        if self.legend_cb.isChecked():
            self.axes.legend(loc='lower left',scatterpoints=1,markerscale=3,frameon=True)

        self.canvas.draw() 

########## IVMainPlot sub class - Boxplot ##########
       
class IVBoxPlot(IVMainPlot):
    def __init__(self, ad, plot_selection, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Boxplot Eta")
        self.setWindowIcon(QtGui.QIcon(icon_name))

        self.ad = ad
        if str(plot_selection) in plot_selection_list:
            self.plot_selection = str(plot_selection)
        IVMainPlot.create_menu(self)
        self.create_main_frame()
        self.on_draw()                     
        
    def on_draw(self):

        # Clear previous and re-draw everything
        self.axes.clear()           

        for i, value in enumerate(plot_selection_list):
            if self.plot_selection == value:
                self.axes.set_ylabel(plot_label_list[i], fontsize=24, weight='black')
        self.axes.tick_params(pad=8)  
        
        data = []
        labels = []
        for i in self.ad:
            if(self.dataset_cb[i].isChecked()):
                if not self.plot_selection == 'Voc*Isc':
                    data.append(self.ad[i][str(self.plot_selection)])
                else:
                    data.append(self.ad[i]['Uoc'] * self.ad[i]['Isc'])
                labels.append(self.ad[i].index.name)
        self.axes.set_xticklabels(labels, rotation=0)
        bp = self.axes.boxplot(data,0,'')
        plt.setp(bp['boxes'], color='black',lw=2)
        plt.setp(bp['whiskers'], color='black',lw=2,ls='-')
        plt.setp(bp['caps'], color='black', lw=2)    

        self.canvas.draw()
    
    def create_main_frame(self):
        self.main_frame = QtGui.QWidget()
        
        # Create the mpl Figure and FigCanvas objects
        self.dpi = 100
        self.fig = Figure((10.0, 10.0), dpi=self.dpi, facecolor='White')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        self.axes = self.fig.add_subplot(111, axisbg='White')        
 
        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Other GUI controls                      
        
        self.dataset_cb = {}
        for i in self.ad:
            self.dataset_cb[i] = QtGui.QCheckBox(self.ad[i].index.name)
            self.dataset_cb[i].setChecked(True)         

        self.show_button = QtGui.QPushButton("&Show")
        self.connect(self.show_button, QtCore.SIGNAL('clicked()'), self.on_draw)                
            
        hbox = QtGui.QHBoxLayout()        
        
        for i in self.ad:
            hbox.addWidget(self.dataset_cb[i])

        hbox.addWidget(self.show_button)            
                                
        vbox = QtGui.QVBoxLayout()        
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addLayout(hbox)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
        
########## IVMainPlot sub class - Histogram ##########
       
class IVHistPlot(IVMainPlot):
    def __init__(self, ad, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Histogram Eta")
        self.setWindowIcon(QtGui.QIcon(icon_name))
        
        self.ad = ad
        IVMainPlot.create_menu(self)
        self.create_main_frame()
        self.on_draw()                     
        
    def on_draw(self):

        # Clear previous and re-draw everything
        self.axes.clear()        

        #bins = 20

        for i in self.ad:
            if(self.dataset_cb[i].isChecked()):
                se = self.ad[i]['Eta'].round(1)
                freq = se.value_counts()
                freq = 100*freq/len(se)
                freq = freq.sort_index()
                #freq = freq.drop(freq.index[[np.arange(0,len(freq)-bins)]]) # if bins < no_datapoints it does not drop anything
                freq.plot(kind='bar',color=cl[i % len(cl)],ax=self.axes)
                if self.title_cb.isChecked():
                    self.axes.set_title(self.ad[i].index.name)
                
        self.axes.set_xlabel(r'$\mathrm{\mathsf{Eta\ [\%]}}$', fontsize=24, weight='black')
        self.axes.set_ylabel(r'$\mathrm{\mathsf{Frequency\ [\%]}}$', fontsize=24, weight='black')
        self.axes.tick_params(pad=8)
        self.axes.grid(False)            

        self.canvas.draw()
    
    def create_main_frame(self):
        self.main_frame = QtGui.QWidget()
        
        # Create the mpl Figure and FigCanvas objects
        self.dpi = 100
        self.fig = Figure((10.0, 10.0), dpi=self.dpi, facecolor='White')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        self.axes = self.fig.add_subplot(111, axisbg='White')        
 
        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Other GUI controls                      

        self.title_cb = QtGui.QCheckBox("&Title")
        self.title_cb.setChecked(True)
        
        self.dataset_cb = {}
        for i in self.ad:
            self.dataset_cb[i] = QtGui.QRadioButton(self.ad[i].index.name)
        self.dataset_cb[0].setChecked(True)         

        self.show_button = QtGui.QPushButton("&Show")
        self.connect(self.show_button, QtCore.SIGNAL('clicked()'), self.on_draw)                
            
        hbox = QtGui.QHBoxLayout()        
        
        hbox.addWidget(self.title_cb)        
        
        for i in self.ad:
            hbox.addWidget(self.dataset_cb[i])

        hbox.addWidget(self.show_button)            
                                
        vbox = QtGui.QVBoxLayout()        
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addLayout(hbox)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
        
########## IVMainPlot sub class - Histogram and density ##########
       
class IVHistDenPlot(IVMainPlot):
    def __init__(self, ad, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("Solar cell data analysis - Histogram and density Eta")
        self.setWindowIcon(QtGui.QIcon(icon_name))
        
        self.ad = ad
        IVMainPlot.create_menu(self)
        self.create_main_frame()
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
                
        #bins = 20 

        for i in self.ad:
            if(self.dataset_cb[i].isChecked()):
                den = self.ad[i]['Eta']
                bn = self.ad[i]['Eta'].round(1)
                freq = bn.value_counts()
                freq = 100*freq/len(bn)
                freq = freq.sort_index()
                #freq = freq.drop(freq.index[[np.arange(0,len(freq)-bins)]]) # if bins < no_datapoints it does not drop anything
                self.axes.bar(freq.index, freq.values, 0.1, color=cl[i % len(cl)],align='center')
                den.plot(kind='kde',c='white',lw=6,ax=self.axes2)
                den.plot(kind='kde',c='black',lw=4,ax=self.axes2)
                den.plot(kind='kde',c='r',lw=3,ax=self.axes2)
                if self.title_cb.isChecked():
                    self.axes.set_title(self.ad[i].index.name)
                
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

    def create_main_frame(self):
        self.main_frame = QtGui.QWidget()
        
        # Create the mpl Figure and FigCanvas objects
        self.dpi = 100
        self.fig = Figure((10.0, 10.0), dpi=self.dpi, facecolor='White')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        self.axes = self.fig.add_subplot(111, axisbg='White')
        self.axes2 = self.axes.twinx()        
 
        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Other GUI controls                      

        self.title_cb = QtGui.QCheckBox("&Title")
        self.title_cb.setChecked(True)
        
        self.dataset_cb = {}
        for i in self.ad:
            self.dataset_cb[i] = QtGui.QRadioButton(self.ad[i].index.name)
        self.dataset_cb[0].setChecked(True)         

        self.show_button = QtGui.QPushButton("&Show")
        self.connect(self.show_button, QtCore.SIGNAL('clicked()'), self.on_draw)                
            
        hbox = QtGui.QHBoxLayout()        
        
        hbox.addWidget(self.title_cb)        
        
        for i in self.ad:
            hbox.addWidget(self.dataset_cb[i])

        hbox.addWidget(self.show_button)            
                                
        vbox = QtGui.QVBoxLayout()        
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addLayout(hbox)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)        