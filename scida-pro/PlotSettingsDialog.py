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

        group_area = QtGui.QGroupBox()
        group_area.setFlat(True)
        group_vbox = QtGui.QVBoxLayout()

        if self.parent.linewidth_enabled:
            self.linewidth_sb = QtGui.QSpinBox()
            self.linewidth_sb.setAccelerated(True)
            self.linewidth_sb.setMaximum(999)
            self.linewidth_sb.setMinimum(1)            
            self.linewidth_sb.setValue(self.parent.linewidth_selection)
            
            hbox = QtGui.QHBoxLayout()
            description = QtGui.QLabel(self.tr("Line width"))
            hbox.addWidget(self.linewidth_sb)
            hbox.addWidget(description)
            hbox.addStretch(1)
            group_vbox.addLayout(hbox)

        if self.parent.dotsize_enabled:
            self.dotsize_sb = QtGui.QSpinBox()
            self.dotsize_sb.setAccelerated(True)
            self.dotsize_sb.setMaximum(999)
            self.dotsize_sb.setMinimum(1)            
            self.dotsize_sb.setValue(self.parent.dotsize_selection)
            
            hbox = QtGui.QHBoxLayout()
            description = QtGui.QLabel(self.tr("Dot size"))
            hbox.addWidget(self.dotsize_sb)
            hbox.addWidget(description)
            hbox.addStretch(1)
            group_vbox.addLayout(hbox)

        if self.parent.title_enabled:
            self.title_cb = QtGui.QCheckBox(self.tr("Title"))
            if self.parent.title_selection:
                self.title_cb.setChecked(True)
            group_vbox.addWidget(self.title_cb)

        if self.parent.legend_enabled:    
            self.legend_cb = QtGui.QCheckBox(self.tr("Legend"))
            if self.parent.legend_selection:
                self.legend_cb.setChecked(True)
            group_vbox.addWidget(self.legend_cb)

        if self.parent.grid_enabled:       
            self.grid_cb = QtGui.QCheckBox(self.tr("Grid"))
            if self.parent.grid_selection:
                self.grid_cb.setChecked(True)
            group_vbox.addWidget(self.grid_cb)

        group_area.setLayout(group_vbox)
        
        if self.parent.grid_enabled or self.parent.legend_enabled or self.parent.title_enabled or\
                self.parent.dotsize_enabled or self.parent.linewidth_enabled:
            vbox.addWidget(group_area)

        scroll_area = QtGui.QScrollArea()
        checkbox_widget = QtGui.QWidget()
        checkbox_vbox = QtGui.QVBoxLayout()

        for i in range(len(self.dataset_cb)):
            self.dataset_cb[i].setMinimumWidth(400) # prevent obscured text
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

        if self.parent.dotsize_enabled: 
            self.parent.dotsize_selection = self.dotsize_sb.value()

        if self.parent.linewidth_enabled: 
            self.parent.linewidth_selection = self.linewidth_sb.value()
            
        self.parent.plot_selection = []
        for i in range(len(self.dataset_cb)):
            if self.dataset_cb[i].isChecked():
                self.parent.plot_selection.append(i)

        self.parent.on_draw()
        self.close()