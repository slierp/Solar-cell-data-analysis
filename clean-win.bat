rmdir build /s /q
rmdir dist /s /q
rmdir scida_pro.egg-info /s /q
cd scida-pro
del *.c
del *.pyc
del *.pyd
rmdir __pycache__ /s /q
cd ..
pause
