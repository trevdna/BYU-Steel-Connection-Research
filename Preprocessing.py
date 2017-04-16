#Refactor of preprocessing tasks as of 9/14/16. To be run solely in Abaqus/CAE but tested in Python.

'''Outline:
*Start with structured data that tells: what experiments we want to run, and what we want the variables to be in those experiments.
*Assert the data is correctly entered.
*Create objects that store each experiment.
*In those objects, have data that corresponds to primary parameter, secondary parameter, and the various values those are to take.
*In each object: have methods that automatically populate a dictionary (once DataArray - now call it whatever we want) with the correct parameters.
*Use the objects to call methods from Scripts with the actual methods to run. No "preprocessing" necessary in the scripts library.

'''

#Supercomputer usage?
supercomputer = 0

#Discover OS & Python version in use
import sys
if sys.platform == 'win32' or sys.platform == 'win64': 
	windows = True
else:
	windows = False
linux = not(windows)
pythonVersionNum = sys.version_info[0]

if supercomputer: assert linux

#Create file path string & chdir
import os

#For getting current source file
from inspect import getsourcefile
from os.path import abspath
absFilePath = abspath(getsourcefile(lambda:0))
if windows: dirChar = '\\'
else:  dirChar = '/'
scriptsFilePath = absFilePath.rsplit(dirChar, 1)[0]
modelsFilePath = os.path.join(scriptsFilePath, 'Models')
if not os.path.exists(modelsFilePath): os.makedirs(modelsFilePath)
sys.path.append(scriptsFilePath)

scriptsFileName = absFilePath.rsplit(dirChar, 1)[1]
preProcessingScript = 0
mainProcessingScript = 0
postProcessingScript = 0
if scriptsFileName == 'Preprocessing.py': 	preProcessingScript = 1
elif scriptsFileName == 'Processing.py': mainProcessingScript = 1
elif scriptsFileName == 'Postprocessing.py': postProcessingScript = 1
else: raise(NameError)

#Remaining import lines
import csv
import multiprocessing
import pdb
if pythonVersionNum == 2: from string import join

if pythonVersionNum == 3: from imp import reload
if not mainProcessingScript:
	try:
		reload(scripts)
	except NameError:
		import scripts

#Dictionary with part names and properties
PropertiesDict = {}
ShapesDatabase = os.path.join(scriptsFilePath, 'ShapesDatabase.csv')
# if supercomputer: ShapesDatabase = filePath + 'InputDatabases/ShapesDatabase_Custom.csv'

propDict = {}
with open(ShapesDatabase) as csvfile:
	quoting = csv.QUOTE_NONNUMERIC
	reader = csv.reader(csvfile)
	for row in reader: propDict[row[0]] = row[3], row[4], row[6], row[8], row[11], row[18], row[22]
'''0: bA - Beam area
1: db - Beam depth 
2: bf - Flange width
3: tw - Thickness of web
4: tf - Thickness of flange
5: Ix - Strong moment of inertia
6: Iy - Weak moment of inertia'''

