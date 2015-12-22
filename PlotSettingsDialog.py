# -*- coding: utf-8 -*-
from __future__ import division
from PyQt4 import QtGui

class PlotSettingsDialog(QtGui.QDialog):
    
    def __init__(self, parent):
        super(QtGui.QDialog, self).__init__(parent)
        
        self.parent = parent       
        
        self.setWindowTitle(self.tr("Plot settings"))
        vbox = QtGui.QVBoxLayout()

        self.dataset_cb = []
                
        if self.parent.single_dataset:
            for i in range(len(self.parent.ad)):
                self.dataset_cb.append(QtGui.QRadioButton(self.parent.ad[i].index.name))
                if i in self.parent.plot_selection:
                    self.dataset_cb[i].setChecked(True)            
        else:
            for i in range(len(self.parent.ad)):
                self.dataset_cb.append(QtGui.QCheckBox(self.parent.ad[i].index.name))
                if i in self.parent.plot_selection:
                    self.dataset_cb[i].setChecked(True)

        scroll_area = QtGui.QScrollArea()
        checkbox_widget = QtGui.QWidget()
        checkbox_vbox = QtGui.QVBoxLayout()

        if self.parent.title_enabled:
            self.title_cb = QtGui.QCheckBox(self.tr("Title"))
            if self.parent.title_selection:
                self.title_cb.setChecked(True)
            checkbox_vbox.addWidget(self.title_cb)

        if self.parent.legend_enabled:    
            self.legend_cb = QtGui.QCheckBox(self.tr("Legend"))
            if self.parent.legend_selection:
                self.legend_cb.setChecked(True)
            checkbox_vbox.addWidget(self.legend_cb)

        if self.parent.grid_enabled:       
            self.grid_cb = QtGui.QCheckBox(self.tr("Grid"))
            if self.parent.grid_selection:
                self.grid_cb.setChecked(True)
            checkbox_vbox.addWidget(self.grid_cb)

        for i in range(len(self.dataset_cb)):
            self.dataset_cb[i].setMinimumWidth(200) # prevent obscured text
            checkbox_vbox.addWidget(self.dataset_cb[i])

        checkbox_widget.setLayout(checkbox_vbox)
        scroll_area.setWidget(checkbox_widget)
        vbox.addWidget(scroll_area)

        ### Buttonbox for ok ###
        hbox = QtGui.QHBoxLayout()
        buttonbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.read)
        buttonbox.rejected.connect(self.reject)
        hbox.addStretch(1) 
        hbox.addWidget(buttonbox)
        hbox.addStretch(1)
        hbox.setContentsMargins(0,0,0,4)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.setMinimumWidth(800)        
        
    def read(self):
        if self.parent.title_enabled:
            self.parent.title_selection = self.title_cb.isChecked()
        
        if self.parent.legend_enabled:         
            self.parent.legend_selection = self.legend_cb.isChecked()

        if self.parent.grid_enabled:             
            self.parent.grid_selection = self.grid_cb.isChecked()
        
        self.parent.plot_selection = []
        for i in range(len(self.dataset_cb)):
            if self.dataset_cb[i].isChecked():
                self.parent.plot_selection.append(i)

        self.parent.on_draw()
        self.close()