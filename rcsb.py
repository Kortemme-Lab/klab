from string import join
from httplib import HTTPConnection
import colortext

visible_colors = [
	'lightblue'		,
	'lightgreen'	,
	'yellow'		,
	'pink'			,
	'cyan'			,
	'lightpurple'	,
	'white'			,
	'aqua'			,
	'green'			,
	'orange'		,
	'purple'		,
	'grey'			,
	'silver'		,
	]

def getPDB(pdbID):
	colortext.printf("Retrieving PDB file", color = "aqua")
	c = HTTPConnection("www.rcsb.org")
	c.request("GET", "/pdb/files/%s.pdb" % pdbID)
	response = c.getresponse()
	contents = response.read()
	c.close()
	if contents[0:6] == "<html>":
		raise Exception("Error retrieving %s." % filename)
	return contents

def getFASTA(pdbID, database_ref = None, database_table = None, database_field = None, database_IDfield = None):
	if database_ref and database_table and database_field and database_IDfield:
		results = database_ref.execute(("SELECT %s FROM %s WHERE %s=" % (database_field, database_table, database_IDfield)) + "%s", parameters = (pdbID,))
		if results:
			assert(len(results) == 1)
			return results[0][database_field] 
	colortext.printf("Retrieving FASTA file", color = "aqua")
	c = HTTPConnection("www.rcsb.org")
	c.request("GET", "/pdb/files/fasta.txt?structureIdList=%s" % pdbID)
	response = c.getresponse()
	contents = response.read()
	c.close()
	if contents[0:6] == "<html>":
		raise Exception("Error retrieving %s." % filename)
	return contents

class FASTA(dict):
	
	fasta_chain_header_ = "|PDBID|CHAIN|SEQUENCE"
	
	def __init__(self, *args, **kw):
		super(FASTA,self).__init__(*args, **kw)
		self.itemlist = super(FASTA,self).keys()
		self.unique_sequences = {}
		self.sequences = []
		self.sequence_string_length = 120
	
	def getNumberOfUniqueSequences(self):
		return len(self.unique_sequences)
	
	def addSequence(self, pdbID, chainID, sequence):
		pdbID = pdbID.upper() 
		self[pdbID] = self.get(pdbID, {})
		self[pdbID][chainID] = sequence
		self.sequences.append((pdbID, chainID, sequence))
		if not self.unique_sequences.get(sequence):
			self.unique_sequences[sequence] = visible_colors[len(self.unique_sequences) % len(visible_colors)]
		self.identical_sequences = None
	
	def getChains(self, pdbID):
		pdbID = pdbID.upper() 
		if not self.get(pdbID):
			raise Exception("FASTA object does not contain sequences for PDB %s." % pdbID)
		return self[pdbID].keys()
	
	def findIdenticalSequences(self):
		sequences = self.sequences
		identical_sequences = {}
		numseq = len(self.sequences)
		for x in range(numseq):
			for y in range(x + 1, numseq):
				pdbID1 = sequences[x][0]
				pdbID2 = sequences[y][0]
				chain1 = sequences[x][1]
				chain2 = sequences[y][1]
				if sequences[x][2] == sequences[y][2]:
					identical_sequences[pdbID1] = identical_sequences.get(pdbID1, {})
					identical_sequences[pdbID1][chain1]=identical_sequences[pdbID1].get(chain1, [])
					identical_sequences[pdbID1][chain1].append("%s:%s" % (pdbID2, chain2))
					identical_sequences[pdbID2] = identical_sequences.get(pdbID2, {})
					identical_sequences[pdbID2][chain2]=identical_sequences[pdbID2].get(chain2, [])
					identical_sequences[pdbID2][chain2].append("%s:%s" % (pdbID1, chain1))
		self.identical_sequences = identical_sequences
	
	def match(self, other):
		colortext.message("FASTA Match")
		for frompdbID, fromchains in sorted(self.iteritems()):
			matched_pdbs = {}
			matched_chains = {}
			for fromchain, fromsequence in fromchains.iteritems():
				for topdbID, tochains in other.iteritems():
					for tochain, tosequence in tochains.iteritems():
						if fromsequence == tosequence:
							matched_pdbs[topdbID] = matched_pdbs.get(topdbID, set())
							matched_pdbs[topdbID].add(fromchain)
							matched_chains[fromchain] = matched_chains.get(fromchain, [])
							matched_chains[fromchain].append((topdbID, tochain))
			foundmatches = []
			colortext.printf("  %s" % frompdbID, color="silver")
			for mpdbID, mchains in matched_pdbs.iteritems():
				if mchains == set(fromchains.keys()):
					foundmatches.append(mpdbID)
					colortext.printf("  PDB %s matched PDB %s on all chains" % (mpdbID, frompdbID), color="white")
			if foundmatches:
				for fromchain, fromsequence in fromchains.iteritems():
					colortext.printf("    %s" % (fromchain), color = "silver")
					colortext.printf("      %s" % (fromsequence), color = self.unique_sequences[fromsequence])
					mstr = []
					for mchain in matched_chains[fromchain]:
						if mchain[0] in foundmatches:
							mstr.append("%s chain %s" % (mchain[0], mchain[1]))
					colortext.printf("	  Matches: %s" % join(mstr, ", "))
			else:
				colortext.error("    No matches found.")
	
	def __repr__(self):
		splitsize = self.sequence_string_length
		self.findIdenticalSequences()
		identical_sequences = self.identical_sequences
		s = []
		s.append(colortext.make("FASTA: Contains these PDB IDs - %s" % join(self.keys(), ", "), color="green"))
		s.append("Number of unique sequences : %d" % len(self.unique_sequences))
		s.append("Chains:")
		for pdbID, chains_dict in self.iteritems():
			s.append("  %s" % pdbID)
			for chainID, sequence in chains_dict.iteritems():
				s.append("    %s" % chainID)
				color = self.unique_sequences[sequence]
				split_sequence = [sequence[i:i+splitsize] for i in range(0, len(sequence), splitsize)]
				for seqpart in split_sequence:
					s.append(colortext.make("      %s" % seqpart, color=color))
				if identical_sequences.get(pdbID) and identical_sequences[pdbID].get(chainID):
					iseqas = identical_sequences[pdbID][chainID]
					s.append("	  Identical sequences: %s" % join(iseqas, ", "))
				
		return join(s, "\n")
	
def parseFASTAs(fasta_list, silent = False, database_ref = None, database_table = None, database_field = None, database_IDfield = None):
			
	if type(fasta_list) == type(""):
		fasta_list = [fasta_list]
	assert(type(fasta_list) == type([]))
	
	allPDBIDs = True
	lengths = [len(f) == 4 for f in fasta_list]
	for l in lengths:
		if not l:
			allPDBIDs = False
			break
	
	if allPDBIDs:
		new_list = []
		for pdbID in fasta_list:
			if not(silent):
				colortext.message("Retrieving %s.fasta." % pdbID)
			new_list.append(getFASTA(pdbID, database_ref = database_ref, database_table = database_table, database_field = database_field, database_IDfield = database_IDfield))
		fasta_list = new_list
	
	fasta = join(fasta_list, "\n")
	
	f = FASTA()
	sequences = []
	chains = [c for c in fasta.split(">") if c]
	for c in chains:
		assert(c[4:5] == ":")
		assert(c[6:].startswith(FASTA.fasta_chain_header_))
		f.addSequence(c[0:4], c[5:6], c[6 + len(FASTA.fasta_chain_header_):].replace("\n","").strip())
	return f
