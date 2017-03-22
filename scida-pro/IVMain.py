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
    
    app.setStyle("windows")       
    window = IVMainGui()        
    window.show()
    app.exec_()
    sys.exit()    