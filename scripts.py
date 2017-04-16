##############################################
#Import lines and other initialization tasks.#
##############################################
from abaqus import *
from abaqusConstants import *
import __main__

import section
import regionToolset
import displayGroupMdbToolset as dgm
import part
import material
import assembly
import step
import interaction
import load
import mesh
import job
import sketch
import visualization
import xyPlot
import displayGroupOdbToolset as dgo
import connectorBehavior

from os import path #for checkOutputFile
from datetime import datetime #__timeStamp for outputValues
from string import upper #findDisplacement

session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)

#Helper methods

def __timeStamp():
	# global TimeStamp
	month = str(datetime.now().month)
	day = str(datetime.now().day)
	year = str(datetime.now().year)
	hour = str(datetime.now().hour)
	minute = str(datetime.now().minute)
	second = str(datetime.now().second)
	return '{0}-{1}-{2}_{3}-{4}-{5}'.format(month, day, year, hour, minute, second)

def __openwrite(outputFile):
	with open(outputFile, 'a') as f:
		f.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\n' %('Model Name', 'Model Type', 'Primary Parameter', 'Primary Value', \
			'Secondary Parameter', 'Secondary Value', 'Blockout Depth', 'Column Shape', 'Cantilever Height',\
			'Total Displacement', 'Connection Stiffness', 'Connection Rotational Stiffness', 'Timestamp'))

def __filter(largeGroup, filteredGroup):
	return filter(lambda x: x not in filteredGroup, largeGroup)

#Preprocessing methods
	
def createModel(paramsDict):
	modelName = paramsDict['modelName']
	mdb.Model(name=modelName, modelType=STANDARD_EXPLICIT)

def createColumnPart(paramsDict): 
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	s = mdb.models[modelName].ConstrainedSketch(name='__profile__', 
		sheetSize=200.0)
	g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
	s.setPrimaryObject(option=STANDALONE)
	if strongOrient:
		print(db)
		print(type(db))
		print(tf)
		print(type(tf))
		s.rectangle(point1=(0, (-db / 2) + tf), point2=((tw / 2),(db / 2) - tf))
		s.rectangle(point1=(0, -db/2), point2=(bf/2, -db/2 + tf))
		s.rectangle(point1=(0, db/2 - tf), point2=(bf/2, db/2))
		s.autoTrimCurve(curve1=g.findAt((bf / 2 - 0.001, -db/2 + tf)), point1=(0.001, -db/2 + tf))
		s.autoTrimCurve(curve1=g.findAt((0.001, -db/2 + tf)), point1=(0.001, -db/2 + tf))    
		s.autoTrimCurve(curve1=g.findAt((bf / 2 - 0.001, db/2 - tf)), point1=(0.001, db/2 - tf))
		s.autoTrimCurve(curve1=g.findAt((0.001, db/2 - tf)), point1=(0.001, db/2 - tf))
	else: #weak axis bending
		s.rectangle(point1=(0, tw/2), point2=(db/2 - tf, -tw/2))
		s.rectangle(point1=(db/2-tf, bf/2), point2=(db/2, -bf/2))
		s.autoTrimCurve(curve1=g.findAt((db/2 - tf, 0.0)), point1=((db/2 - tf, 0.0)))
		s.autoTrimCurve(curve1=g.findAt((db/2 - tf, 0.0)), point1=((db/2 - tf, 0.0)))

	p = mdb.models[modelName].Part(name='Column', dimensionality=THREE_D, 
		type=DEFORMABLE_BODY)
	p = mdb.models[modelName].parts['Column']
	p.BaseSolidExtrude(sketch=s, depth=columnLength)
	mdb.models[modelName].sketches.changeKey(fromName='__profile__', 
		toName='ColumnSketch')
	s.unsetPrimaryObject()
	
	#Column Part Division
	p = mdb.models[modelName].parts['Column']
	DatumPointID=p.DatumPointByCoordinate(coords=(0.0, 0.0, embedDepth)).id
	c = p.cells
	pickedCells = c.findAt(((0.0, 0.0, 0.0), ))
	e, v2, d = p.edges, p.vertices, p.datums
	if strongOrient:
		coord = (0.0, db / 2, embedDepth)
	else:
		coord = (0.0, tw/2, embedDepth)

	p.PartitionCellByPlanePointNormal(point=d[DatumPointID], normal=e.findAt(coordinates=coord), cells=pickedCells)
		
	#Add baseplate
	f = p.faces
	if strongOrient:
		coord1 = (tw/4, -db/4, 0.0)
		coord2 = (tw/2, 0.0, 0.0)
	else:
		coord1 = (db/2-tf/2, -bf/2, 0.0)
		coord2 = (db/2, 0.0, 0.0)
	t = p.MakeSketchTransform(sketchPlane=f.findAt(coordinates=coord1), sketchUpEdge=e.findAt(coordinates=coord2), 
		sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
	s = mdb.models[modelName].ConstrainedSketch(name='__profile__', 
		sheetSize=22.62, gridSpacing=0.56, transform=t)
	g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
	s.setPrimaryObject(option=SUPERIMPOSE)
	
	p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)

	s.rectangle(point1=(0, -bpWY / 2), point2=(bpWX / 2, bpWY / 2))
	
	p.SolidExtrude(sketchPlane=f.findAt(coordinates=coord1), 
		sketchUpEdge=e.findAt(coordinates=coord2), 
		sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s, depth=baseDepth, 
		flipExtrudeDirection=OFF)
	mdb.models[modelName].sketches.changeKey(fromName='__profile__', 
		toName='BaseplateSketch')
	s.unsetPrimaryObject()

def divideColumnPart(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass		
	p = mdb.models[modelName].parts['Column']
	c = p.cells
	f = p.faces
	if strongOrient:
		#Dividing the top-down face into rectangular cells
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bf/2 - (bf/2-tw/2)/2, db/2 - tf, Z/2)), cells=c[:])
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bf/2 - (bf/2-tw/2)/2, -db/2 + tf, Z/2)), cells=c[:])
	else:
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(db/2-tf, tw/2 +(bf/2-tw/2)/2, Z/2)), cells=c[:])

	#Divisions with baseplate involved
	if strongOrient:
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bf/2, db/2 - tf/2, bpTop + embedDepth/2)), cells=c[:])
	else:
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(db/2-tf/2, bf/2, bpTop + embedDepth/2)), cells=c[:])
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(db/2-tf/2, -bf/2, bpTop + embedDepth/2)), cells=c[:])
	if strongOrient:
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bpWX/4, 0,0)), cells=c[:])
	elif not strongOrient:
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(0.001, bpWY/4,0)), cells=c[:])

