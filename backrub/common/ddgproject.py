#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

import sys, os
import MySQLdb
import MySQLdb.cursors
import traceback
import pickle
import time
from datetime import datetime, date
from string import join, letters
import math
from httplib import HTTPConnection
import getpass
import itertools
sys.path.insert(0, "common")
import colortext
from pdb import PDB

sqrt = math.sqrt
DictCursor = MySQLdb.cursors.DictCursor
StdCursor = MySQLdb.cursors.Cursor

PDBToUniProt = {}
UniProtKBACToPDB = {}
uniprotmapping = os.path.join("rawdata", "uniprotmapping.csv")
UniqueIDs = {}

PDBChains = {}

aas = [
	["A", "ALA", "Alanine",			"non-polar",	"small"], 
	["C", "CYS", "Cysteine",		"non-polar",	"small"],
	["D", "ASP", "Aspartic acid",	"polar",		"small"],
	["E", "GLU", "Glutamic acid",	"polar",		"large"],
	["F", "PHE", "Phenylalanine",	"non-polar",	"large"],
	["G", "GLY", "Glycine",			"non-polar",	"small"],
	["H", "HIS", "Histidine",		"polar",		"large"],
	["I", "ILE", "Isoleucine",		"non-polar",	"large"],
	["K", "LYS", "Lysine",			"polar",		"large"],
	["L", "LEU", "Leucine",			"non-polar",	"large"],
	["M", "MET", "Methionine",		"non-polar",	"large"],
	["N", "ASN", "Asparagine",		"polar",		"small"],
	["P", "PRO", "Proline",			"non-polar",	"small"],
	["Q", "GLN", "Glutamine",		"polar",		"large"],
	["R", "ARG", "Arginine",		"polar",		"large"],
	["S", "SER", "Serine",			"polar",		"small"],
	["T", "THR", "Threonine",		"polar",		"small"],
	["V", "VAL", "Valine",			"non-polar",	"small"],
	["W", "TRP", "Tryptophan",		"non-polar",	"large"],
	["Y", "TYR", "Tyrosine",		"polar",		"large"]
]
# These lists are used to verify record imports from the different databases
# We scan these lists in order to find matches so reorder the chain letters and insertion codes according to what (I'm guessing here) is typical usage in PDB files.
AllowedAminoAcids = [aa[0] for aa in aas]
CommonChainLetters = ['_', '-'] + list(itertools.chain(*[[letters[i+26], letters[i]] for i in range(26)])) + ['4', '1']
AllowedChainLetters = [chr(i) for i in range(32, 127)]
AllowedChainLetters = [c for c in AllowedChainLetters if c not in CommonChainLetters]
AllowedChainLetters = CommonChainLetters + AllowedChainLetters
AllowedInsertionCodes = list(itertools.chain(*[[letters[i+26], letters[i]] for i in range(26)]))

def computeStandardDeviation(values):
	sum = 0
	n = len(values)
	
	for v in values:
		sum += v
	
	mean = sum / n
	sumsqdiff = 0
	
	for v in values:
		t = (v - mean)
		sumsqdiff += t * t
	
	variance = sumsqdiff / n
	stddev = math.sqrt(variance)
	
	return stddev, variance

def readUniProtMap():
	if os.path.exists(uniprotmapping):
		F = open(uniprotmapping)
		contents = F.read().split("\n")
		F.close()
		for line in contents[1:]:
			if line:
				line = line.split("\t")
				pdbID = line[0]
				UPAC = line[1]
				UPID = line[2]
				if PDBToUniProt.get(pdbID):
					PDBToUniProt[pdbID].append((UPAC, UPID))
				else:
					PDBToUniProt[pdbID] = [(UPAC, UPID)]
				if UniProtKBACToPDB.get(UPAC):
					UniProtKBACToPDB[UPAC].append(pdbID)
				else:
					UniProtKBACToPDB[UPAC] = [pdbID]
					

class FieldNames(dict):
	'''Define database fieldnames here so we can change them in one place if need be.'''
		
	def __init__(self):
		self.queued = "queued"
		self.active = "active"
		self.done = "done"
		self.failed = "failed"
		
		self.Structure = "Structure"
		self.PDB_ID = "PDB_ID"	
		self.Content = "Content"
		self.Resolution = "Resolution"
		self.Source = "Source"
		self.Protein = "Protein"
		self.Techniques = "Techniques"
		self.BFactors = "BFactors"
		
		self.Experiment = "Experiment"
		self.ID = "ID"
		self.Mutant = "Mutant"
		self.ScoreVariance = "ScoreVariance"
				
		self.ExperimentID = "ExperimentID"
		self.Chain = "Chain"
		self.ResidueID = "ResidueID"
		self.WildTypeAA = "WildTypeAA"
		self.MutantAA = "MutantAA"
		
		self.SourceID = "SourceID"
		self.ddG = "ddG"
		self.NumberOfMeasurements = "NumberOfMeasurements"
		
		self.Name = "Name"
		self.Version = "Version"
		self.SVNRevision = "SVNRevision"
		
		self.Type = "Type"
		self.Command = "Command"
		
		self.Prediction = "Prediction"
		self.PredictionSet = "PredictionSet"
		self.ToolID = "ToolID"
		self.CommandID = "CommandID"
		self.KeptHETATMLines = "KeptHETATMLines"
		self.StrippedPDB = "StrippedPDB"
		self.InputFiles = "InputFiles"
		self.Description = "Description"
		self.EntryDate = "EntryDate"
		self.StartDate = "StartDate"
		self.EndDate = "EndDate"
		self.CryptID = "cryptID"
		self.Status = "Status"
		self.Errors = "Errors"
		self.AdminCommand = "AdminCommand" 

	def __getitem__(self, key):
		return self.__dict__[key]
	
