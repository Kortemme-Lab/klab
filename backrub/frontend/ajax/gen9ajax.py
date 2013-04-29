#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

#import cgi


#import json

#import serial
#ser = serial.Serial('/dev/ttyUSB0', 57600)
#ser.write("Hello, this is a command for value %s from slider id!\n" % (form["rating"]))      # write a string
#ser.close()

#F = open("/tmp/testfile.txt", "w")
#F.write(estr)
#F.close()

import cgi
import cgitb
import traceback
import simplejson as json
import sys
import os
import base64
from pseToJSmol import JSmolScriptGenerator
#from pseToJSmol import getPDBGZContents


F = open("/tmp/testfile.txt", "w")

from subprocess import Popen, PIPE
def getPDBGZContents(fname):
	f = Popen(['gunzip', '-c', fname], stdout=PIPE)
	return "".join([line for line in f.stdout])

def getUserDesignRatings(gen9db, DesignID):
	UserDesignRatings = []
	results = gen9db.execute_select("""
SELECT FirstName, UserDesignRating.*
FROM UserDesignRating 
INNER JOIN (
SELECT UserID,DesignID,MAX(Date) AS MaxDate
FROM UserDesignRating GROUP BY UserID, DesignID) udr
ON udr.UserID=UserDesignRating.UserID AND udr.DesignID=UserDesignRating.DesignID AND udr.MaxDate=UserDesignRating.Date
INNER JOIN User ON UserDesignRating.UserID=User.ID WHERE UserDesignRating.DesignID=%s
ORDER BY DesignID, FirstName""", parameters=(DesignID,))
	for r in results:
		UserDesignRatings.append(r)
	return UserDesignRatings

def getMeetingDesignRatings(gen9db, DesignID):
	MeetingDesignRatings = {}
	results = gen9db.execute_select("""
SELECT MeetingDesignRating.*
FROM MeetingDesignRating 
INNER JOIN (
SELECT MeetingDate, DesignID, MAX(CommentDate) AS MaxDate
FROM MeetingDesignRating GROUP BY MeetingDate, DesignID) mdr
ON mdr.MeetingDate=MeetingDesignRating.MeetingDate AND mdr.DesignID=MeetingDesignRating.DesignID AND mdr.MaxDate=MeetingDesignRating.CommentDate WHERE MeetingDesignRating.DesignID=%s
""", parameters=(DesignID,))
	for r in results:
		key = r['DesignID']
		MeetingDesignRatings[key] = MeetingDesignRatings.get(key, {})
		MeetingDesignRatings[key][r['MeetingDate']] = r
	return MeetingDesignRatings

def getUserScaffoldRatings(gen9db, ComplexID):
	UserScaffoldRatings = {}
	UserScaffoldTerminiOkay = {}
	#results = gen9db.execute_select("SELECT UserScaffoldRating.*, User.FirstName FROM UserScaffoldRating INNER JOIN User ON UserID=User.ID")
	results = gen9db.execute_select("""
SELECT FirstName, UserScaffoldRating.*
FROM UserScaffoldRating 
INNER JOIN (
SELECT UserID, ComplexID, MAX(Date) AS MaxDate
FROM UserScaffoldRating GROUP BY UserID, ComplexID) udr
ON udr.UserID=UserScaffoldRating.UserID AND udr.ComplexID=UserScaffoldRating.ComplexID AND udr.MaxDate=UserScaffoldRating.Date
INNER JOIN User ON UserScaffoldRating.UserID=User.ID WHERE UserScaffoldRating.ComplexID=%s""", parameters=(ComplexID,))
	for r in results:
		key = r['ComplexID']
		UserScaffoldRatings[key] = UserScaffoldRatings.get(key, {})
		UserScaffoldRatings[key][r['UserID']] = r
		if r['TerminiAreOkay']:
			UserScaffoldTerminiOkay[key] = r['TerminiAreOkay']
	return UserScaffoldRatings, UserScaffoldTerminiOkay