def createColumnSet(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	#Partition the top edge of the middle of the column
	p = mdb.models[modelName].parts['Column']
	e = p.edges
	pickedEdges = e.findAt(((0.0, 0.0, columnLength), ))
	p.PartitionEdgeByParam(edges=pickedEdges, parameter=0.5)
	#Create set for strong applied load
	v = p.vertices
	verts = v.findAt(((0.0, 0.0, columnLength), ))
	p.Set(vertices=verts, name='Set-1')	

def createFoundationPart(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	s = mdb.models[modelName].ConstrainedSketch(name='__profile__', 
		sheetSize=200.0)
	g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
	s.setPrimaryObject(option=STANDALONE)
	s.rectangle(point1=(0, -fWY/2), point2=(fWX/2, fWY/2))
	p = mdb.models[modelName].Part(name='Foundation', dimensionality=THREE_D, 
		type=DEFORMABLE_BODY)
		
	p = mdb.models[modelName].parts['Foundation']
	p.BaseSolidExtrude(sketch=s, depth=tFD)
	s.unsetPrimaryObject()
	del mdb.models[modelName].sketches['__profile__']

	#Cut hole for column.
	f, e = p.faces, p.edges
	t = p.MakeSketchTransform(sketchPlane=f.findAt(coordinates=(0.0, 0.0, 
		tFD)), sketchUpEdge=e.findAt(coordinates=(fWX/2, 0.0, tFD)), 
		sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 
		tFD))
	s1 = mdb.models[modelName].ConstrainedSketch(name='__profile__', 
		sheetSize=27.71, gridSpacing=0.69, transform=t)
	s1.setPrimaryObject(option=SUPERIMPOSE)
	p.projectReferencesOntoSketch(sketch=s1, filter=COPLANAR_EDGES)
	s1.retrieveSketch(sketch=mdb.models[modelName].sketches['ColumnSketch'])
	p.CutExtrude(sketchPlane=f.findAt(coordinates=(0.0, 0.0, tFD)), 
		sketchUpEdge=e.findAt(coordinates=(fWX/2, 0.0, tFD)), 
		sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s1, depth=embedDepth, 
		flipExtrudeDirection=OFF)
	s1.unsetPrimaryObject()
	del mdb.models[modelName].sketches['__profile__']

	#Cut hole for baseplate.
	if strongOrient:
		coord = (tw / 10, -db / 10, bpTop)
	else:
		coord = (db / 10, 0.0, bpTop)
	t = p.MakeSketchTransform(sketchPlane=f.findAt(coordinates=coord), 
		sketchUpEdge=e.findAt(coordinates=(0.0, 0.0, bpTop)), 
		sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 
		bpTop))
	s2 = mdb.models[modelName].ConstrainedSketch(name='__profile__', 
		sheetSize=27.71, gridSpacing=0.69, transform=t)
	s2.setPrimaryObject(option=SUPERIMPOSE)
	p.projectReferencesOntoSketch(sketch=s2, filter=COPLANAR_EDGES)
	s2.rectangle(point1=(0, -bpWY / 2), point2=(bpWX / 2, bpWY / 2))
	p.CutExtrude(sketchPlane=f.findAt(coordinates=coord), 
		sketchUpEdge=e.findAt(coordinates=(0.0, 0.0, bpTop)), 
		sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s2, depth=baseDepth, 
		flipExtrudeDirection=OFF)
	s2.unsetPrimaryObject()
	del mdb.models[modelName].sketches['__profile__']

