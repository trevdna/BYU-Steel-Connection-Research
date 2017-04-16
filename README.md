# BYU-Steel-Connection-Research
Shallowly Embedded Steel Connection Research - FEA Automation Code

This is the online code repository for my FEA model generation. This is in conjunction with the research into shallowly embedded steel-concrete connections being performed by Dr. Paul Richards, Department of Civil Engineering, at Brigham Young University.

I will spend more time at a later date explaining the code in greater depth. For now, however, the steps to running it are as follows:

1) You will need to run it on a Linux machine as the code now stands. Earlier, more primitive versions would run on Windows machines. Please reach out to me or to Dr. Richards if you would like access to these scripts.
2) Download the 3 files onto a local machine: RunMe.py, Preprocessing.py, and scripts.py. 


Briefly, these files contain the following:
    *RunMe: This file contains the top-level commands that interact with the operating system. It copies the file "Preprocessing" twice, titling the copies "Processing" and "Postprocessing". It commands the OS to run the Preprocessing script in Abaqus CAE, then for Python to run the Processing script, then for Abaqus CAE to run the Postprocessing script.
    *Preprocessing: 