def getMeetingScaffoldRatings(gen9db, ComplexID):
	MeetingScaffoldRatings = {}
	results = gen9db.execute_select("""
SELECT MeetingScaffoldRating.*
FROM MeetingScaffoldRating 
INNER JOIN (
SELECT MeetingDate, ComplexID, MAX(CommentDate) AS MaxDate
FROM MeetingScaffoldRating GROUP BY MeetingDate, ComplexID) mdr
ON mdr.MeetingDate=MeetingScaffoldRating.MeetingDate AND mdr.ComplexID=MeetingScaffoldRating.ComplexID AND mdr.MaxDate=MeetingScaffoldRating.CommentDate
WHERE MeetingScaffoldRating.ComplexID=%s""", parameters=(ComplexID,))
	for r in results:
		key = r['ComplexID']
		MeetingScaffoldRatings[key] = MeetingScaffoldRatings.get(key, {})
		MeetingScaffoldRatings[key][r['MeetingDate']] = r
	return MeetingScaffoldRatings

def getHeaderCSSClasses(gen9db, DesignID):
	DesignID = long(DesignID)
	design_data = gen9db.execute_select("SELECT Design.ID AS DesignID, PDBBiologicalUnit.ComplexID, Design.*, SmallMolecule.Name AS SmallMoleculeName, SmallMolecule.ID AS SmallMoleculeID, SmallMoleculeMotif.Name AS TargetMotifName FROM Design INNER JOIN SmallMoleculeMotif ON TargetSmallMoleculeMotifID=SmallMoleculeMotif.ID INNER JOIN SmallMolecule ON SmallMoleculeID=SmallMolecule.ID INNER JOIN PDBBiologicalUnit ON PDBBiologicalUnit.PDBFileID=WildtypeScaffoldPDBFileID AND PDBBiologicalUnit.BiologicalUnit=WildtypeScaffoldBiologicalUnit WHERE Design.ID=%s", parameters=(DesignID,))
	assert(len(design_data) == 1)
	design_data = design_data[0]
	ComplexID = design_data['ComplexID']
	
	UserDesignRatings = getUserDesignRatings(gen9db, DesignID)
	MeetingDesignRatings = getMeetingDesignRatings(gen9db, DesignID)
	UserScaffoldRatings, UserScaffoldTerminiOkay = getUserScaffoldRatings(gen9db, ComplexID)
	MeetingScaffoldRatings = getMeetingScaffoldRatings(gen9db, ComplexID)
	
	F.write("\n***MeetingDesignRatings\n")
	F.write(str(MeetingDesignRatings))
	F.write("\n")
	
	design_tr_class = DesignIterator.getDesignsCSSClass(DesignID, UserDesignRatings, MeetingDesignRatings)
	scaffold_tr_class = DesignIterator.getScaffoldsCSSClass(ComplexID, UserScaffoldRatings, MeetingScaffoldRatings)
	return design_tr_class, scaffold_tr_class
 