def divideFoundationPart(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	p = mdb.models[modelName].parts['Foundation']
	c = p.cells
	f = p.faces

	#Dividing the top-down face into rectangular cells
	if strongOrient:
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bf/2, db/2 - tf/2, bpTop + embedDepth/2)), cells=c[:])
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bf/2 - (bf/2-tw/2)/2, db/2 - tf, bpTop + embedDepth/2)), cells=c[:])
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bf/2 - (bf/2-tw/2)/2, -db/2 + tf, bpTop + embedDepth/2)), cells=c[:])
	else:
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(db/2 - tf, tw/2 + 0.001, bpTop + embedDepth/2)), cells=c[:])
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(db/2-tf/2, bf/2 , bpTop + embedDepth/2)), cells=c[:])
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(db/2-tf/2,-bf/2, bpTop + embedDepth/2)), cells=c[:])

	#Nothing below here changes for strong/weak axis bending
	#Dividing the side-view face into rectangular cells
	if baseplateType == 'Square' or baseplateType == 'Rectangle':
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bpWX / 2 - 0.001, - bpWY / 2 + 0.001, bpTop)), cells=c[:])
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bpWX/4, -bpWY/2, bpTop-baseDepth/2)), cells=c[:])
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bpWX/4, bpWY/2, bpTop-baseDepth/2)), cells=c[:])
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates=(bpWX/4, 0, bpTop-baseDepth)), cells=c[:])
	else: #This will work for either a reduced bp or none at all.
		p.PartitionCellByExtendFace(extendFace=f.findAt(coordinates = (bf/4, db/2 - tf/4, bpTop-baseDepth)), cells=c[:]) 
	
	if modelType == 'CohesiveZoneModel':
		print(modelType)
		p = mdb.models[modelName].parts['Foundation']
		d, f, c = p.datums, p.faces, p.cells
		#Create datum planes to partition cohesive zones
		if strongOrient:
			topFlangeTopID = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=db/2 + cohThk).id
			topFlangeBotID = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=db/2 - tf - cohThk).id
			botFlangeTopID = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=-db/2 + tf + cohThk).id
			botFlangeBotID = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=-db/2 - cohThk).id
			webID = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=tw/2 + cohThk).id
			flangeEdgeID = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=bf/2 + cohThk).id
			#Create partitions
			p.PartitionCellByExtendFace(extendFace=f.findAt((bf/4, db/2, bpTop + embedDepth/2),), cells=c[:])
			p.PartitionCellByExtendFace(extendFace=f.findAt((bf/4, -db/2, bpTop + embedDepth/2),), cells=c[:])
			#Top flange top
			pickedCells = c.findAt((bf/4, db/2 + cohThk/2, bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[topFlangeTopID], cells=pickedCells)
			#Top flange bottom
			c = p.cells
			pickedCells = c.findAt((bf/4, db/2 - tf - cohThk/2, bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[topFlangeBotID], cells=pickedCells)
			#Bottom flange top
			c = p.cells
			pickedCells = c.findAt((bf/4, -db/2 + tf + cohThk/2, bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[botFlangeTopID], cells=pickedCells)
			#Bottom flange bottom
			c = p.cells
			pickedCells = c.findAt((bf/4, -db/2 - cohThk/2, bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[botFlangeBotID], cells=pickedCells)
			#Web
			c = p.cells
			pickedCells = c.findAt((tw/2 + cohThk/2,0.0, bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[webID], cells=pickedCells)
			#Top flange edge
			c = p.cells
			pickedCells = c.findAt((bf/2 + cohThk/2, db/2 - tf/2, bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[flangeEdgeID], cells=pickedCells)
			#Bottom flange edge
			c = p.cells
			pickedCells = c.findAt((bf/2 + cohThk/2, -db/2 + tf/2, bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[flangeEdgeID], cells=pickedCells)

			#Corners
			if baseplateType != 'Reduced' and baseplateType != 'None': #As it is, the corner divisions are only cosmetic (until I can actually assign them cohesive elements and properties). So, since the corners are giving me mesh problems for reduced baseplate models, I'll take them out.
				#Corners - sketch

				p = mdb.models[modelName].parts['Foundation']
				f, e, d = p.faces, p.edges, p.datums
				t = p.MakeSketchTransform(sketchPlane=f.findAt((tw/2 + cohThk + 0.001, 0.0, tFD),), sketchUpEdge=e.findAt((bf/2, 0.0, tFD),), 
					sketchPlaneSide=SIDE1, origin=(0.0, 0.0, tFD))
				s = mdb.models[modelName].ConstrainedSketch(
					name='__profile__', sheetSize=23.96, gridSpacing=0.59, transform=t)
				g, v, d1, c = s.geometry, s.vertices, s.dimensions, s.constraints
				s.setPrimaryObject(option=SUPERIMPOSE)
				p = mdb.models[modelName].parts['Foundation']
				p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)

				s.rectangle(point1=(bf/2, db/2), point2=(bf/2 + cohThk, db/2+cohThk))#Top flange, top corner
				s.rectangle(point1=(bf/2, db/2 - tf), point2=(bf/2 + cohThk, db/2 - tf - cohThk))#Top flange, bot corner
				s.rectangle(point1=(bf/2, -db/2 + tf), point2=(bf/2 + cohThk, -db/2 + tf + cohThk))#Bot flange, top corner
				s.rectangle(point1=(bf/2, -db/2), point2=(bf/2 + cohThk, -db/2 - cohThk))#Bot flange, bot corner

				p = mdb.models[modelName].parts['Foundation']
				f = p.faces
				pickedFaces = (f.findAt((bf/2 + cohThk, db/2 + cohThk, tFD),), f.findAt((bf/2 + cohThk, 0.0, tFD),), f.findAt((bf/2 + cohThk, -db/2 - cohThk, tFD),))
				e1, d2 = p.edges, p.datums
				p.PartitionFaceBySketch(sketchUpEdge=e1.findAt((bf/2, 0.0, tFD),), faces=pickedFaces, sketch=s)
				s.unsetPrimaryObject()
				del mdb.models[modelName].sketches['__profile__']

				#Corners - division

				p = mdb.models[modelName].parts['Foundation']
				c = p.cells
				e, d = p.edges, p.datums

				pickedCells1 = c.findAt((bf/2 + cohThk, db/2 + cohThk, bpTop + embedDepth/2),)
				pickedEdges1 =(e.findAt((bf/2+cohThk, db/2+cohThk/2, tFD),), e.findAt((bf/2 + cohThk/2, db/2+cohThk, tFD),)) #top flange top corner
				p.PartitionCellByExtrudeEdge(line=e.findAt((bf/2, db/2, tFD-0.001),), cells=pickedCells1, edges=pickedEdges1, 
					sense=FORWARD)

				pickedCells2 = c.findAt((bf/2 + cohThk + 0.001, 0.0, bpTop + embedDepth/2),)
				pickedEdges2 =(e.findAt((bf/2+cohThk, db/2-tf-cohThk/2, tFD),), e.findAt((bf/2+cohThk/2, db/2-tf-cohThk, tFD),)) #top flange bot corner
				p.PartitionCellByExtrudeEdge(line=e.findAt((bf/2, db/2-tf, tFD-0.001),), cells=pickedCells2, edges=pickedEdges2, 
					sense=FORWARD)

				pickedCells2 = c.findAt((bf/2 + cohThk + 0.001, 0.0, bpTop + embedDepth/2),)
				pickedEdges3 = (e.findAt((bf/2+cohThk, -db/2+tf+cohThk/2, tFD),), e.findAt((bf/2+cohThk/2, -db/2+tf+cohThk, tFD),)) #bot flange top
				p.PartitionCellByExtrudeEdge(line=e.findAt((bf/2, -db/2+tf, tFD-0.001),), cells=pickedCells2, edges=pickedEdges3, 
					sense=FORWARD)

				c = p.cells
				e, d = p.edges, p.datums
				pickedCells3 = c.findAt((bf/2 + cohThk, -db/2 - cohThk, bpTop + embedDepth/2),)
				pickedEdges4 = (e.findAt((bf/2+cohThk, -db/2-cohThk/2, tFD),), e.findAt((bf/2+cohThk/2, -db/2-cohThk, tFD),)) #bot flange bot
				p.PartitionCellByExtrudeEdge(line=e.findAt((bf/2, db/2, tFD-0.001),), cells=pickedCells3, edges=pickedEdges4, 
					sense=FORWARD)

		elif not strongOrient:
			webTopID = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=tw/2 + cohThk).id
			webBotID = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=-tw/2 - cohThk).id
			flangeLeftID = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=db/2 - tf - cohThk).id
			flangeRightID = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=db/2 + cohThk).id
			flangeTopID = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=bf/2 + cohThk).id
			flangeBotID = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=-bf/2 - cohThk).id

			#Create partitions
			p.PartitionCellByExtendFace(extendFace=f.findAt((db/2, 0.0, bpTop + embedDepth/2),), cells=c[:])
			#Web top
			c = p.cells
			pickedCells = c.findAt((db/4, tw/2 + cohThk, bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[webTopID], cells=pickedCells)
			#Web bot
			c = p.cells
			pickedCells = c.findAt((db/4, -tw/2 - cohThk, bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[webBotID], cells=pickedCells)
			#Flange Left
			c = p.cells
			pickedCells = c.findAt((db/2 - tf - cohThk, tw/2 + cohThk + 0.001, bpTop + embedDepth/2), )
			p.PartitionCellByDatumPlane(datumPlane=d[flangeLeftID], cells=pickedCells)
			c = p.cells
			pickedCells = c.findAt((db/2 - tf - cohThk, -tw/2 - cohThk - 0.001, bpTop + embedDepth/2), )
			p.PartitionCellByDatumPlane(datumPlane=d[flangeLeftID], cells=pickedCells)
			#Flange Right
			c = p.cells
			pickedCells = c.findAt((db/2 + cohThk, 0.0 , bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[flangeRightID], cells=pickedCells)
			#Flange Top
			c = p.cells
			pickedCells = c.findAt((db/2 - tf/2, bf/2 + cohThk , bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[flangeTopID], cells=pickedCells)
			#Flange Bot
			c = p.cells
			pickedCells = c.findAt((db/2 - tf/2, -bf/2 - cohThk , bpTop + embedDepth/2),)
			p.PartitionCellByDatumPlane(datumPlane=d[flangeBotID], cells=pickedCells)

		if baseplate: #Create divisions for the cohesive zone around the baseplate.
			bpBotID = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset = bpTop - baseDepth - cohThk).id
			bpTopID = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset = bpTop + cohThk).id
			bpUpID = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset = bpWY / 2 + cohThk).id
			bpDownID = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset = -bpWY / 2 - cohThk).id
			bpSideID = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset = bpWX / 2 + cohThk).id 

			d = p.datums
			f = p.faces
			c = p.cells
			if baseplateType == 'Square' or baseplateType == 'Rectangle':
				p.PartitionCellByExtendFace(extendFace=f.findAt((bpWX/2, 0.0, bpTop - baseDepth/2),), cells=c[:])
			c = p.cells
			pickedCells = c.getByBoundingBox(zMax = bpTop - baseDepth, xMax = bpWX / 2, yMin = -bpWY / 2, yMax = bpWY / 2)
			p.PartitionCellByDatumPlane(datumPlane=d[bpBotID], cells=pickedCells)
			c = p.cells
			pickedCells = c.getByBoundingBox(zMin = bpTop, xMax = bpWX / 2, yMin = -bpWY / 2, yMax = bpWY / 2)
			p.PartitionCellByDatumPlane(datumPlane=d[bpTopID], cells=pickedCells)
			if baseplateType == 'Square' or baseplateType == 'Rectangle':
				c = p.cells
				pickedCells = c.getByBoundingBox(xMax = bpWX / 2, yMin = bpWY / 2, zMin = bpTop - baseDepth, zMax = bpTop)
				p.PartitionCellByDatumPlane(datumPlane=d[bpUpID], cells=pickedCells)
				c = p.cells
				pickedCells = c.getByBoundingBox(xMax = bpWX / 2, yMax = -bpWY / 2, zMin = bpTop - baseDepth, zMax = bpTop)
				p.PartitionCellByDatumPlane(datumPlane=d[bpDownID], cells=pickedCells)
				c = p.cells
				pickedCells = c.getByBoundingBox(xMin = bpWX / 2, yMin = -bpWY / 2, yMax = bpWY / 2, zMin = bpTop - baseDepth, zMax = bpTop)
				p.PartitionCellByDatumPlane(datumPlane=d[bpSideID], cells=pickedCells)
		else:
			pass #For future researchers (who are interested): cohesive zones around the bottom of the column in the no baseplate case.