FieldNames_ = FieldNames()

class DBObject(object):
	dict = {}
	databaseID = None
	
	def __init__(self, Description):
		pass
					
	def __getitem__(self, key):
		return self.dict[key]

	def getDatabaseID(self):
		if not self.databaseID:
			raise Exception("Cannot get the database ID of an uncommitted record.")
		else:
			return self.databaseID
		
	def commit(self, db):
		raise Exception("Concrete function commit needs to be defined.")
	
	def __repr__(self):
		raise Exception("Concrete function  __repr__  needs to be defined.")
	
class PDBStructure(DBObject):
	
	def __init__(self, pdbID, content = None, protein = None, source = None):
		self.dict = {
			FieldNames_.PDB_ID : pdbID,
			FieldNames_.Content : content,
			FieldNames_.Protein : protein,
			FieldNames_.Source : source,
			FieldNames_.Resolution : None,
			FieldNames_.Techniques : None,
		}
	
	def getPDBContents(self):
		d = self.dict
		id = d[FieldNames_.PDB_ID]
		if len(id) != 4:
			print(id)
		assert(len(id) == 4)
		filename = os.path.join("pdbs", id + ".pdb")
		contents = None
		chains = {}
		
		if not os.path.exists(filename):
			print("Missing file for %s %s" % (id, filename))
			c = HTTPConnection("www.rcsb.org")
			c.request("GET", "/pdb/files/%s.pdb" % id)
			response = c.getresponse()
			contents = response.read()
			c.close()
			if contents[0:6] == "<html>":
				print(contents)
				raise Exception("Error retrieving %s." % filename)				
			F = open(filename, "w")
			F.write(contents)
			F.close()		
			if not os.path.exists(filename):
				raise Exception("Error retrieving %s." % filename)
		else:
			F = open(filename, "r")
			contents = F.read()
			F.close()		
		
		resolution = None
		lines = contents.split("\n")
		for line in lines:
			if line.startswith("ATOM") or line.startswith("HETATM"):
				chains[line[21]] = True
			elif line.startswith("EXPDTA"):
				techniques = line[10:71].split(";")
				for k in range(len(techniques)):
					techniques[k] = techniques[k].strip() 
				techniques = join(techniques, ";")
			elif line.startswith("REMARK   2 RESOLUTION."):
				if line[23:38] == "NOT APPLICABLE.":
					resolution = "N/A"
				elif line[31:].startswith("ANGSTROMS."):
					resolution = float(line[22:30])
				else:
					print(line)
					raise Exception("Error parsing PDB file.")
				
		PDBChains[d[FieldNames_.PDB_ID]] = chains.keys()
		
		if not resolution:
			raise Exception("Could not determine resolution for %s." % filename)
		if resolution == "N/A":
			resolution = None
		
		UniqueIDs[id] = True
			
		if not PDBToUniProt:
			readUniProtMap()
		if not PDBToUniProt.get(id):
			raise Exception("Could not find a UniProt mapping for %s in %s." % (id, uniprotmapping))
		d[FieldNames_.Content] = contents
		d[FieldNames_.Resolution] = resolution
		d[FieldNames_.Techniques] = techniques
		
		pdb = PDB(lines)
		pdbID = d[FieldNames_.PDB_ID]
		foundRes = pdb.CheckForPresenceOf(["CSE", "MSE"])
		if foundRes:
			colortext.error("The PDB %s contains residues which could affect computation (%s)." % (pdbID, join(foundRes, ", ")))
			if "CSE" in foundRes:
				colortext.error("The PDB %s contains CSE. Check." % pdbID)
			if "MSE" in foundRes:
				colortext.error("The PDB %s contains MSE. Check." % pdbID)

		d[FieldNames_.BFactors] = pickle.dumps(pdb.ComputeBFactors()) 
		
		return contents
			
	def commit(self, db):
		'''Returns the database record ID if an insert occurs but will typically return None if the PDB is already in the database.'''
		d = self.dict
		
		self.getPDBContents()
		assert(PDBChains.get(d[FieldNames_.PDB_ID]))
		
		results = db.execute("SELECT * FROM Structure WHERE PDB_ID=%s", parameters = (d[FieldNames_.PDB_ID]))
		
		if results:
			assert(len(results) == 1)
			result = results[0]
			pdbID = result[FieldNames_.PDB_ID]
			for k, v in d.iteritems():
				if k != FieldNames_.PDB_ID:
					if k == FieldNames_.Techniques and result[k] == "":
						SQL = "UPDATE Structure SET %s" % k
						SQL += "=%s WHERE PDB_ID=%s" 
						results = db.execute(SQL, parameters = (v, pdbID))
					if d[k] and not(result[k]):
						SQL = "UPDATE Structure SET %s" % k
						SQL += "=%s WHERE PDB_ID=%s" 
						results = db.execute(SQL, parameters = (v, pdbID))
		else:
			SQL = 'INSERT INTO Structure (PDB_ID, Content, Resolution, Protein, Source) VALUES (%s, %s, %s, %s, %s);'
			vals = (d[FieldNames_.PDB_ID], d[FieldNames_.Content], d[FieldNames_.Resolution], d[FieldNames_.Protein], d[FieldNames_.Source]) 
			db.execute(SQL, parameters = vals)
			self.databaseID = db.getLastRowID()
		
		return self.databaseID			
		
	def __repr__(self):
		d = self.dict
		str = []
		str.append("%s: %s" % (FieldNames_.PDB_ID, d[FieldNames_.PDB_ID]))
		str.append("%s: %s" % (FieldNames_.Protein, d[FieldNames_.Protein]))
		return join(str, "\n")

