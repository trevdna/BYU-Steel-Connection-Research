# BYU-Steel-Connection-Research
Shallowly Embedded Steel Connection Research - FEA Automation Code

This is the online code repository for my FEA model generation. This is in conjunction with the research into shallowly embedded steel-concrete connections being performed by Dr. Paul Richards, Department of Civil Engineering, at Brigham Young University.

The steps to running it are as follows:

1) You will need to run it on a Linux machine as the code now stands. Earlier, more primitive versions would run on Windows machines. Please reach out to me or to Dr. Richards if you would like access to these scripts.
2) Download the 4 files onto a local machine: RunMe.py, Preprocessing.py, scripts.py, and ShapesDatabase.csv. 
3) Near the bottom of Preprocessing.py, there are several pre-loaded experiments. Room is available for two parameters, which can vary depending on the values input into the list, a list of blockout depths, and a list of model types. Input your preferred parameters for each of these, for each experiment you want to run.
4) In the command line, run "python /MYFILEPATHHERE/RunMe.py" in the command line (where "MYFILEPATHHERE" is obviously whatever folder you are working from.
5) Hopefully, no bugs come up, and all models run correctly. In several minutes to hours, your models will have run, and you will have one or several .csv files as outputs, waiting for your analysis in the "Models" folder, which is an automatically created folder for holding on to your models and output files.

If you want to understand how these files work, a basic understanding of the Python programming language (as well as a little bit of knowledge of object oriented programming in general) will help. The explanations that follow will assume both.

Briefly, these files contain the following:

*RunMe.py: This file contains the top-level commands that interact with the operating system. It copies the file "Preprocessing" twice, titling the copies "Processing" and "Postprocessing". It commands the OS to run the Preprocessing script in Abaqus CAE, then for Python to run the Processing script, then for Abaqus CAE to run the Postprocessing script.

*Preprocessing.py: This file serves as a template for "preprocessing", "processing" and "postprocessing" files. This was done so that any changes (especially to the experiments but also to the underlying code) would be automatically sent out to the other two, preventing problems created by discrepancies between the files. When preprocessing is run, it does the following:
- Creates experiment objects that hold values definining what parameters are to be varied in each experiment.
- Takes the values in the experiment object to create a DataArray object for each model that is to be built. Each DataArray object holds a dictionary of parameters ("paramsDict"). It initializes each paramsDict with default values, and then changes any values that are to be overwritten (based on the parameters from the experiment object).
- Once the paramsDict is built, it runs the "preprocess" routine, which uses the parameters in the paramsDict to call each of the necessary subroutines to build the model in Abaqus, in turn. Each of these subroutines is contained in scripts.py, which were imported when preprocess.py was initialized.
- This process is repeated for each model. By the time this routine has finished, there is a ".inp" file for each DataArray, which represents the model - its geometry, boundary conditions, loads, etc. - to the Abaqus solver. Also, the ".cae" file can be opened in the Abaqus/CAE viewer.
            
*Processing.py: When processing.py is run, it will do everything that Preprocessing.py did with respect to creating experiment and DataArray objects. However, instead of creating a ".inp" file for each model, it will instead take each existing ".inp" file in the experiments you have listed, and submit them to the Abaqus solver to run in parallel. You will probably be limited by the number of licenses available; most of your submissions will probably wait in line for a turn a the license. This is normal. There is no particular order in which these run. Processing will create many files, but the most important are the ".odb" file and the ".output" file. The ".odb" is the output database, and can be opened and viewed in the Abaqus/CAE viewer. The ".output" file holds the displacement value that will be scraped by the "Postprocessing.py" file.
    
*Postprocessing.py: When Postprocessing.py is run, it will do everything that Preprocessing.py did with respect to creating experiment and DataArray objects. Once it has done that, it will take each ".output" file corresponding to the models in each of your experiments, and scrape the displacement values from that file. It will then calculate lateral stiffness and rotational stiffness values, and export that information - along with information about the model and the timestamp - to a .csv file for further analysis.

*scripts.py: This contains the subroutines that contain the necessary commands to build the models in Abaqus.

*ShapesDatabase.csv: This database contains information about the steel shapes' cross sections that is needed for the automated lookups. It is based on the spreadsheet at structuresworkshop.com/files/AISC_Shapes_Database_v13.2.xls, but is formatted to run with these scripts.


To-Dos in this README:

* Explain the subroutines in scripts.py
* Explain that I need to use "abaqus-old" to access 6.14, and why (better results).
* Explain the bug when run on Windows machine
* Post older code that will run on Windows machine (though not as efficient)
* Explain the supercomputer usage
* Explain the unpublished information about the preliminary results that justified some of my assumptions/simplifications.
* Explain future research directions / roads not travelled: weak-axis bending; using concrete-specific material properties instead of cohesive zone models; working more closely w/ Dr. Scott.
