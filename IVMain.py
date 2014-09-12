# -*- coding: utf-8 -*-
"""
Created on Fri Sep 12 20:16:51 2014

@author: rnaber
"""
from __future__ import division
from PyQt4 import QtGui
from IVMainGui import IVMainGui
import sys
import Required_resources

if __name__ == "__main__":
    app = QtGui.QApplication.instance()
    if not app:
        # if no other PyQt program is running (such as the IDE) create a new instance
        app = QtGui.QApplication(sys.argv)       
    
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            print "Solar cell data analysis"
            print "Options:"
            print "--h, --help  : Help message"
            exit()
        
    window = IVMainGui()
    window.show()
    app.exec_()