class ExperimentSet(DBObject):
	
	def __init__(self, pdbid, source, interface = None):
		self.dict = {
			FieldNames_.Structure	: pdbid,
			FieldNames_.Source		: source,
			FieldNames_.ScoreVariance: None,
			"Interface"				: interface,
			"Mutants"				: {},
			"Mutations"				: [],
			"ExperimentChains"		: [],
			"ExperimentScores"		: [],
			"StdDeviation"			: None,
			"WithinStdDeviation"	: None
		}
	
	def addMutant(self, mutant):
		self.dict["Mutants"][mutant] = True

	def addMutation(self, chainID, residueID, wildtypeAA, mutantAA, ID = None):
		errors = []
		residueID = ("%s" % residueID).strip()
		if not chainID in AllowedChainLetters:
			errors.append("The chain '%s' is invalid." % chainID)
		if not wildtypeAA in AllowedAminoAcids:
			errors.append("The wildtype amino acid '%s' is invalid." % wildtypeAA)
		if not mutantAA in AllowedAminoAcids:
			errors.append("The mutant amino acid '%s' is invalid." % mutantAA)
		if not residueID.isdigit():
			if not residueID[0:-1].isdigit():
				errors.append("The residue '%s' is invalid." % residueID)
			elif residueID[-1] not in AllowedInsertionCodes:
				errors.append("The insertion code '%s' of residue '%s' is invalid." % (residue[-1], residueID))
		if errors:
			ID = ID or ""
			if ID:
				ID = ", ID %s" % ID
			errors = join(['\t%s\n' % e for e in errors], "")
			raise Exception("An exception occurred processing a mutation in the dataset %s%s.\n%s" % (self.dict[FieldNames_.Source], ID, errors))
		self.dict["Mutations"].append({
			FieldNames_.Chain 		: chainID,
			FieldNames_.ResidueID	: residueID,
			FieldNames_.WildTypeAA	: wildtypeAA,
			FieldNames_.MutantAA	: mutantAA
			})
	
	def addChain(self, chainID, ID = ""):
		if not chainID in AllowedChainLetters:
			raise Exception("An exception occurred processing a chain in the dataset %s%s.\n\tThe chain '%s' is invalid." % (self.dict[FieldNames_.Source], ID, errors, chainID))
		self.dict["ExperimentChains"].append(chainID)
	
	def getChains(self):
		return self.dict["ExperimentChains"]
	
	def setMutantIfUnset(self, mutant):
		if not self.dict[FieldNames_.Mutant]:
			self.dict[FieldNames_.Mutant] = mutant
	
	def addExperimentalScore(self, sourceID, ddG, pdbID, numMeasurements = 1):
		if pdbID != self.dict[FieldNames_.Structure]:
			raise colortext.Exception("Adding experimental score related to PDB structure %s to an experiment whose PDB structure should be %s." % (pdbID, self.dict[FieldNames_.Structure]))
		self.dict["ExperimentScores"].append({
			FieldNames_.SourceID				: sourceID,
			FieldNames_.ddG						: ddG,
			FieldNames_.NumberOfMeasurements	: numMeasurements
			})
	
	def mergeScores(self, maxStdDeviation = 1.0):
		d = self.dict
		
		n = len(d["ExperimentScores"])
		if n > 1:
			n = float(n)
			sum = 0
			for experimentalResult in d["ExperimentScores"]:
				if experimentalResult[FieldNames_.NumberOfMeasurements] != 1:
					raise Exception("Cannot merge scores when individual scores are from more than one measurement. Need to add logic to do proper weighting.")
				sum += experimentalResult[FieldNames_.ddG]
			mean = sum / n
			squaredsum = 0
			for experimentalResult in d["ExperimentScores"]:
				diff = (experimentalResult[FieldNames_.ddG] - mean)
				squaredsum += diff * diff
			variance = squaredsum / n
			d[FieldNames_.ScoreVariance] = variance
			stddev = sqrt(variance)
			d["StdDeviation"] = stddev 
			d["WithinStdDeviation"] = stddev <= maxStdDeviation
		else:
			d[FieldNames_.ScoreVariance] = 0
			d["WithinStdDeviation"] = True	
	
	def isEligible(self):
		d = self.dict
		if d["WithinStdDeviation"] == None:
			raise Exception("Standard deviation not yet computed.")
		else:
			return d["WithinStdDeviation"]
	
	def __repr__(self):
		raise Exception('''This is unlikely to work as I have not tested it in a while. In particular, ddG is not a string anymore.''')
		d = self.dict
		str = []
		str.append("%s: %s" % (FieldNames_.Structure, d[FieldNames_.Structure]))
		str.append("%ss: %s" % (FieldNames_.Mutant, join(d["Mutants"].keys(), ', ')))
		str.append("%s: %s" % (FieldNames_.Source, d[FieldNames_.Source]))
		str.append("Chains: %s" % (join([chain for chain in d["ExperimentChains"]], ", ")))
		str.append("Mutations:")
		for mutation in d["Mutations"]:
			str.append("\t%s%s: %s -> %s" % (mutation[FieldNames_.Chain], mutation[FieldNames_.ResidueID], mutation[FieldNames_.WildTypeAA], mutation[FieldNames_.MutantAA]))
		str.append("Experimental Scores:")
		for score in d["ExperimentScores"]:
			n = score[FieldNames_.NumberOfMeasurements]
			if n > 1:
				str.append("\t%s\t%0.2f (%d measurements)" % (score[FieldNames_.SourceID], score[FieldNames_.ddG], score[FieldNames_.NumberOfMeasurements]))
			else:
				str.append("\t%s\t%0.2f" % (score[FieldNames_.SourceID], score[FieldNames_.ddG]))
		return join(str, "\n")
			
	def commit(self, db):
		'''Commits the set of experiments associated with the mutation to the database. Returns the unique ID of the associated Experiment record.'''
		d = self.dict
		
		for score in d["ExperimentScores"]:
			scoresPresent = True
			results = db.execute("SELECT Source, SourceID FROM Experiment INNER JOIN ExperimentScore ON Experiment.ID=ExperimentID WHERE Source=%s AND SourceID=%s", parameters = (d[FieldNames_.Source], score[FieldNames_.SourceID]))
			if results:
				return
		
		if not scoresPresent:
			raise Exception("This experiment has no associated scores.")
		
		if not d[FieldNames_.ScoreVariance]:
			self.mergeScores()
		
		if d["Mutants"]:
			for mutant in d["Mutants"].keys():
				MutantStructure = PDBStructure(mutant)
				MutantStructure.commit(db)
		
		# Sanity check that the chain information is correct (ProTherm has issues)
		pdbID = d[FieldNames_.Structure] 
		associatedRecords = sorted([score[FieldNames_.SourceID] for score in d["ExperimentScores"]])
		associatedRecordsStr = "%s (records: %s)" % (d[FieldNames_.Source], join(map(str, sorted([score[FieldNames_.SourceID] for score in d["ExperimentScores"]])),", "))
		chainsInPDB = PDBChains.get(d[FieldNames_.Structure])
		if not chainsInPDB:
			raise Exception("The chains for %s were not read in properly." % associatedRecordsStr)
		for c in self.dict["ExperimentChains"]:
			if not c in chainsInPDB:
				if len(chainsInPDB) == 1 and len(self.dict["ExperimentChains"]) == 1:
					colortext.warning("%s: Chain '%s' of %s does not exist in the PDB %s. Chain %s exists. Use that chain instead." % (pdbID, c, associatedRecordsStr, pdbID, chainsInPDB[0]))
					db.addChainWarning(pdbID, associatedRecords, c)
				else:
					db.addChainError(pdbID, associatedRecords, c)
					raise colortext.Exception("Error committing experiment:\n%s: Chain '%s' of %s does not exist in the PDB %s. Chains %s exist." % (pdbID, c, associatedRecordsStr, pdbID, join(chainsInPDB, ", ")))
				
		# Sanity check that the wildtypes of all mutations are correct
		WildTypeStructure = PDBStructure(pdbID)
		contents = WildTypeStructure.getPDBContents()
		pdb = PDB(contents.split("\n"))
		
		badResidues = ["CSE", "MSE"]
		foundRes = pdb.CheckForPresenceOf(badResidues)
		if foundRes:
			colortext.warning("The PDB %s contains residues which could affect computation (%s)." % (pdbID, join(foundRes, ", ")))
			for res in foundRes:
				colortext.warning("The PDB %s contains %s. Check." % (pdbID, res))
		for mutation in d["Mutations"]:
			foundMatch = False
			for resid, wtaa in sorted(pdb.ProperResidueIDToAAMap().iteritems()):
				c = resid[0]
				resnum = resid[1:].strip()
				if mutation[FieldNames_.Chain] == c and mutation[FieldNames_.ResidueID] == resnum and mutation[FieldNames_.WildTypeAA] == wtaa:
					foundMatch = True
			if not foundMatch:
				#raise colortext.Exception("%s: Could not find a match for mutation %s %s:%s -> %s in %s." % (pdbID, mutation[FieldNames_.Chain], mutation[FieldNames_.ResidueID], mutation[FieldNames_.WildTypeAA], mutation[FieldNames_.MutantAA], associatedRecordsStr ))
				colortext.error("%s: Could not find a match for mutation %s %s:%s -> %s in %s." % (pdbID, mutation[FieldNames_.Chain], mutation[FieldNames_.ResidueID], mutation[FieldNames_.WildTypeAA], mutation[FieldNames_.MutantAA], associatedRecordsStr ))
				
				#raise Exception(colortext.make_error("%s: Could not find a match for mutation %s %s:%s -> %s in %s." % (pdbID, mutation[FieldNames_.Chain], mutation[FieldNames_.ResidueID], mutation[FieldNames_.WildTypeAA], mutation[FieldNames_.MutantAA], associatedRecordsStr )))
				
		# To disable adding new experiments:	return here
		
		SQL = 'INSERT INTO Experiment (Structure, Source) VALUES (%s, %s);'
		vals = (d[FieldNames_.Structure], d[FieldNames_.Source]) 
		#print(SQL % vals)
		db.execute(SQL, parameters = vals)
		
		self.databaseID = db.getLastRowID()
		ExperimentID = self.databaseID
		#print(ExperimentID)
		
		for chain in d["ExperimentChains"]:
			SQL = 'INSERT INTO ExperimentChain (ExperimentID, Chain) VALUES (%s, %s);'
			vals = (ExperimentID, chain) 
			#print(SQL % vals)
			db.execute(SQL, parameters = vals)
		
		interface = d["Interface"]
		if interface:
			SQL = 'INSERT INTO ExperimentInterface (ExperimentID, Interface) VALUES (%s, %s);'
			vals = (ExperimentID, interface) 
			#print(SQL % vals)
			db.execute(SQL, parameters = vals)
		
		for mutant in d["Mutants"].keys():
			SQL = 'INSERT INTO ExperimentMutant (ExperimentID, Mutant) VALUES (%s, %s);'
			vals = (ExperimentID, mutant) 
			#print(SQL % vals)
			db.execute(SQL, parameters = vals)
		
		for mutation in d["Mutations"]:
			SQL = 'INSERT INTO ExperimentMutation (ExperimentID, Chain, ResidueID, WildTypeAA, MutantAA) VALUES (%s, %s, %s, %s, %s);'
			vals = (ExperimentID, mutation[FieldNames_.Chain], mutation[FieldNames_.ResidueID], mutation[FieldNames_.WildTypeAA], mutation[FieldNames_.MutantAA]) 
			#print(SQL % vals)
			db.execute(SQL, parameters = vals)
			
		for score in d["ExperimentScores"]:
			SQL = 'INSERT INTO ExperimentScore (ExperimentID, SourceID, ddG, NumberOfMeasurements) VALUES (%s, %s, %s, %s);'
			vals = (ExperimentID, score[FieldNames_.SourceID], score[FieldNames_.ddG], score[FieldNames_.NumberOfMeasurements]) 
			#print(SQL % vals)
			db.execute(SQL, parameters = vals)
		
		
		return self.databaseID

