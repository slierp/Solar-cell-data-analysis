# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='scida-pro',
      version='1.5.1',
      description='Solar cell data analysis using python modules pandas, matplotlib and pyqt',
      url='https://github.com/slierp/Solar-cell-data-analysis',
      author='Ronald Naber',
      license='Public domain',
      packages=['scida-pro'],
      package_data={'scida-pro': ['*.csv'],},
      zip_safe=False,
      classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Environment :: Win32 (MS Windows)',
      'Environment :: X11 Applications',
      'Environment :: X11 Applications :: Qt',
      'Operating System :: OS Independent',
      'Intended Audience :: End Users/Desktop',
      'Intended Audience :: Science/Research',
      'Programming Language :: Python',
      'Topic :: Scientific/Engineering'])

