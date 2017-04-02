# -*- coding: utf-8 -*-
from __future__ import division
from PyQt5 import QtWidgets

class PlotSettingsDialog(QtWidgets.QDialog):
    
    def __init__(self, parent):
        super(QtWidgets.QDialog, self).__init__(parent)
        
        self.parent = parent       
        
        self.setWindowTitle(self.tr("Plot settings"))
        vbox = QtWidgets.QVBoxLayout()

        self.dataset_cb = []
                
        if self.parent.single_dataset:
            for i in range(len(self.parent.ad)):
                self.dataset_cb.append(QtWidgets.QRadioButton(self.parent.ad[i].index.name))
                if i in self.parent.plot_selection:
                    self.dataset_cb[i].setChecked(True)            
        else:
            for i in range(len(self.parent.ad)):
                self.dataset_cb.append(QtWidgets.QCheckBox(self.parent.ad[i].index.name))
                if i in self.parent.plot_selection:
                    self.dataset_cb[i].setChecked(True)       

        group_area = QtWidgets.QGroupBox()
        group_area.setFlat(True)
        group_vbox = QtWidgets.QVBoxLayout()

        if self.parent.linewidth_enabled:
            self.linewidth_sb = QtWidgets.QSpinBox()
            self.linewidth_sb.setAccelerated(True)
            self.linewidth_sb.setMaximum(999)
            self.linewidth_sb.setMinimum(1)            
            self.linewidth_sb.setValue(self.parent.linewidth_selection)
            
            hbox = QtWidgets.QHBoxLayout()
            description = QtWidgets.QLabel(self.tr("Line width"))
            hbox.addWidget(self.linewidth_sb)
            hbox.addWidget(description)
            hbox.addStretch(1)
            group_vbox.addLayout(hbox)

        if self.parent.dotsize_enabled:
            self.dotsize_sb = QtWidgets.QSpinBox()
            self.dotsize_sb.setAccelerated(True)
            self.dotsize_sb.setMaximum(999)
            self.dotsize_sb.setMinimum(1)            
            self.dotsize_sb.setValue(self.parent.dotsize_selection)
            
            hbox = QtWidgets.QHBoxLayout()
            description = QtWidgets.QLabel(self.tr("Dot size"))
            hbox.addWidget(self.dotsize_sb)
            hbox.addWidget(description)
            hbox.addStretch(1)
            group_vbox.addLayout(hbox)

        if self.parent.scatter_enabled:       
            self.scatter_sb = QtWidgets.QDoubleSpinBox()
            self.scatter_sb.setAccelerated(True)
            self.scatter_sb.setMaximum(0.5)
            self.scatter_sb.setMinimum(0)
            self.scatter_sb.setSingleStep(0.01)
            self.scatter_sb.setDecimals(2)            
            self.scatter_sb.setValue(self.parent.scatter_selection)
            
            hbox = QtWidgets.QHBoxLayout()
            description = QtWidgets.QLabel(self.tr("Scatter amount"))
            hbox.addWidget(self.scatter_sb)
            hbox.addWidget(description)
            hbox.addStretch(1)
            group_vbox.addLayout(hbox)

        if self.parent.title_enabled:
            self.title_cb = QtWidgets.QCheckBox(self.tr("Title"))
            if self.parent.title_selection:
                self.title_cb.setChecked(True)
            group_vbox.addWidget(self.title_cb)

        if self.parent.legend_enabled:    
            self.legend_cb = QtWidgets.QCheckBox(self.tr("Legend"))
            if self.parent.legend_selection:
                self.legend_cb.setChecked(True)
            group_vbox.addWidget(self.legend_cb)

        if self.parent.grid_enabled:       
            self.grid_cb = QtWidgets.QCheckBox(self.tr("Grid"))
            if self.parent.grid_selection:
                self.grid_cb.setChecked(True)
            group_vbox.addWidget(self.grid_cb)

        group_area.setLayout(group_vbox)
        
        if self.parent.grid_enabled or self.parent.legend_enabled or self.parent.title_enabled or\
                self.parent.dotsize_enabled or self.parent.linewidth_enabled or self.parent.scatter_enabled:
            vbox.addWidget(group_area)

        scroll_area = QtWidgets.QScrollArea()
        checkbox_widget = QtWidgets.QWidget()
        checkbox_vbox = QtWidgets.QVBoxLayout()

        for i in range(len(self.dataset_cb)):
            self.dataset_cb[i].setMinimumWidth(400) # prevent obscured text
            checkbox_vbox.addWidget(self.dataset_cb[i])

        checkbox_widget.setLayout(checkbox_vbox)
        scroll_area.setWidget(checkbox_widget)
        vbox.addWidget(scroll_area)

        ### Buttonbox for ok ###
        hbox = QtWidgets.QHBoxLayout()
        buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
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

        if self.parent.scatter_enabled: 
            self.parent.scatter_selection = self.scatter_sb.value()
            
        self.parent.plot_selection = []
        for i in range(len(self.dataset_cb)):
            if self.dataset_cb[i].isChecked():
                self.parent.plot_selection.append(i)

        self.parent.on_draw()
        self.close()