class Prediction(DBObject):
	
	def __init__(self, ExperimentID, PredictionSet, ToolID, ddG, status, NumberOfMeasurements = 1):
		self.dict = {
			FieldNames_.ExperimentID		: ExperimentID,
			FieldNames_.PredictionSet		: PredictionSet,
			FieldNames_.ToolID				: ToolID,
			FieldNames_.CommandID			: None,
			FieldNames_.KeptHETATMLines		: None,
			FieldNames_.StrippedPDB			: None,
			FieldNames_.InputFiles			: {},
			FieldNames_.Description			: {},
			FieldNames_.ddG					: ddG,
			FieldNames_.NumberOfMeasurements: NumberOfMeasurements,
			FieldNames_.Status				: status,
		}
		if ExperimentID == None:
			raise Exception("Cannot create the following Prediction - Missing ExperimentID:\n***\n%s\n***" % self)
		
	def setOptional(self, CommandID = None, KeptHETATMLines = None, StrippedPDB = None, InputFiles = None, Description = None):
		d = self.dict
		if CommandID:
			d[FieldNames_.CommandID] = CommandID
		if KeptHETATMLines:
			d[FieldNames_.KeptHETATMLines] = KeptHETATMLines
		if StrippedPDB:
			d[FieldNames_.StrippedPDB] = StrippedPDB
		if InputFiles:
			d[FieldNames_.InputFiles] = InputFiles
		if Description:
			d[FieldNames_.Description] = Description			
			
	def commit(self, db):
		d = self.dict
		d[FieldNames_.InputFiles] = pickle.dumps(d[FieldNames_.InputFiles])
		d[FieldNames_.Description] = pickle.dumps(d[FieldNames_.Description]) 
		fields = [FieldNames_.ExperimentID, FieldNames_.PredictionSet, FieldNames_.ToolID, FieldNames_.CommandID, FieldNames_.KeptHETATMLines, 
				FieldNames_.StrippedPDB, FieldNames_.InputFiles, FieldNames_.Description, FieldNames_.ddG, FieldNames_.NumberOfMeasurements, FieldNames_.Status]
		try:
			db.insertDict('Prediction', d, fields)
		except Exception, e:
			raise Exception("\nError committing prediction to database.\n***\n%s\n%s\n***" % (self, str(e)))
		self.databaseID = db.getLastRowID()
		return self.databaseID

	def __repr__(self):
		raise Exception('''This is unlikely to work as I have not tested it in a while.''')
		d = self.dict
		str = []
		str.append("%s: %s" % (FieldNames_.ExperimentID, d[FieldNames_.ExperimentID]))
		str.append("%s: %s" % (FieldNames_.PredictionSet, d[FieldNames_.PredictionSet]))
		str.append("%s: %d" % (FieldNames_.ToolID, d[FieldNames_.ToolID]))
		if d[FieldNames_.CommandID]:
			str.append("%s: %d" % (FieldNames_.CommandID, d[FieldNames_.CommandID]))
		if d[FieldNames_.KeptHETATMLines] == None:
			str.append("%s: NULL" % (FieldNames_.KeptHETATMLines))
		else:
			str.append("%s: %d" % (FieldNames_.KeptHETATMLines, d[FieldNames_.KeptHETATMLines]))
		n = d[FieldNames_.NumberOfMeasurements]
		if n > 1:
			str.append("%s: %0.2f (%d measurements)" % (FieldNames_.ddG, d[FieldNames_.ddG], n))
		else:
			str.append("%s: %0.2f" % (FieldNames_.ddG, d[FieldNames_.ddG]))
		
		str.append("%s:" % (FieldNames_.InputFiles))
		if d[FieldNames_.InputFiles]:
			ifiles = d[FieldNames_.InputFiles]
			if type(ifiles) == type(""):
				ifiles = pickle.loads(ifiles)
			for k,v in ifiles.iteritems():
				str.append("\t%s" % k)
		else:
			str.append("\tEmpty")
		str.append("%s:" % (FieldNames_.Description))
		if d[FieldNames_.Description]:
			idesc = d[FieldNames_.Description]
			if type(idesc) == type(""):
				idesc = pickle.loads(idesc)
			for k,v in idesc.iteritems():
				str.append("\t%s: %s" % (k, v))
		else:
			str.append("\tEmpty")
		
		return join(str, "\n")

	def __getitem__(self, key):
		return dict_[key]
		