def addComment(gen9db, data):
	from datetime import datetime, date
	
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	CommentType = form['CommentType'].value
	CommentMaker = form['CommentMaker'].value
	DesignID = long(form['DesignID'].value)
	Gen9Username = form['Username'].value
	Rating = form['Rating'].value
	Comments = form['Comments'].value
	if Rating == 'null':
		Rating = None
	if Comments == 'null':
		Comments = None
	
	html = []
	F.write('here')
	F.write(str(data))
	Gen9Error = None
	success = True
	
	design_data = gen9db.execute_select("SELECT Design.ID AS DesignID, PDBBiologicalUnit.ComplexID, Design.*, SmallMolecule.Name AS SmallMoleculeName, SmallMolecule.ID AS SmallMoleculeID, SmallMoleculeMotif.Name AS TargetMotifName FROM Design INNER JOIN SmallMoleculeMotif ON TargetSmallMoleculeMotifID=SmallMoleculeMotif.ID INNER JOIN SmallMolecule ON SmallMoleculeID=SmallMolecule.ID INNER JOIN PDBBiologicalUnit ON PDBBiologicalUnit.PDBFileID=WildtypeScaffoldPDBFileID AND PDBBiologicalUnit.BiologicalUnit=WildtypeScaffoldBiologicalUnit WHERE Design.ID=%s", parameters=(DesignID,))
	assert(len(design_data) == 1)
	design_data = design_data[0]
	ComplexID = design_data['ComplexID']
	
	if CommentMaker == "User":
		if CommentType == "Design": 
			gres = gen9db.execute("SELECT * FROM UserDesignRating WHERE UserID=%s AND DesignID=%s", parameters=(Gen9Username, DesignID))
			if gres and False:
				assert(len(gres) == 1)
				gen9db.execute("UPDATE UserDesignRating SET Rating=%s WHERE UserID=%s AND DesignID=%s", parameters=(Rating, Gen9Username, DesignID))
				gen9db.execute("UPDATE UserDesignRating SET RatingNotes=%s WHERE UserID=%s AND DesignID=%s", parameters=(Comments, Gen9Username, DesignID))
			elif Rating and not(Comments):
				Gen9Error = "You need to specify a design rating AND add notes."
			elif Comments and (not(Rating) or Rating == 'None'):
				Gen9Error = "You need to specify a design rating AND add notes."
			else: 
				details = {
					'UserID'			: Gen9Username,
					'DesignID'			: DesignID,
					'Date'				: current_time,
					'Rating'			: Rating,
					'RatingNotes'		: Comments,
				}
				gen9db.insertDict('UserDesignRating', details,)
		elif CommentType == "Scaffold":
			gres = gen9db.execute("SELECT * FROM UserScaffoldRating WHERE UserID=%s AND ComplexID=%s", parameters=(Gen9Username, ComplexID))
			if gres and False:
				assert(len(gres) == 1)
				gen9db.execute("UPDATE UserScaffoldRating SET Rating=%s WHERE UserID=%s AND ComplexID=%s", parameters=(Rating, Gen9Username, ComplexID))
				gen9db.execute("UPDATE UserScaffoldRating SET RatingNotes=%s WHERE UserID=%s AND ComplexID=%s", parameters=(Comments, Gen9Username, ComplexID))
			elif Rating and not(Comments):
				Gen9Error = "You need to specify a scaffold rating AND add notes."
			elif Comments and (not(Rating) or Rating == 'None'):
				Gen9Error = "You need to specify a scaffold rating AND add notes."
			else: 
				details = {
					'UserID'			: Gen9Username,
					'ComplexID'			: ComplexID,
					'Date'				: current_time,
					'Rating'			: Rating,
					'RatingNotes'		: Comments,
					'TerminiAreOkay'	: None,
				}
				gen9db.insertDict('UserScaffoldRating', details,)
	elif CommentMaker == "Meeting":
		Gen9MeetingDate = date.today()
		if CommentType == "Design": 
			if Rating and not(Comments):
				Gen9Error = "You need to specify a design rating AND add notes."
			elif Comments and (not(Rating) or Rating == 'None'):
				Gen9Error = "You need to specify a design rating AND add notes."
			else: 
				details = {
					'DesignID'			: DesignID,
					'MeetingDate'		: Gen9MeetingDate,
					'CommentDate'		: current_time,
					'Approved'			: Rating,
					'ApprovalNotes'		: Comments,
					'UserID'			: Gen9Username,
				}
				gen9db.insertDict('MeetingDesignRating', details,)
		elif CommentType == "Scaffold": 
			if Rating and not(Comments):
				Gen9Error = "You need to specify a design rating AND add notes."
			elif Comments and (not(Rating) or Rating == 'None'):
				Gen9Error = "You need to specify a design rating AND add notes."
			else:
				details = {
					'ComplexID'			: ComplexID,
					'MeetingDate'		: Gen9MeetingDate,
					'CommentDate'		: current_time,
					'Approved'			: Rating,
					'ApprovalNotes'		: Comments,
					'UserID'			: Gen9Username,
					
				}
				gen9db.insertDict('MeetingScaffoldRating', details,)
	
	# Regenerate HTML
	MeetingDesignRatings = getMeetingDesignRatings(gen9db, DesignID)
	UserDesignRatings = getUserDesignRatings(gen9db, DesignID)
	MeetingScaffoldRatings = getMeetingScaffoldRatings(gen9db, ComplexID)
	UserScaffoldRatings, UserScaffoldTerminiOkay = getUserScaffoldRatings(gen9db, ComplexID)
	
	html = DesignIterator.getCommentsForDesign(DesignID, ComplexID, MeetingDesignRatings, UserDesignRatings, MeetingScaffoldRatings, UserScaffoldRatings, UserScaffoldTerminiOkay, group_colors = DesignIterator.getGroupColors()) 

	F.write("\n".join(html))
	return html	
