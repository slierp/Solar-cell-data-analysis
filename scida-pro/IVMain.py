# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
from IVMainGui import IVMainGui
import sys
import Required_resources

if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if not app:
        # if no other PyQt program is running (such as the IDE) create a new instance
        app = QtWidgets.QApplication(sys.argv)       
    
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            print("Solar cell data analysis")
            print("Options:")
            print("--h, --help  : Help message")
            exit()

    app.setStyle("windows")        
    window = IVMainGui()
    window.show()
    app.exec_()   