def createMaterialDefinitions(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	m = mdb.models[modelName]
	m.Material(name='Concrete')
	m.materials['Concrete'].Elastic(table=((
		concreteMod, concretePoisson), ))
	m.Material(name='Steel')
	m.materials['Steel'].Elastic(table=((
		steelMod, steelPoisson), ))
	if modelType == 'CohesiveZoneModel':
		m.Material(name='Cohesive')
		m.materials['Cohesive'].Elastic(type=TRACTION, table=((cohesiveMod, cohesiveMod/2, cohesiveMod/2), ))
	
def createSectionDefinitions(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	m = mdb.models[modelName]
	m.HomogeneousSolidSection(name='Foundation', 
		material='Concrete', thickness=None)
	m.HomogeneousSolidSection(name='Steel', 
		material='Steel', thickness=None)
	if modelType == 'CohesiveZoneModel':
		m.CohesiveSection(name='Cohesive', material='Cohesive', response=TRACTION_SEPARATION, 
			outOfPlaneThickness=None)
	
def assignSections(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	#Column
	p = mdb.models[modelName].parts['Column']
	c = p.cells
	cells = c[:]
	region = regionToolset.Region(cells=cells)
	p.SectionAssignment(region=region, sectionName='Steel', offset=0.0, 
		offsetType=MIDDLE_SURFACE, offsetField='', 
		thicknessAssignment=FROM_SECTION)
	#Foundation

	#Cohesive zone cells, if needed
	p = mdb.models[modelName].parts['Foundation']
	c = p.cells
	if modelType == 'CohesiveZoneModel':#Assign the cohesive zone section to those areas that are in the cohesive zone.
		if strongOrient:
			cells1 = c.findAt(((bf/4, db/2 + cohThk/2, bpTop + embedDepth/2),))
			cells2 = c.findAt(((bf/4, db/2 - tf - cohThk/2, bpTop + embedDepth/2),))
			cells3 = c.findAt(((bf/4, -db/2 + tf + cohThk/2, bpTop + embedDepth/2),))
			cells4 = c.findAt(((bf/4, -db/2 - cohThk/2, bpTop + embedDepth/2),))
			cells5 = c.findAt(((tw/2 + cohThk/2,0.0, bpTop + embedDepth/2),))
			cells6 = c.findAt(((bf/2 + cohThk/2, db/2 - tf/2, bpTop + embedDepth/2),))
			cells7 = c.findAt(((bf/2 + cohThk/2, -db/2 + tf/2, bpTop + embedDepth/2),))
			pass #corners
			cohesiveCells = cells1 + cells2 + cells3 + cells4 + cells5 + cells6 + cells7
		elif not strongOrient:
			cells1 = c.findAt(((db/4, tw/2 + cohThk/2, bpTop + embedDepth/2),))
			cells2 = c.findAt(((db/4, -tw/2 - cohThk/2, bpTop + embedDepth/2),))
			cells3 = c.findAt(((db/2 - tf - cohThk/2, db/4, bpTop + embedDepth/2),))
			cells4 = c.findAt(((db/2 - tf - cohThk/2, -db/4, bpTop + embedDepth/2),))
			cells5 = c.findAt(((db/2 + cohThk/2, 0.0, bpTop + embedDepth/2),))
			cells6 = c.findAt(((db/2 - tf/2, bf/2 + cohThk/2, bpTop + embedDepth/2),))
			cells7 = c.findAt(((db/2 - tf/2, -bf/2 - cohThk/2, bpTop + embedDepth/2),))
			pass #corners
			cohesiveCells = cells1 + cells2 + cells3 + cells4 + cells5 + cells6 + cells7
		if baseplate:
			cells8 = c.getByBoundingBox(xMin=0.0, xMax=bpWX/2, yMin = -bpWY/2, yMax = bpWY/2, zMin=bpTop, zMax=bpTop+cohThk)#Beneath baseplate
			cells9 = c.getByBoundingBox(xMin=0.0, xMax=bpWX/2, yMin = -bpWY/2, yMax = bpWY/2, zMax=bpTop-baseDepth, zMin=bpTop-baseDepth-cohThk) #Below baseplate
			cells10 = c.getByBoundingBox(xMin=0.0, xMax=bpWX/2, yMin = bpWY/2, yMax = bpWY/2+cohThk, zMin=bpTop-baseDepth, zMax=bpTop) #Up-baseplate side
			cells11 = c.getByBoundingBox(xMin=0.0, xMax=bpWX/2, yMin = -bpWY/2-cohThk, yMax = -bpWY/2, zMin=bpTop-baseDepth, zMax=bpTop) #Down-baseplate side
			cells12 = c.getByBoundingBox(xMin=bpWX/2, xMax=bpWX/2+cohThk, yMin = -bpWY/2, yMax = bpWY/2, zMin=bpTop-baseDepth, zMax=bpTop) #Right-baseplate side
			cohesiveCells =cohesiveCells + cells8 + cells9 + cells10 + cells11 + cells12 
		region = regionToolset.Region(cells=cohesiveCells)
		p.SectionAssignment(region=region, sectionName='Cohesive', offset=0.0, 
			offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

	#Concrete cells
	p = mdb.models[modelName].parts['Foundation']
	c = p.cells
	if not(modelType == 'CohesiveZoneModel'):
		cells = c[:]
		region = regionToolset.Region(cells=cells)
		p.SectionAssignment(region=region, sectionName='Foundation', offset=0.0, 
			offsetType=MIDDLE_SURFACE, offsetField='', 
			thicknessAssignment=FROM_SECTION)
	else:
		#Get a list of all the indices of the cells
		bigList = []
		for cell in c:
			bigList += [cell.index]
		#List of indices to be filtered
		smallList = []
		for cell in cohesiveCells:
			smallList += [cell.index]
		#Filter - now we have a list of all indices we want
		cellsList = __filter(bigList, smallList)
		#Loop through each index; grab that cell, give it a section assignment.
		for index in cellsList:
			i = int(index) #Not needed?
			region = regionToolset.Region(cells=c[index:(index+1)])
			p.SectionAssignment(region=region, sectionName='Foundation', offset=0.0, 
				offsetType=MIDDLE_SURFACE, offsetField='', 
				thicknessAssignment=FROM_SECTION)	

def createLoadStep(paramsDict):
	modelName=paramsDict['modelName']
	#Create load step
	mdb.models[modelName].StaticStep(name='Load', previous='Initial', maxNumInc=500)

def instanceParts(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	#Create assembly
	a = mdb.models[modelName].rootAssembly
	a.DatumCsysByDefault(CARTESIAN)
	p = mdb.models[modelName].parts['Column']
	a.Instance(name='Column-1', part=p, dependent=ON)
	a = mdb.models[modelName].rootAssembly
	p = mdb.models[modelName].parts['Foundation']
	a.Instance(name='Foundation-1', part=p, dependent=ON)
	#Align assembly
	a = mdb.models[modelName].rootAssembly
	a.translate(instanceList=('Column-1', ), vector=(0.0, 0.0, bpTop))
	
def createContactProperties(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	#Create face group
	a = mdb.models[modelName].rootAssembly
	s1 = a.instances['Column-1'].faces
	print(strongOrient)
	if strongOrient:
		#1-Column flange, exterior faces; 2-Top column flange, top face; 3- Top column flange, bottom face; 4-Web exterior face; 5-Bottom column flange, top face
		#6- Bottom column flange, bottom face; 7-Baseplate, upper face; 8-Baseplate, lower face; 9-Baseplate, top face; 10-Baseplate, exterior face; 11-Baseplate, bottom face
		side1Faces1 = s1.getByBoundingBox(xMin = bf/2, xMax = bf/2, zMax=tFD) + \
			s1.getByBoundingBox(yMin = db/2, yMax = db/2, zMax=tFD) + \
			s1.getByBoundingBox(yMin = db/2 - tf, yMax = db/2 - tf, zMax=tFD) + \
			s1.getByBoundingBox(xMin = tw/2, xMax = tw/2, zMax=tFD) + \
			s1.getByBoundingBox(yMin = -db/2 + tf, yMax = -db/2 + tf, zMax=tFD) + \
			s1.getByBoundingBox(yMin = -db/2, yMax = -db/2, zMax=tFD) + \
			s1.getByBoundingBox(zMin = bpTop, zMax = bpTop) + \
			s1.getByBoundingBox(zMin = bpTop - baseDepth, zMax = bpTop - baseDepth) + \
			s1.getByBoundingBox(yMin = bpWY/2, yMax = bpWY/2, zMax=tFD) + \
			s1.getByBoundingBox(xMin = bpWX/2, xMax = bpWX/2, zMax=tFD) + \
			s1.getByBoundingBox(yMin = -bpWY/2, yMax = -bpWY/2, zMax=tFD)
		#N.B. if other faces are colinear with these faces, they may be selected by these methods as well!
		region1=regionToolset.Region(side1Faces=side1Faces1)
	else:
		#1-Top column faces (web top, flange top-left, flange top) 2-Side column face (flange right) 3-Bottom column faces (web bottom, flange bottom-left, flange bottom)
		#4-Baseplate, upper face; 5-Baseplate, lower face; 6-Baseplate, top face; 7-Baseplate, exterior face; 8-Baseplate, bottom face
		side1Faces1 = s1.getByBoundingBox(xMin = 0, xMax = db/2, yMin=tw/2, yMax=bf/2, zMin=bpTop, zMax=tFD) + \
			s1.getByBoundingBox(xMin = db/2, xMax = db/2, zMax=tFD) + \
			s1.getByBoundingBox(xMin = 0, xMax = db/2, yMin=-bf/2, yMax=-tw/2, zMin=bpTop, zMax=tFD) + \
			s1.getByBoundingBox(zMin = bpTop, zMax = bpTop) + \
			s1.getByBoundingBox(zMin = bpTop - baseDepth, zMax = bpTop - baseDepth) + \
			s1.getByBoundingBox(yMin = bpWY/2, yMax = bpWY/2) + \
			s1.getByBoundingBox(xMin = bpWX/2, xMax = bpWX/2) + \
			s1.getByBoundingBox(yMin = -bpWY/2, yMax = -bpWY/2)
		# N.B. if other faces are colinear with these faces, they may be selected by these methods as well!
		region1=regionToolset.Region(side1Faces=side1Faces1)

	s1 = a.instances['Foundation-1'].faces

	if strongOrient:
		#Faces touching the web, then top flange, then bottom flange
		side1Faces1 = s1.getByBoundingBox(0, -db/2, bpTop, tw/2, db/2, tFD) + \
			s1.getByBoundingBox(0,db/2-tf,bpTop,bf/2,db/2, tFD ) + \
			s1.getByBoundingBox(0,-db/2,bpTop,bf/2,-(db/2 -tf), tFD) 
	else:
		#Faces touching the web, then flange
		side1Faces1 = s1.getByBoundingBox(0, -tw/2, bpTop, db/2-tf, tw/2, tFD) + \
			s1.getByBoundingBox(db/2-tf,-bf/2,bpTop,db/2,bf/2,tFD )

	if baseplate:
		side1Faces1 += s1.getByBoundingBox(0,-bpWY/2,bpTop-baseDepth,bpWX/2,bpWY/2,bpTop) #Faces touching the baseplate

	region2=regionToolset.Region(side1Faces=side1Faces1)

	if modelType == 'Contact' or modelType == 'Friction':
		#Create interaction properties
		mdb.models[modelName].ContactProperty('IntProp-1')
		mdb.models[modelName].interactionProperties['IntProp-1'].TangentialBehavior(
			formulation=PENALTY, directionality=ISOTROPIC, slipRateDependency=OFF, 
			pressureDependency=OFF, temperatureDependency=OFF, dependencies=0, 
			table=((Friction, ), ), shearStressLimit=None, 
			maximumElasticSlip=FRACTION, fraction=0.005, elasticSlipStiffness=None)

		mdb.models[modelName].interactionProperties['IntProp-1'].NormalBehavior(
			pressureOverclosure=HARD, allowSeparation=OFF,
			constraintEnforcementMethod=DEFAULT)
		mdb.models[modelName].ContactStd(name='Int-1', createStepName='Initial')
		
		# if steelMod >= concreteMod:#stiffer column
		masterSurf = region1
		slaveSurf = region2
		# else:
		# 	masterSurf = region2
		# 	slaveSurf = region1
		mdb.models[modelName].SurfaceToSurfaceContactStd(name='Int-1', 
			createStepName='Load', master=masterSurf, slave=slaveSurf, sliding=FINITE, 
			thickness=ON, interactionProperty='IntProp-1', 
			adjustMethod=NONE,
			# initialclearance=OMIT,
			datumAxis=None,
			clearanceRegion=None)

	elif modelType == 'RigidTie' or modelType == 'Rigid' or modelType == 'CohesiveZoneModel':
		mdb.models[modelName].Tie(name='Constraint-1', master=region1, 
			slave=region2, positionToleranceMethod=COMPUTED, adjust=ON, 
			tieRotations=ON, thickness=ON)
	else:
		raise TypeError('Unknown Model Type')
		
def seedMesh(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	if modelName == 'onePartModel':
		p = mdb.models[modelName].parts['CombinedPart']
		c = p.cells
		pickedRegions = c[:]
		p.setMeshControls(regions=pickedRegions, elemShape=HEX, technique=STRUCTURED)
		p.seedPart(size=meshSize, deviationFactor=0.1, minSizeFactor=0.1)
	else:
		#Column seeding and generation
		p = mdb.models[modelName].parts['Column']
		c = p.cells
		pickedRegions = c[:]
		p.setMeshControls(regions=pickedRegions, elemShape=HEX, technique=STRUCTURED)
		p.seedPart(size=meshSize, deviationFactor=0.1, minSizeFactor=0.1)

		#Foundation seeding and generation
		p = mdb.models[modelName].parts['Foundation']
		c = p.cells
		pickedRegions = c[:]
		p.seedPart(size=meshSize, deviationFactor=0.1, minSizeFactor=0.1)
		if modelType == 'CohesiveZoneModel':
			elemType1 = mesh.ElemType(elemCode=COH3D8, elemLibrary=STANDARD)
			elemType2 = mesh.ElemType(elemCode=COH3D6, elemLibrary=STANDARD)
			elemType3 = mesh.ElemType(elemCode=UNKNOWN_TET, elemLibrary=STANDARD)
			if strongOrient:
				cells1 = c.findAt(((bf/4, db/2 + cohThk/2, bpTop + embedDepth/2),))
				cells2 = c.findAt(((bf/4, db/2 - tf - cohThk/2, bpTop + embedDepth/2),))
				cells3 = c.findAt(((bf/4, -db/2 + tf + cohThk/2, bpTop + embedDepth/2),))
				cells4 = c.findAt(((bf/4, -db/2 - cohThk/2, bpTop + embedDepth/2),))
				cells5 = c.findAt(((tw/2 + cohThk/2,0.0, bpTop + embedDepth/2),))
				cells6 = c.findAt(((bf/2 + cohThk/2, db/2 - tf/2, bpTop + embedDepth/2),))
				cells7 = c.findAt(((bf/2 + cohThk/2, -db/2 + tf/2, bpTop + embedDepth/2),))
				cells = cells1 + cells2 + cells3 + cells4 + cells5 + cells6 + cells7
				pass #Corners
			elif not strongOrient:
				cells1 = c.findAt(((db/4, tw/2 + cohThk/2, bpTop + embedDepth/2),))
				cells2 = c.findAt(((db/4, -tw/2 - cohThk/2, bpTop + embedDepth/2),))
				cells3 = c.findAt(((db/2 - tf - cohThk/2, db/4, bpTop + embedDepth/2),))
				cells4 = c.findAt(((db/2 - tf - cohThk/2, -db/4, bpTop + embedDepth/2),))
				cells5 = c.findAt(((db/2 + cohThk/2, 0.0, bpTop + embedDepth/2),))
				cells6 = c.findAt(((db/2 - tf/2, bf/2 + cohThk/2, bpTop + embedDepth/2),))
				cells7 = c.findAt(((db/2 - tf/2, -bf/2 - cohThk/2, bpTop + embedDepth/2),))
				pass #corners
				cells = cells1 + cells2 + cells3 + cells4 + cells5 + cells6 + cells7
			if baseplate:
				cells8 = c.getByBoundingBox(xMin=0.0, xMax=bpWX/2, yMin = -bpWY/2, yMax = bpWY/2, zMin=bpTop, zMax=bpTop+cohThk)#Above baseplate
				cells9 = c.getByBoundingBox(xMin=0.0, xMax=bpWX/2, yMin = -bpWY/2, yMax = bpWY/2, zMax=bpTop-baseDepth, zMin=bpTop-baseDepth-cohThk) #Below baseplate
				cells10 = c.getByBoundingBox(xMin=0.0, xMax=bpWX/2, yMin = bpWY/2, yMax = bpWY/2+cohThk, zMin=bpTop-baseDepth, zMax=bpTop) #Up-baseplate side
				cells11 = c.getByBoundingBox(xMin=0.0, xMax=bpWX/2, yMin = -bpWY/2-cohThk, yMax = -bpWY/2, zMin=bpTop-baseDepth, zMax=bpTop) #Down-baseplate side
				cells12 = c.getByBoundingBox(xMin=bpWX/2, xMax=bpWX/2+cohThk, yMin = -bpWY/2, yMax = bpWY/2, zMin=bpTop-baseDepth, zMax=bpTop) #Right-baseplate side
				cells = cells + cells8 + cells9 + cells10 + cells11 + cells12 
			pickedRegions =(cells, )
			p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, 
				elemType3))
		
def generateMesh(paramsDict):
	modelName = paramsDict['modelName']

	p = mdb.models[modelName].parts['Column']
	p.generateMesh()
	p = mdb.models[modelName].parts['Foundation']
	p.generateMesh()
		
def createBoundaryConditions(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	#Fixed BC
	a = mdb.models[modelName].rootAssembly
	if modelName == 'onePartModel':
		f = a.instances[ColumnPart + '-1'].faces
	else:
		f = a.instances['Foundation-1'].faces
	
	facesBottom = f.getByBoundingBox(zMax=0.0)
	facesSides = f.getByBoundingBox(xMin=fWX/2)

	if boundaryConditions == 'Default': #Bottom
		faces1 = facesBottom
	elif boundaryConditions == 'Sides':
		faces1 = facesSides

	region = regionToolset.Region(faces=faces1)
	mdb.models[modelName].EncastreBC(name='FixedBC', 
		createStepName='Initial', region=region, localCsys=None)
			
	#Symmetry BC
	if modelName <> 'onePartModel':
		#Column symmetry
		a = mdb.models[modelName].rootAssembly
		f = a.instances['Column-1'].faces
		faces1 = f.getByBoundingBox(xMax = 0.0) #Get all faces that lie on the x=0.0 plane.
		region = regionToolset.Region(faces=faces1)
		mdb.models[modelName].XsymmBC(name='ColumnSymmetry', createStepName='Initial', 
			region=region)
		#Foundation symmetry
		f = a.instances['Foundation-1'].faces
		faces1 = f.getByBoundingBox(xMax = 0.0) #Get all faces that lie on the x=0.0 plane.
		region = regionToolset.Region(faces=faces1)
		mdb.models[modelName].XsymmBC(name='ContinuumSymmetry', createStepName='Initial', 
			region=region)
	else:
		a = mdb.models[modelName].rootAssembly
		f = a.instances['CombinedPart-1'].faces
		faces1 = f.getByBoundingBox(xMax = 0.0) #Get all faces that lie on the x=0.0 plane.
		region = regionToolset.Region(faces=faces1)
		mdb.models[modelName].XsymmBC(name='Symmetry', createStepName='Initial', 
			region=region)
		if modelType == 'CohesiveZoneModel':
			pass #Will not be affected by presence of cohesive zone when the getByBoundingBox method is used.
		
def createRigidTopConstraint(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	a = mdb.models[modelName].rootAssembly
	e1 = a.instances[columnPartName + '-1'].edges
	v1 = a.instances[columnPartName + '-1'].vertices
	refID = a.ReferencePoint(point=v1.findAt(coordinates=(0.0, 0.0, Z+tFD))).id

	f1 = a.instances[columnPartName  + '-1'].faces
	faces1 = f1.getByBoundingBox(zMin = Z+tFD)
	region4=regionToolset.Region(faces=faces1)
	r1 = a.referencePoints
	refPoints1=(r1[refID], )
	region1=regionToolset.Region(referencePoints=refPoints1)
	mdb.models[modelName].RigidBody(name='FlangeRigidBody', 
		refPointRegion=region1, tieRegion=region4)

def createAppliedLoad(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	a = mdb.models[modelName].rootAssembly
	if strongOrient: #Much better results when weak axis bending is distributed. Strong axis doesn't care so much.
		region = a.instances[columnPartName + '-1'].sets['Set-1']
		mdb.models[modelName].ConcentratedForce(name='Load-1', 
			createStepName='Load', region=region, cf1=0, cf2=appliedLoad/2, cf3=-axialLoad/2, 
			distributionType=UNIFORM, field='', localCsys=None)
	else: #Distributed AKA traction load
		#Lateral Load
		s1 = a.instances['Column-1'].faces
		side1Faces1 = s1.getByBoundingBox(zMin = Z+tFD)
		region = regionToolset.Region(side1Faces=side1Faces1)
		mdb.models[modelName].SurfaceTraction(
			name='TractionLoad', createStepName='Load', region=region, magnitude=appliedLoad / bA, 
			directionVector=((0,0,0),(0,1,0)), distributionType=UNIFORM, 
			field='', localCsys=None, resultant=OFF)
		#Axial Load
		if axialLoad != 0.0:
			s1 = a.instances['Column-1'].faces
			side1Faces1 = s1.getByBoundingBox(zMin = Z+tFD)
			region = regionToolset.Region(side1Faces=side1Faces1)
			mdb.models[modelName].SurfaceTraction(
				name='TractionLoad', createStepName='Load', region=region, magnitude=axialLoad / bA, 
				directionVector=((0,0,0),(0,0,-1)), distributionType=UNIFORM, 
				field='', localCsys=None, resultant=OFF)
		
def createJob(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	mdb.Job(name=modelName, model=modelName, description='', 
		type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue='', 
		memory=90, memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
		explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF, 
		modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
		scratch='', multiprocessingMode=DEFAULT, numCpus=4, numDomains=4)
		
def createHistoryOutputRequest(paramsDict):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	regionDef=mdb.models[modelName].rootAssembly.instances[columnPartName + '-1'].sets['Set-1']
	mdb.models[modelName].HistoryOutputRequest(name='H-Output-2', 
		createStepName='Load', variables=('U1', 'U2'), region=regionDef, 
		sectionPoints=DEFAULT, rebar=EXCLUDE)

def writeInputFile(paramsDict):
	modelName = paramsDict['modelName']
	mdb.jobs[modelName].writeInput(consistencyChecking=OFF)
	
def saveModelFile(paramsDict):
	mdb.saveAs(pathName=paramsDict['mdbFileName'])
				
		
#Postprocessing methods
		
def checkOutputFile(paramsDict): #check that output file exists and is closed
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass
	#does the output file exist?
	if not(path.exists(outputFileName)):
		__openwrite(outputFileName)
		
	#if it exists, is it open?
	else:
		try:
			with open(outputFileName, 'a') as f:
				f.write('')
		except IOError:
			pass#Error message: close the output file!
			outputFileName = outputFileName[0:-4] + '(2).csv'#Give a second chance.
			if not(path.exists(outputFileName)):
				__openwrite(outputFileName)
			else: 
				try:
					with open(outputFileName, 'a') as f:
						f.write('')
				except IOError:
					raise IOError#No third chances.
	
		
def findDisplacementAndOutput(paramsDict, firstParam, firstParamEntry, secondParam, secondParamEntry, blockoutEntry, modelTypeEntry):
	for key in list(paramsDict):
		exec('%s="%s"' %(key, paramsDict[key]))
		try:#only expecting strings or numbers.
			exec('%s=float(%s)' %(key, key))
		except ValueError:
			pass

	assert modelType == modelTypeEntry
	#Output algorithm: get node name.
	p = mdb.models[modelName].parts[columnPartName]
	n = p.nodes
	if strongOrient: radius = meshSize/2 - 0.001
	elif not strongOrient: radius = tw/2 - 0.001
	if modelName <> 'onePartModel':
		nodes = n.getByBoundingSphere((0.0,0.0,columnLength),  radius) 
	else:
		nodes = n.getByBoundingSphere((0.0,0.0,tFD + Z), radius) 
	loadnode = nodes[0].label
	#Create XY data from the output history request.
	
	try:
		odb = session.odbs[odbFileName]
		session.XYDataFromHistory(name='Displacement at load', odb=odb, 
			outputVariableName='Spatial displacement: U2 PI: ' + upper(columnPartName) + '-1 Node ' + str(loadnode) + ' in NSET SET-1', 
			steps=('Load', ), )
		#Report the XY data to the .output file
		x0 = session.xyDataObjects['Displacement at load']
		session.writeXYReport(fileName=modelName+'.output', xyData=(x0, ))
		
		#Enter the .output file and scrape the needed information.	
		#The number we want will be on the 6th line from the end.
		f = open(modelName+'.output')
		lines = f.readlines()
		myString = lines[-5]
		totalDisp = float(myString[26:-1])
		f.close()

		
		kipLoad = float(appliedLoad) / 1000.0
		if strongOrient: columnStiff = float(3.0 * steelMod/1000.0 * Ix / Z**3) #in kips
		elif not strongOrient: columnStiff = float(3.0 * steelMod/1000.0 * Iy / Z**3) #in kips
		columnDisp = kipLoad/columnStiff
		connDisp = totalDisp - columnDisp
		connStiff = kipLoad / connDisp
		connRotStiff = connStiff * Z**2
	except: #What happens if the XYData is not available? (Patch)
		totalDisp = "ERROR"
		connStiff = "ERROR"
		connRotStiff = "ERROR"		
	
	with open(outputFileName, 'a') as f:
		f.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\n' %(modelName, modelTypeEntry, firstParam, firstParamEntry, secondParam,\
			secondParamEntry, blockoutEntry, columnName, Z, totalDisp, connStiff, connRotStiff, __timeStamp()))
		