try:
	sys.path.insert(0, '../..')
	sys.path.insert(0, '..')
	
	import common.rosettadb as rosettadb
	from gen9 import DesignIterator
	form = cgi.FieldStorage()
	
	from common.rosettahelper import WebsiteSettings
	settings = WebsiteSettings(sys.argv, os.environ['SCRIPT_NAME'])

	gen9db = rosettadb.ReusableDatabaseInterface(settings, host = "kortemmelab.ucsf.edu", db = "Gen9Design")
	
	if form.has_key('request'):
		if form['request'].value == 'DesignDetails':
			if form.has_key('DesignID'):
				DesignID = form['DesignID'].value
				results = gen9db.execute("SELECT * FROM Design WHERE ID=%s", parameters=(DesignID,))
				gen9db.close()
				assert(len(results) == 1)
				print 'Content-Type: application/json\n\n'
				print(json.dumps(results[0]))
				F.write(json.dumps(results[0]))
				
		elif form['request'].value == 'AddComment':
			F.write('\nHERE1\n')
			
			html = "\n".join(addComment(gen9db, form))
			print 'Content-Type: text/html\n\n'
			print(html)
			F.write('\nHERE2\n')
		
		elif form['request'].value == 'GetHeaderCSSClasses':
			if form.has_key('DesignID'):
				F.write('\nHERE1\n')
				design_tr_class, scaffold_tr_class = getHeaderCSSClasses(gen9db, form['DesignID'].value)
				print 'Content-Type: application/json\n\n'
				print(json.dumps({'design_tr_class' : design_tr_class, 'scaffold_tr_class' : scaffold_tr_class}))
				F.write('\nHERE2\n')
		
		elif form['request'].value == 'DesignResidueDetails':
			design_residue_data = {}
			if form.has_key('DesignID'):
				DesignID = form['DesignID'].value
				
				design_type = gen9db.execute_select("SELECT Type FROM Design WHERE ID=%s", parameters=(DesignID,))[0]['Type']
				
				results = gen9db.execute_select('''
					SELECT DesignID, Chain, OriginalAA, ResidueID, VariantAA, IsMotifResidue, IsMutation, PositionWithinChain,
					  fa_dun, fa_atr,	fa_rep,	fa_sol,	p_aa_pp, hbond_sr_bb, hbond_lr_bb, hbond_bb_sc, hbond_sc, hack_elec, rama, total,
					  RANL_SignificantChiChange, RANL_Chi1Delta, RANL_Chi2Delta, RANL_AllSideChainHeavyAtomsRMSD,
					  RSNL_SignificantChiChange, RSNL_Chi1Delta, RSNL_Chi2Delta, RSNL_AllSideChainHeavyAtomsRMSD,
					  RSWL_SignificantChiChange, RSWL_Chi1Delta, RSWL_Chi2Delta, RSWL_AllSideChainHeavyAtomsRMSD
					FROM DesignResidue WHERE DesignID=%s ORDER BY Chain, ResidueID''', parameters=(DesignID,))
			
			for r in results:
				design_residue_data[r['Chain']] = design_residue_data.get(r['Chain'], {})
				design_residue_data[r['Chain']][r['ResidueID']] = r
			
			html = 'test'
			if design_type != 'Manual':
				html = "\n".join(DesignIterator.get_Design_residue_table_HTML(design_residue_data))
			else:
				OriginalDesignID = gen9db.execute_select("SELECT OriginalDesignID FROM ManualDesign WHERE DesignID=%s", parameters=(DesignID,))[0]['OriginalDesignID']
				set_of_motif_residues = set([r['ResidueID'] for r in gen9db.execute_select("SELECT ResidueID FROM DesignResidue WHERE DesignID=%s AND IsMotifResidue=1", parameters=(OriginalDesignID,))])
				html = "\n".join(DesignIterator.get_ManualDesign_residue_table_HTML(design_residue_data, set_of_motif_residues))
		
			print 'Content-Type: text/html\n\n'
			print(html)
			F.write(json.dumps(design_residue_data))
				
		elif form['request'].value == 'DesignPDBContents':
			if form.has_key('DesignID'):
				DesignID = form['DesignID'].value
				results = gen9db.execute("SELECT FilePath FROM Design WHERE ID=%s", parameters=(DesignID,))
				gen9db.close()
				assert(len(results) == 1)
				#readlines
				print 'Content-Type: text/html\n\n'
				print(getPDBGZContents(results[0]['FilePath']))
				#print(json.dumps(results[0]))
				#F.write(json.dumps(results[0]))
		elif form['request'].value == 'newDesignPDBContents':
			#model1 = getPDBGZContents('/kortemmelab/shared/projects/Gen9/biosensor_design/data/FPP/templates/1FPP.pdb.gz')
			#model2 = getPDBGZContents('/kortemmelab/shared/projects/Gen9/biosensor_design/data/CFF/templates/1C8L.pdb.gz')
			
			
			design_record = gen9db.execute("SELECT * FROM Design WHERE ID=%s", parameters=(form['DesignID'].value,))[0]
			small_molecule = gen9db.execute("SELECT SmallMoleculeID, PDBFileID FROM SmallMoleculeMotif WHERE ID=%s", parameters=(design_record['TargetSmallMoleculeMotifID'],))[0]
			small_molecule_motif_residues = gen9db.execute("SELECT * FROM SmallMoleculeMotifResidue WHERE SmallMoleculeMotifID = %s", parameters=(design_record['TargetSmallMoleculeMotifID'],))
			motif_residues = gen9db.execute("SELECT Chain, OriginalAA, ResidueID, VariantAA, IsMutation FROM DesignResidue WHERE DesignID=%s AND IsMotifResidue=1", parameters=(design_record['ID'],))
			jmol = JSmolScriptGenerator(design_record, small_molecule, small_molecule_motif_residues, motif_residues).script
			
			
			F.write('HERE5\n')
			#model1 = getPDBGZContents('/kortemmelab/shared/dropbox/1UBQ.pdb.gz')
			#model2 = getPDBGZContents('/kortemmelab/shared/dropbox/1DTX.pdb.gz')
			#F.write(model1)
			#d = {"model1" : model1, "model2" : model2}
			d = {"script" : jmol}#, "model1" : model1, "model2" : model2}
			F.write(json.dumps(d))
			#print
			print 'Content-Type: application/json\n\n'
			print(json.dumps(d))
			F.write('HERE6')
				
	F.write('\nHERE4\n')
	F.close()
except Exception, e:
	if gen9db:
		gen9db.close()
	#F = open("/tmp/testfile.txt", "w")
	F.write("%s\n%s" % (str(e), traceback.format_exc()))
	if form:
		F.write("Form:")
		F.write(str(form))
	F.close()