class DataArray(object):
	def __init__(self, firstParam, firstParamEntry, secondParam, secondParamEntry, modelTypeEntry, blockoutEntry):
			
		def __removeDot(foo):
			if pythonVersionNum == 2:
				return join(str(foo).split('.'),'pt')
			else:#Python 3.X - probably more brittle but should be OK.
				foo = str(foo) 
				bar = str(foo).split('.')
				if len(bar) == 2:
					return bar[0] + 'pt' + bar[1]
				elif len(bar) == 1:
					return bar[0]
				else:
					raise TypeError

		#Bug prevention assertions
		pass
	
		#Required properties
		self.modelType = 'CohesiveZoneModel'
		self.strongOrient = True
		self.baseplate = True #Is there a baseplate?
		self.columnName = 'W8X48'
		self.Z = 80.25 #Cantilever height
		self.blockoutDepth = 6.5 #blockoutDepth #Total blockout depth, not counting grout in Barnwell's experiments beneath
		self.bpWX = 13 #BasePlate Width, X-dir
		self.bpWY = 13 #BasePlate Width, Y-dir
		self.baseDepth = 1.0
		self.baseplateType = 'Square'
		self.fWX = 42.0 #Foundation Width in the X-dir
		self.fWY = 42.0 #Foundation Width in the Y-dir
		self.botFD = 24.0 #bottom Foundation Depth
		self.steelMod   = 29000000.0
		self.concreteMod = 3500000.0
		self.steelPoisson = 0.27
		self.concretePoisson = 0.15
		self.appliedLoad = 1000 #pounds
		self.axialLoad = 0.0 #pounds
		self.meshSize = 0.5
		self.boundaryConditions = "Default"
		
		#Overrides
		if type(firstParamEntry) is str:
			exec('self.%s="%s"' %(firstParam, firstParamEntry)) in globals(), locals()
		else:
			exec('self.%s=%s' %(firstParam, firstParamEntry)) in globals(), locals()
		if type(secondParamEntry) is str:
			exec('self.%s="%s"' %(secondParam, secondParamEntry)) in globals(), locals()
		else:
			exec('self.%s=%s' %(secondParam, secondParamEntry)) in globals(), locals()
			
		exec('self.%s=%s' %("blockoutDepth", blockoutEntry)) in globals(), locals()
		exec('self.%s="%s"' %("modelType", modelTypeEntry)) in globals(), locals()

		#Additional, optional overrides
		if self.baseplateType == 'Rectangle': pass
		pass #More special cases
		
		#Type assertions
		pass

		#Derived quantities
		if self.modelType == 'CohesiveZoneModel':
			if not 'cohesiveMod' in [firstParam, secondParam]: self.cohesiveMod = 5E4
			self.cohThk = 0.01 #COHesive zone THicKness
		if self.modelType == 'Contact': self.Friction = 0.2
		self.bA = float(propDict[self.columnName][0])
		self.db = float(propDict[self.columnName][1])
		self.bf = float(propDict[self.columnName][2])
		self.tw = float(propDict[self.columnName][3])
		self.tf = float(propDict[self.columnName][4])
		self.Ix = float(propDict[self.columnName][5])
		self.Iy = float(propDict[self.columnName][6])
		self.bA = self.db * self.tw + 2 * self.bf * self.tf - 2 * self.tf * self.tw #I think it is better to use calculated values than look it up from the AISC Manual
		self.embedDepth = self.blockoutDepth - self.baseDepth #Changing from an embedDepth-centered to a blockoutDepth-centered paradigm.
		# self.blockoutDepth = self.embedDepth + self.baseDepth
		self.columnLength = self.embedDepth + self.Z
		self.tFD = self.blockoutDepth + self.botFD #total foundation depth
		self.bpTop = self.tFD - self.embedDepth #BasePlate Top height
		self.bpTop = self.tFD - self.embedDepth #BasePlate Top height
		if self.columnName == 'W14X53':
			self.bpWX = 12.0
			self.bpWY = 15.0
			self.baseDepth = 2.25
			
		elif self.columnName == 'W10X77':
			self.bpWX = 18.0
			self.bpWY = 12.0
			self.baseDepth = 3.0
		
		#Sanity check assertions
		assert self.baseplateType == 'Square' or self.baseplateType == 'Rectangle' or self.baseplateType == 'Reduced' or self.baseplateType == 'None'
		if self.strongOrient:
			assert self.bpWX >= self.bf
		else:
			assert self.bpWX >= self.db
		assert self.modelType == modelTypeEntry
		
		#Bug-prevention assertions - for functionality that is either deprecated or not yet supported.
		assert self.baseplate == True
		
		#Derived metadata
		self.modelName = '%s#%s_%s#%s_blktDep#%s_mdlType#%s' %(firstParam, __removeDot(firstParamEntry), secondParam, __removeDot(secondParamEntry), __removeDot(blockoutEntry), modelTypeEntry)
		print(self.modelName)
		self.mdbFileName = os.path.join(modelsFilePath, (self.modelName + '.mdb'))
		self.odbFileName = os.path.join(modelsFilePath, (self.modelName + '.odb'))
		self.outputFileName = os.path.join(modelsFilePath, (firstParam + '_' + secondParam + '.csv'))
		if self.modelName == 'onePartModel': self.columnPartName = 'CombinedPart'
		else: self.columnPartName = 'Column'
			

		#Create parameters dictionary
		self.paramsDict = {}
		for key in list(self.__dict__.keys()):
			exec('self.paramsDict["%s"]="%s"' %(key, self.__dict__[key])) in globals(), locals()
		del self.paramsDict['paramsDict']#weird bug here!
	
	def preProcess(self):
		Mdb() #Exit any open model database file, create a new, blank one. 
		scripts.createModel(self.paramsDict)
		scripts.createColumnPart(self.paramsDict)
		scripts.divideColumnPart(self.paramsDict)
		scripts.createColumnSet(self.paramsDict)
		scripts.createFoundationPart(self.paramsDict)
		scripts.divideFoundationPart(self.paramsDict)
		scripts.createMaterialDefinitions(self.paramsDict)
		scripts.createSectionDefinitions(self.paramsDict)
		scripts.assignSections(self.paramsDict)
		scripts.createLoadStep(self.paramsDict)
		scripts.instanceParts(self.paramsDict)
		scripts.createContactProperties(self.paramsDict)
		scripts.seedMesh(self.paramsDict)
		scripts.generateMesh(self.paramsDict)
		scripts.createBoundaryConditions(self.paramsDict)
		scripts.createRigidTopConstraint(self.paramsDict)
		scripts.createAppliedLoad(self.paramsDict)
		scripts.createJob(self.paramsDict)
		scripts.createHistoryOutputRequest(self.paramsDict)
		scripts.writeInputFile(self.paramsDict) #to run in processing
		scripts.saveModelFile(self.paramsDict)#to open in postprocessing
		
	def preProcessTest(self):
		testDict = {}
		for key in list(self.__dict__.keys()):
			exec('testDict["%s"]="%s"' %(key, self.__dict__[key]))
			print('Key = ' + str(key) + ' , value = ' + str(self.__dict__[key]))

	def postProcess(self, firstParam, firstParamEntry, secondParam, secondParamEntry, blockoutEntry, modelTypeEntry):
		session.openOdb(name=self.odbFileName)
		openMdb(pathName=self.mdbFileName)
		scripts.checkOutputFile(self.paramsDict)
		scripts.findDisplacementAndOutput(self.paramsDict, firstParam, firstParamEntry, secondParam, secondParamEntry, blockoutEntry, modelTypeEntry)

