#Supercomputer usage?
supercomputer = 0

#Discover OS & Python version in use
import sys
if sys.platform == 'win32' or sys.platform == 'win64': 
	windows = True
else:
	windows = False
linux = not(windows)
if supercomputer: assert linux
pythonVersionNum = sys.version_info[0]

import os
from shutil import copy

#For getting current source file
from inspect import getsourcefile
from os.path import abspath
absFilePath = abspath(getsourcefile(lambda:0))
if windows: dirChar = '\\'
else:  dirChar = '/'
scriptsFilePath = absFilePath.rsplit(dirChar, 1)[0]
modelsFilePath = os.path.join(scriptsFilePath, 'Models')
if not os.path.exists(modelsFilePath): os.makedirs(modelsFilePath)

if linux:
	os.chdir(modelsFilePath)
	guiCaps = 'GUI'
	if supercomputer:
		os.system('module load abaqus/6.14')#Module for 6.16 needs loading?
else: #Windows
	guiCaps = 'gui'


#Copy template (Preprocessing.py) to main and post-processing scripts, overwriting old files.
#Forcibly prevents discrepancies in the 3 files (esp. in batches to run)
copy(os.path.join(scriptsFilePath, 'Preprocessing.py'), os.path.join(scriptsFilePath, 'Processing.py'))
copy(os.path.join(scriptsFilePath, 'Preprocessing.py'), os.path.join(scriptsFilePath, 'Postprocessing.py'))

##########
#RUN ME!!#
##########
print('\nBeginning preprocessing...')
os.system('abaqus.old cae no%s=%s' %(guiCaps, os.path.join(scriptsFilePath, 'Preprocessing')))
print('\nPreprocessing complete. Beginning main processing...')
os.system('python %s' %os.path.join(scriptsFilePath, 'Processing.py'))
print('\nMain processing complete. Beginning postprocessing...')
os.system('abaqus.old cae no%s=%s' %(guiCaps, os.path.join(scriptsFilePath, 'Postprocessing')))
print('Done!')