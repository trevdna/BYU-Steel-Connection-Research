# BYU-Steel-Connection-Research
Shallowly Embedded Steel Connection Research - FEA Automation Code

This is the online code repository for my FEA model generation. This is in conjunction with the research into shallowly embedded steel-concrete connections being performed by Dr. Paul Richards, Department of Civil Engineering, at Brigham Young University.

I will spend more time at a later date explaining the code in greater depth. For now, however, the steps to running it are as follows:

1) You will need to run it on a Linux machine as the code now stands. Earlier, more primitive versions would run on Windows machines. Please reach out to me or to Dr. Richards if you would like access to these scripts.
2) Download the 3 files onto a local machine: RunMe.py, Preprocessing.py, and scripts.py. 
3) Near the bottom of Preprocessing.py, there are several pre-loaded experiments. Room is available for two parameters, which can vary depending on the values input into the list, a list of blockout depths, and a list of model types. Input your preferred parameters for each of these, for each experiment you want to run.
4) In the command line, run "python /MYFILEPATHHERE/RunMe.py" in the command line (where "MYFILEPATHHERE" is obviously whatever folder you are working from.
5) Hopefully, no bugs come up, and all models run correctly. In several minutes to hours, your models will have run, and you will have one or several .csv files as outputs, waiting for your analysis in the "Models" folder, which is an automatically created folder for holding on to your models and output files.


Briefly, these files contain the following:
    *RunMe: This file contains the top-level commands that interact with the operating system. It copies the file "Preprocessing" twice, titling the copies "Processing" and "Postprocessing". It commands the OS to run the Preprocessing script in Abaqus CAE, then for Python to run the Processing script, then for Abaqus CAE to run the Postprocessing script.
    *Preprocessing: 