def _experimentWrapper__process(ModelName):
	print("abaqus.old job=%s cpus=4 interactive ask_delete=OFF" %ModelName) 
	os.system("abaqus.old job=%s cpus=4 interactive ask_delete=OFF" %ModelName) 
	return

class experimentWrapper(object):
	def __init__(self):
		self.values = ['']
		
	def __setitem__(self, key, object):
		self.values += ['']
		self.values[key] = object
		
	def __getitem__(self, key):
		return self.values[key]

	def populate(self, firstParam, firstParamList, secondParam, secondParamList, modelTypeList, blockoutList):
		for firstParamEntry in firstParamList:
			for secondParamEntry in secondParamList:
				for modelTypeEntry in modelTypeList:
					for blockoutEntry in blockoutList:
						valLength = len(self.values)
						self[valLength] = DataArray(firstParam, firstParamEntry, secondParam, secondParamEntry, modelTypeEntry, blockoutEntry)
						if __name__ == '__main__': self.values[valLength].preProcessTest()
						if preProcessingScript == True:
							self.values[valLength].preProcess()
						elif postProcessingScript == True:
							self.values[valLength].postProcess(firstParam, firstParamEntry, secondParam, secondParamEntry, blockoutEntry, modelTypeEntry)

	def mainProcessing(self, firstParamList, secondParamList, modelTypeList, blockoutList):
		multiprocessing.freeze_support()#Not really working for Windows. Linux only I guess.
		#Define maxProcesses
		numModels = len(firstParamList) * len(secondParamList) * len(modelTypeList) * len(blockoutList)
		maxCPUS = multiprocessing.cpu_count()
		if linux: maxCPUS *= 0.5
		maxProcesses = int(min(numModels, maxCPUS / 4))

		modelNamesList = []
		for index in range(1, len(self.__dict__['values'])):
			dataArray = self.__dict__['values'][index]
			modelNamesList += [dataArray.modelName]
		try:
			pool = multiprocessing.Pool(processes=maxProcesses)#There's probably a cleaner way to do this, but this seems to work fine.
			pool.map(__process, modelNamesList)
		except RuntimeError: #Does not work for Windows...
			print("FAILED! Run only on Linux for now.")

	def mainProcessingTest(self, firstParamList, secondParamList, modelTypeList, blockoutList):
		for index in range(1, len(self.__dict__['values'])):
			dataArray = self.__dict__['values'][index]
			print("\nThe modelName associated with the dataArray object is " + dataArray.modelName + "/n")

##########################################
#BATCH LISTS FOR TESTING & CODE EXECUTION#
##########################################
# Nick's First shapes (from thesis)#
# firstParam = 'columnName'
# firstParamList = ['W8X35', 'W8X48']
# secondParam = 'baseDepth'
# secondParamList = [1.0]
# modelTypeList = ['CohesiveZoneModel', 'RigidTie', 'Contact']
# blockoutList = [2.5, 4.5, 6.5, 8.5, 10.5, 14.5, 16.5, 18.5]