class ddGDatabase(object):
	
	chainErrors = {}
	chainWarnings= {}
	
	def __init__(self):
		if os.path.exists("pw"):
			F = open("pw")
			passwd = F.read().strip()
			F.close()
		else:
			passwd = getpass.getpass("Enter password to connect to MySQL database:")
		self.connection = MySQLdb.Connection(host = "kortemmelab.ucsf.edu", db = "ddG", user = "kortemmelab", passwd = passwd, port = 3306, unix_socket = "/var/lib/mysql/mysql.sock")
		self.numTries = 32
		self.lastrowid = None
	
	def addChainWarning(self, pdbID, associatedRecords, c):
		chainWarnings = self.chainWarnings
		chainWarnings[pdbID] = chainWarnings.get(pdbID) or []
		chainWarnings[pdbID].append((associatedRecords, c))

	def addChainError(self, pdbID, associatedRecords, c):
		chainErrors = self.chainErrors
		chainErrors[pdbID] = chainErrors.get(pdbID) or []
		chainErrors[pdbID].append((associatedRecords, c))

	def getLastRowID(self):
		return self.lastrowid
		
	def close(self):
		self.connection.close()
	
	def insertDict(self, tblname, d, fields = None):
		'''Simple function for inserting a dictionary whose keys match the fieldnames of tblname.'''
		
		if fields == None:
			fields = sorted(d.keys())
		values = None
		try:
			SQL = 'INSERT INTO %s (%s) VALUES (%s)' % (tblname, join(fields, ", "), join(['%s' for x in range(len(fields))], ','))
			values = tuple([d[k] for k in fields])
	 		#print(SQL % values)
			self.execute(SQL, parameters = values)
		except Exception, e:
			if SQL and values:
				sys.stderr.write("\nSQL execution error in query '%s' %% %s at %s:" % (SQL, values, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nError: '%s'.\n" % (str(e)))
			sys.stderr.flush()
			raise Exception("Error occurred during database insertion.")

	def addTechniquesFields(self):
		'''Used to update missing Techniques fields as this field was added after the initial PDB import.'''
		return
		results = self.execute("SELECT * FROM Structure")
		for result in results:
			pdbID = result[FieldNames_.PDB_ID]
			contents = result[FieldNames_.Content]
			lines = contents.split("\n")
			for line in lines:
				if line.startswith("EXPDTA"):
					techniques = line[10:71].split(";")
					for k in range(len(techniques)):
						techniques[k] = techniques[k].strip() 
					techniques = join(techniques, ";")
					break
			if not result[FieldNames_.Techniques]:
				SQL = "UPDATE Structure SET %s" % FieldNames_.Techniques
				SQL += "=%s WHERE PDB_ID=%s"
				self.execute(SQL, parameters = (techniques, pdbID))

	def callproc(self, procname, parameters = (), cursorClass = MySQLdb.cursors.DictCursor, quiet = False):
		"""Calls a MySQL stored procedure procname. This uses DictCursor by default."""
		i = 0
		errcode = 0
		caughte = None
		while i < self.numTries:
			i += 1
			try:    
				cursor = self.connection.cursor(cursorClass)
				if type(parameters) != type(()):
					parameters = (parameters,)
				errcode = cursor.callproc(procname, parameters)
				results = cursor.fetchall()
				self.lastrowid = int(cursor.lastrowid)
				cursor.close()
				return results
			except MySQLdb.OperationalError, e:
				errcode = e[0]
				self.connection.ping()
				caughte = e
				continue
			except:                
				traceback.print_exc()
				break
		
		if not quiet:
			sys.stderr.write("\nSQL execution error call stored procedure %s at %s:" % (procname, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
			sys.stderr.flush()
		raise MySQLdb.OperationalError(caughte)
	
	def insert(self, table, fieldnames, values):
		try:
			sql = None
			valuestring = join(["%s" for field in fieldnames], ", ")
			sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, join(fieldnames, ", "), valuestring)
			#print(sql, values)
			if not len(fieldnames) == len(values):
				raise Exception("Fieldnames and values lists are not of equal size.")
			return
			self.execute(sql, parameters)
		except Exception, e:
			if sql:
				sys.stderr.write("\nSQL execution error in query '%s' %% %s at %s:" % (sql, values, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nError: '%s'.\n" % (str(e)))
			sys.stderr.flush()
			raise Exception("Error occurred during database insertion.")
		
	def execute(self, sql, parameters = None, cursorClass = MySQLdb.cursors.DictCursor, quiet = False):
		"""Execute SQL query. This uses DictCursor by default."""
		i = 0
		errcode = 0
		caughte = None
		while i < self.numTries:
			i += 1
			try:    
				cursor = self.connection.cursor(cursorClass)
				if parameters:
					errcode = cursor.execute(sql, parameters)
				else:
					errcode = cursor.execute(sql)
				self.connection.commit()
				results = cursor.fetchall()
				self.lastrowid = int(cursor.lastrowid)
				cursor.close()
				return results
			except MySQLdb.OperationalError, e:
				errcode = e[0]
				self.connection.ping()
				caughte = e
				continue
			except:                
				traceback.print_exc()
				break
		
		if not quiet:
			sys.stderr.write("\nSQL execution error in query %s at %s:" % (sql, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
			sys.stderr.flush()
		raise MySQLdb.OperationalError(caughte)
	
	def getStandardDeviation(self, ID):
		results = self.callproc("GetScores", ID)
		scores = []
		if len(results) == 1:
			return 0
		else:
			for result in results:
				if result["NumberOfMeasurements"] != 1:
					raise Exception("Need to add logic for calculating standard deviation.")
			scores = [result["ddG"] for result in results]
			stddev, variance = computeStandardDeviation(scores)
			return stddev

class DatabasePrimer(object):
	'''This class fills in initial values for Tool, AminoAcid, UniProtKB, and UniProtKBMapping. The last will print errors if the corresponding PDB is not in the database.'''
	
	def __init__(self, ddGdb):
		self.ddGdb = ddGdb
		if False:
			self.insertTools()
			self.insertAminoAcids()
			self.insertUniProtKB()
	
	def computeBFactors(self):
		SQL = 'SELECT PDB_ID, Content FROM Structure'
		results = self.ddGdb.execute(SQL)
		for result in results:
			pdbID = result["PDB_ID"]
			colortext.message(pdbID)
			pdb = PDB(result["Content"].split("\n"))
			BF = pickle.dumps(pdb.ComputeBFactors())
			SQL = ('UPDATE Structure SET %s=' % FieldNames_.BFactors) + '%s WHERE PDB_ID = %s'
			results = self.ddGdb.execute(SQL, parameters = (BF, pdbID))
	
	def checkForCSEandMSE(self):
		SQL = 'SELECT PDB_ID, Content FROM Structure'
		results = self.ddGdb.execute(SQL)
		for result in results:
			pdbID = result["PDB_ID"]
			pdb = PDB(result["Content"].split("\n"))
			foundRes = pdb.CheckForPresenceOf(["CSE", "MSE"])
			if foundRes:
				colortext.warning("The PDB %s contains residues which could affect computation (%s)." % (pdbID, join(foundRes, ", ")))
				if "CSE" in foundRes:
					colortext.printf(pdbID, color = 'lightpurple')
					colortext.warning("The PDB %s contains CSE. Check." % pdbID)
				if "MSE" in foundRes:
					colortext.printf(pdbID, color = 'lightpurple')
					colortext.warning("The PDB %s contains MSE. Check." % pdbID)
		
	def insertTools(self):
		emptydict = pickle.dumps({})
		
		# Tool name, Version, SVN information
		Tools = [
			('CC/PBSA',		'Unknown', 	0, emptydict),
			('EGAD', 		'Unknown', 	0, emptydict),
			('FoldX',		'3.0', 		0, emptydict),
			('Hunter',		'Unknown', 	0, emptydict),
			('IMutant2',	'2.0', 		0, emptydict),
		]
				
		Tools.append(('Rosetta', '2.1', 8075,
			pickle.dumps({
				"FirstBranchRevision"			:	9888,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-2.1",
				"SourceSVNRevision"				:	8075,
				"Source_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/rosetta++",
				"DatabaseSVNRevisionInTrunk"	:	7966,
				"Database_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/rosetta_database",
			})))

		Tools.append(('Rosetta', '2.1.1', 13074,
			pickle.dumps({
				"FirstBranchRevision"			:	13894 ,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-2.1.1",
				"SourceSVNRevision"				:	13074,
				"Source_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-2.1/rosetta++",
				"DatabaseSVNRevisionInTrunk"	:	13074,
				"Database_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-2.1/rosetta_database",
			})))

		Tools.append(('Rosetta', '2.1.2', 15393 ,
			pickle.dumps({
				"FirstBranchRevision"			:	15394,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-2.1.2",
				"SourceSVNRevision"				:	15393,
				"Source_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-2.1.1/rosetta++",
				"DatabaseSVNRevisionInTrunk"	:	15393,
				"Database_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-2.1.1/rosetta_database",
			})))

		Tools.append(('Rosetta', '2.2.0', 16310,
			pickle.dumps({
				"FirstBranchRevision"			:	16427,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-2.2.0",
				"SourceSVNRevision"				:	16310,
				"Source_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/rosetta++",
				"DatabaseSVNRevisionInTrunk"	:	15843,
				"Database_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/rosetta_database",
			})))

		Tools.append(('Rosetta', '2.3.0', 20729,
			pickle.dumps({
				"FirstBranchRevision"			:	20798,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-2.3.0",
				"SourceSVNRevision"				:	20729,
				"Source_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/rosetta++",
				"DatabaseSVNRevisionInTrunk"	:	20479,
				"Database_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/rosetta_database",
			})))
		
		Tools.append(('Rosetta', '2.3.1', 0,
			pickle.dumps({
				"FirstBranchRevision"			:	36012,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-2.3.1",
				"SourceSVNRevision"				:	None,
				"Source_SVN_URL"				:	None,
				"DatabaseSVNRevisionInTrunk"	:	None,
				"Database_SVN_URL"				:	None,
			})))
		
		Tools.append(('Rosetta', '3.0', 26316,
			pickle.dumps({
				"FirstBranchRevision"			:	26323 ,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-3.0",
				"SourceSVNRevision"				:	26316,
				"Source_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/mini",
				"DatabaseSVNRevisionInTrunk"	:	26298,
				"Database_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/minirosetta_database",
			})))

		Tools.append(('Rosetta', '3.1', 32528,
			pickle.dumps({
				"FirstBranchRevision"			:	30467,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-3.1",
				"SourceSVNRevision"				:	32528,
				"Source_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/mini",
				"DatabaseSVNRevisionInTrunk"	:	32509,
				"Database_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/minirosetta_database",
			})))

		Tools.append(('Rosetta', '3.2', 39284,
			pickle.dumps({
				"FirstBranchRevision"			:	39352,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-3.2",
				"SourceSVNRevision"				:	39284,
				"Source_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/mini",
				"DatabaseSVNRevisionInTrunk"	:	39117,
				"Database_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/minirosetta_database",
			})))

		Tools.append(('Rosetta', '3.2.1', 40878,
			pickle.dumps({
				"FirstBranchRevision"			:	40885,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-3.2.1",
				"SourceSVNRevision"				:	40878,
				"Source_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-3.2/rosetta_source",
				"DatabaseSVNRevisionInTrunk"	:	40878,
				"Database_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-3.2/rosetta_database",
			})))

		Tools.append(('Rosetta', '3.3', 42941,
			pickle.dumps({
				"FirstBranchRevision"			:	42943,
				"Branch_SVN_URL"				:	"https://svn.rosettacommons.org/source/branches/releases/rosetta-3.3",
				"SourceSVNRevision"				:	42941,
				"Source_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/mini",
				"DatabaseSVNRevisionInTrunk"	:	42940,
				"Database_SVN_URL"				:	"https://svn.rosettacommons.org/source/trunk/minirosetta_database",
			})))
	
		for t in Tools:
			SQL = 'SELECT * FROM Tool WHERE Name=%s AND Version=%s AND SVNRevision=%s'
			numresults = len(self.ddGdb.execute(SQL, parameters = (t[0], t[1], t[2])))
			assert(numresults == 0 or numresults == 1)
			if numresults == 0:
				SQL = 'INSERT INTO Tool (Name, Version, SVNRevision, SVNRevisionInfo) VALUES (%s, %s, %s, %s)'
				self.ddGdb.execute(SQL, parameters = t)
	
	def deleteAllExperimentalData(self):
		'''THIS WILL REMOVE *ALL* EXPERIMENTAL DATA FROM THE DATABASE. USE AT GREAT RISK!
		   This function runs much quicker than the selective data removal function removeExperimentalData.
		   It should fail when there are associated Predictions as this breaks a foreign key constraint.
		   This is by design; Prediction data should not be deleted lightly.
		   To avoid deleting the other records associated with the Experiment, we raise an exception first.
		  '''
		
		predictions = self.ddGdb.execute('SELECT * FROM Prediction')
		if not predictions:
			results = self.ddGdb.execute('DELETE FROM ExperimentInterface')
			results = self.ddGdb.execute('DELETE FROM ExperimentChain')
			results = self.ddGdb.execute('DELETE FROM ExperimentMutation')
			results = self.ddGdb.execute('DELETE FROM ExperimentMutant')
			results = self.ddGdb.execute('DELETE FROM ExperimentScore')
			results = self.ddGdb.execute('DELETE FROM Experiment')
		else:
			raise Exception("Database integrity failure: Cannot delete an Experiment (ID = %s) with an associated Prediction (ID = %s)." % (ID, predictions[0]['ID']))

	def deleteExperimentalDataByDataset(self):
		'''THIS WILL REMOVE ALL EXPERIMENTAL DATA FROM THE removethese ARRAY FROM THE DATABASE. USE AT GREAT RISK!
		   It should fail when there are associated Predictions as this breaks a foreign key constraint.
		   This is by design; Prediction data should not be deleted lightly.
		   To avoid deleting the other records associated with the Experiment, we raise an exception first.
		  '''
		
		removethese = ["Potapov-2009", "SenLiu-ComplexExperimentalDataset", "ProTherm-2008-09-08-23581"]
		experimentIDs = []
		for dataset in removethese:
			SQL = 'SELECT ID FROM Experiment WHERE Source=%s'
			results = self.ddGdb.execute(SQL, parameters = (dataset,))
			for result in results:
				experimentIDs.append(result['ID'])
		
		for ID in experimentIDs:
			predictions = self.ddGdb.execute('SELECT * FROM Prediction WHERE ExperimentID=%s', parameters = (ID,))
			if not predictions:
				results = self.ddGdb.execute('DELETE FROM ExperimentInterface WHERE ExperimentID=%s', parameters = (ID,))
				results = self.ddGdb.execute('DELETE FROM ExperimentChain WHERE ExperimentID=%s', parameters = (ID,))
				results = self.ddGdb.execute('DELETE FROM ExperimentMutation WHERE ExperimentID=%s', parameters = (ID,))
				results = self.ddGdb.execute('DELETE FROM ExperimentMutant WHERE ExperimentID=%s', parameters = (ID,))
				results = self.ddGdb.execute('DELETE FROM ExperimentScore WHERE ExperimentID=%s', parameters = (ID,))
				results = self.ddGdb.execute('DELETE FROM Experiment WHERE ID=%s', parameters = (ID,))
			else:
				raise Exception("Database integrity failure: Cannot delete an Experiment (ID = %s) with an associated Prediction (ID = %s)." % (ID, predictions[0]['ID']))
	
	def insertUniProtKB(self):
		uniprot = os.path.join("rawdata", "uniprotmapping.csv")
		F = open(uniprot)
		lines = F.read().split("\n")[1:]
		F.close()
		UniProtKB = {}
		UniProtKBMapping = {}
		
		for line in lines:
			data = line.split("\t")
			if len(data) == 3:
				PDBID, AC, ID = data 
				UniProtKB[AC] = ID
				UniProtKBMapping[AC] = UniProtKBMapping.get(AC, []) or []
				UniProtKBMapping[AC].append(PDBID)
		
		for AC, ID in sorted(UniProtKB.iteritems()):
			if not self.ddGdb.execute("SELECT * FROM UniProtKB WHERE UniProtKB_AC=%s", parameters = (AC,)):
				SQL = 'INSERT INTO UniProtKB (UniProtKB_AC, UniProtKB_ID) VALUES (%s, %s);'
				self.ddGdb.execute(SQL, parameters = (AC, ID))
		
		for AC, pdbIDs in sorted(UniProtKBMapping.iteritems()):
			for pdbID in pdbIDs:
				if not self.ddGdb.execute("SELECT * FROM UniProtKBMapping WHERE UniProtKB_AC=%s AND PDB_ID=%s", parameters = (AC, pdbID)):
					SQL = 'INSERT INTO UniProtKBMapping (UniProtKB_AC, PDB_ID) VALUES (%s, %s);'
					try:
						self.ddGdb.execute(SQL, parameters = (AC, pdbID), quiet = True)
					except:
						pass
			
		
	def insertAminoAcids(self):
		global aas
		for aa in aas:
			SQL = 'INSERT INTO AminoAcids (Code, LongCode, Name, Polarity, Size) VALUES (%s, %s, %s, %s, %s);'
			self.ddGdb.execute(SQL, parameters = tuple(aa))

if __name__ == "__main__":
	ddGdb = ddGDatabase()
	primer = DatabasePrimer(ddGdb)
	#primer.checkForCSEandMSE()
	#primer.computeBFactors()
	#print("Removing all data")
	#primer.deleteAllExperimentalData()
	primer.insertTools()
	