# experiment0 = experimentWrapper()
# experiment0.populate(firstParam, firstParamList, secondParam, secondParamList, modelTypeList, blockoutList)
# if mainProcessingScript: experiment0.mainProcessing(firstParamList, secondParamList, modelTypeList, blockoutList)
# ##########################################
#Kevin's D2 & D3#
# firstParam = 'columnName'
# firstParamList = ['W14X53']
# secondParam = 'baseDepth'
# secondParamList = [2.25]
# modelTypeList = ['CohesiveZoneModel', 'RigidTie']
# blockoutList = [float(x - secondParamList[0]) for x in range(4, 16)]
# blockoutList = [float(x) for x in range(4, 16)]
# blockoutList = [float(16)]

# experiment1 = experimentWrapper()
# experiment1.populate(firstParam, firstParamList, secondParam, secondParamList, modelTypeList, blockoutList)
# if mainProcessingScript: experiment1.mainProcessing(firstParamList, secondParamList, modelTypeList, blockoutList)
# ##########################################
#Kevin's D series#
# firstParam = 'columnName'
# firstParamList = ['W14X53']
# secondParam = 'cohesiveMod'
# secondParamList = [5E3, 1E4, 5E4, 1E5, 5E5, 1E6]
# modelTypeList = ['CohesiveZoneModel']
# blockoutList = [float(x) for x in range(4, 17)]
# blockoutList = [float(16)]

# experiment2 = experimentWrapper()
# experiment2.populate(firstParam, firstParamList, secondParam, secondParamList, modelTypeList, blockoutList)
# if mainProcessingScript: experiment2.mainProcessing(firstParamList, secondParamList, modelTypeList, blockoutList)
# ########################################### 
##########################################
#Kevin's F series#
# firstParam = 'columnName'
# firstParamList = ['W10X77']
# secondParam = 'cohesiveMod'
# secondParamList = [5E3, 1E4, 5E4, 1E5, 5E5, 1E6]
# modelTypeList = ['CohesiveZoneModel']
# blockoutList = [float(x) for x in range(4, 17)]
# blockoutList = [float(16)]

# experiment2 = experimentWrapper()
# experiment2.populate(firstParam, firstParamList, secondParam, secondParamList, modelTypeList, blockoutList)
# if mainProcessingScript: experiment2.mainProcessing(firstParamList, secondParamList, modelTypeList, blockoutList)
# ##########################################
#Kevin's F2 & F3#
# firstParam = 'columnName'
# firstParamList = ['W10X77']
# secondParam = 'baseDepth'
# secondParamList = [3.0]
# modelTypeList = ['CohesiveZoneModel', 'RigidTie']
#blockoutList = [float(x - secondParamList[0]) for x in range(4, 16)]
# blockoutList = [float(x) for x in range(4, 16)]
# blockoutList = [float(16)]

# experiment3 = experimentWrapper()
# experiment3.populate(firstParam, firstParamList, secondParam, secondParamList, modelTypeList, blockoutList)
# if mainProcessingScript: experiment3.mainProcessing(firstParamList, secondParamList, modelTypeList, blockoutList)
# ##########################################
#Kevin's F4#
# firstParam = 'columnName'
# firstParamList = ['W10X77']
# secondParam = 'baseDepth'
# secondParamList = [2.0]
# modelTypeList = ['CohesiveZoneModel', 'RigidTie']
#blockoutList = [float(x - secondParamList[0]) for x in range(4, 16)]
# blockoutList = [float(x) for x in range(4, 16)]

# experiment4 = experimentWrapper()
# experiment4.populate(firstParam, firstParamList, secondParam, secondParamList, modelTypeList, blockoutList)
# if mainProcessingScript: experiment4.mainProcessing(firstParamList, secondParamList, modelTypeList, blockoutList)
# ##########################################
firstParam = 'columnName'
firstParamList = ['W8X48']
secondParam = 'Z'
secondParamList = [83.25]
modelTypeList = ['CohesiveZoneModel']
blockoutList = [2.5, 4.5, 6.5, 8.5, 10.5, 14.5, 16.5, 18.5]

experiment5 = experimentWrapper()
experiment5.populate(firstParam, firstParamList, secondParam, secondParamList, modelTypeList, blockoutList)
if mainProcessingScript: experiment5.mainProcessing(firstParamList, secondParamList, modelTypeList, blockoutList)
# ##########################################
# firstParam = 'columnName'
# firstParamList = ['W8X35']
# secondParam = 'cohesiveMod'
# secondParamList = [10000.0, 50000.0, 100000.0]
# modelTypeList = ['Contact']
# blockoutList = [2.5, 4.5, 6.5, 8.5, 10.5, 14.5, 16.5, 18.5]

# experiment6 = experimentWrapper()
# experiment6.populate(firstParam, firstParamList, secondParam, secondParamList, modelTypeList, blockoutList)
# if mainProcessingScript: experiment6.mainProcessing(firstParamList, secondParamList, modelTypeList, blockoutList)
