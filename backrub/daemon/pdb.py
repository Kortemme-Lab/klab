#!/usr/bin/python2.4


import re
import sys
import types
import string
import UserDict
import spatialhash
import chainsequence

#todo: replace with ROSETTAWEB_SK_AA
aa1 = {"ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
       "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
       "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
       "TRP": "W", "TYR": "Y"}

residues = ["ALA", "CYS", "ASP", "ASH", "GLU", "GLH", "PHE", "GLY", "HIS", 
            "HIE", "HIP", "ILE", "LYS", "LYN", "LEU", "MET", "ASN", "PRO", 
            "GLN", "ARG", "ARN", "SER", "THR", "VAL", "TRP", "TYR"]

# todo: replace residues with this and move to rwebhelper.py
allowedResidues = {}
for r in residues:
    allowedResidues[r] = True

nucleotides_dna = ["DT","DA","DC","DG"]
nucleotides_rna = ["U","C","G","A"]

          
records = ["HEADER","OBSLTE","TITLE","SPLIT","CAVEAT","COMPND","SOURCE","KEYWDS",
           "EXPDTA","NUMMDL","MDLTYP","AUTHOR","REVDAT","SPRSDE","JRNL","REMARK",
           "DBREF","DBREF1","DBREF2","DBREF1/DBREF2","SEQADV","SEQRES","MODRES",
           "HET","HETNAM","HETSYN","FORMUL","HELIX","SHEET","SSBOND","LINK","CISPEP",
           "SITE","CRYST1","ORIGX1","ORIGX2","ORIGX3","SCALE1","SCALE2","SCALE3",
           "MTRIX1","MTRIX2","MTRIX3","MODEL","ATOM","ANISOU","TER","HETATM",
           "ENDMDL","CONECT","MASTER","END"]

# todo: This is duplicated in rosettahelper as unique. After refactorization, remove this duplicate
# maybe remove it entirely as it's outside code and is overkill for how it's used in this file
def myunique(s):
    """Return a list of the elements in s, but without duplicates.
    http://code.activestate.com/recipes/52560/
    """
    # case 0, empty object
    n = len(s)
    if n == 0:
        return []

    # case 1: if the objects in the list are hashable, try to use a dict
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()

    # case 2: objects are not hashable, use sorting
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]

    # case 3: Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u

class PDB:
    """A class to store and manipulate PDB data"""
  
    ## Constructor:
  # takes either a pdb file, a list of strings = lines of a pdb file, or another object
  # 
  # 
    def __init__(self, pdb = None):
    
        self.lines = []
        if type(pdb) == types.StringType:
            self.read(pdb)
        elif type(pdb) == types.ListType:
            self.lines.extend(pdb)
        elif type(pdb) == type(self):
            self.lines.extend(pdb.lines)
    
    def read(self, pdbpath):
    
        pdbhandle = open(pdbpath)
        self.lines = pdbhandle.readlines()
        pdbhandle.close()
    
    def write(self, pdbpath):
    
        pdbhandle = open(pdbpath, "w")
        text = string.join(self.lines, '\n')
        pdbhandle.write(text)
        pdbhandle.close()
    
    def remove_nonbackbone_atoms(self, resid_list):
    
        backbone_atoms = set(["N", "CA", "C", "O", "OXT"])
    
        resid_set = set(resid_list)
    
        self.lines = [line for line in self.lines if line[0:4] != "ATOM" or
                                                     line[21:26] not in resid_set or
                                                     line[12:16].strip() in backbone_atoms]

    def fix_backbone_occupancy(self):
    
        backbone_atoms = set(["N", "CA", "C", "O"])
    
        for i in xrange(len(self.lines)):
            line = self.lines[i]
            if line.startswith("ATOM") and line[12:16].strip() in backbone_atoms and float(line[54:60]) == 0:
                self.lines[i] = line[:54] + "  1.00" + line[60:]
                
    def fix_chain_id(self):
        """fill in missing chain identifier""" 
        
        for i in xrange(len(self.lines)):
            line = self.lines[i]
            if line.startswith("ATOM") and line[21] == ' ':
                self.lines[i] = line[:21] + 'A' + line[22:]
                

    def remove_hetatm(self):
    
        self.lines = [line for line in self.lines if not line.startswith("HETATM")]

    
    def aa_resids(self, only_res=None):
    
        if only_res:
          atomlines = [line for line in self.lines if line[0:4] == "ATOM" and line[17:20] in residues and line[26] == ' ']
        else:  
          atomlines = [line for line in self.lines if line[0:4] == "ATOM" and (line[17:20] in residues or line[18:20] in nucleotides_dna or line[19:20] in nucleotides_rna ) and line[26] == ' ']

        resid_set = set()
        resid_list = []
    
        # todo: Seems a little expensive to create a set, check 'not in', and do fn calls to add to the set. Use a dict instead? 
        for line in atomlines:
            resid = line[21:26]
            if resid not in resid_set:
                resid_set.add(resid)
                resid_list.append(resid)
        
        return resid_list # format: "A 123" or: '%s%4.i' % (chain,resid)
    
        
    def aa_resid2type(self):
        '''this creates a dictionary where the resid "A 123" is mapped to the one-letter aa type'''

        resid2type = {}

        for line in self.lines:
            resname = line[17:20]
            if line[0:4] == "ATOM" and resname in residues and line[26] == ' ' and line[13:16] == 'CA ':
                resid2type[line[21:26]] = aa1[resname]

        return resid2type # format: "A 123" or: '%s%4.i' % (chain,resid)    
        
    def pruneChains(self, chainsChosen):
        # If chainsChosen is non-empty then removes any ATOM lines of chains not in chainsChosen
        if chainsChosen and (sorted(chainsChosen) != sorted(self.chain_ids())):
            templines = []
            for line in self.lines:
                # todo: All this looks suboptimal - we read through the lines multiple times with similar string selection
                if line[0:4] == "ATOM" and line[17:20] in residues and line[26] == ' ':
                    chain = line[21:22]
                    if chain in chainsChosen:
                        # Only keep ATOM lines for chosen chains
                        templines.append(line)
                else:
                    # Keep all non-ATOM lines
                    templines.append(line)
            self.lines = templines
    
    def chain_ids(self):
        chain_ids = set()
        chainlist = []
        for line in self.lines:
            if line[0:4] == "ATOM" and line[17:20] in residues and line[26] == ' ':
                chain = line[21:22]
                if chain not in chain_ids:
                    chain_ids.add(chain)
                    chainlist.append(chain)
                    
        return chainlist
        
    def number_of_models(self):
        return len( [line for line in self.lines if line[0:4] == 'MODEL'] )
    
    
    def fix_residue_numbering(self):
        """this function renumbers the res ids in order to avoid strange behaviour of Rosetta"""
        
        resid_list = self.aa_resids()
        resid_set  = set(resid_list)
        resid_lst1 = list(resid_set)
        resid_lst1.sort()
        map_res_id = {}
        
        x = 1
        old_chain = resid_lst1[0][0]
        for resid in resid_lst1:
            map_res_id[resid] = resid[0] + '%4.i' % x
            if resid[0] == old_chain:
                x+=1
            else:
                x = 1
                old_chain = resid[0]
        
        atomlines = []
        for line in self.lines:
            if line[0:4] == "ATOM" and line[21:26] in resid_set and line[26] == ' ':
                lst = [char for char in line]
                #lst.remove('\n')
                lst[21:26] = map_res_id[line[21:26]]
                atomlines.append( string.join(lst,'') )
                #print string.join(lst,'')
            else:
                atomlines.append(line)
                
        self.lines = atomlines
        return map_res_id
     
    
    def get_residue_mapping(self):
        """this function maps the chain and res ids "A 234" to values from [1-N]"""
        
        resid_list = self.aa_resids()
        # resid_set  = set(resid_list)
        # resid_lst1 = list(resid_set)
        # resid_lst1.sort()
        map_res_id = {}
        
        x = 1
        for resid in resid_list:
            # map_res_id[ int(resid[1:].strip()) ] = x
            map_res_id[ resid ] = x
            x+=1
        return map_res_id
    
    def atomlines(self, resid_list = None):
    
        if resid_list == None:
            resid_list = self.aa_resids()
    
        resid_set = set(resid_list)
    
        return [line for line in self.lines if line[0:4] == "ATOM" and line[21:26] in resid_set and line[26] == ' ' ]


    def neighbors(self, distance, residue, atom = None, resid_list = None): #atom = " CA "
    
        if atom == None:     # consider all atoms
            lines = [line for line in self.atomlines(resid_list)]
        else:                # consider only given atoms
            lines = [line for line in self.atomlines(resid_list) if line[12:16] == atom]
    
        shash = spatialhash.SpatialHash(distance)
    
        #resid_pos = []
        
        for line in lines:
            pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
            shash.insert(pos, line[21:26])
    
        neighbor_list = []        # (key, value) = (resid, 
        
        for line in lines:
            #print line
            resid = line[21:26]
            #print resid[1:-1], str(residue).rjust(4), resid[1:-1] == str(residue).rjust(4)
            if resid[1:] == str(residue).rjust(4):
                pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
                for data in shash.nearby(pos, distance):
                    if data[1] not in neighbor_list:
                        #print data
                        neighbor_list.append(data[1])
                neighbor_list.sort()
        return neighbor_list


    #todo 29: Optimise all callers of this function by using fastneighbors2 instead
    def neighbors2(self, distance, chain_residue, atom = None, resid_list = None):  
        
        #atom = " CA "
        '''this one is more precise since it uses the chain identifier also'''
        
        if atom == None:     # consider all atoms
            lines = [line for line in self.atomlines(resid_list) if line[17:20] in residues]
        else:                # consider only given atoms
            lines = [line for line in self.atomlines(resid_list) if line[17:20] in residues and line[12:16] == atom]
        
        shash = spatialhash.SpatialHash(distance)
        
        for line in lines:
            pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
            shash.insert(pos, line[21:26])
        
        neighbor_list = []
        for line in lines:
            resid = line[21:26]
            if resid == chain_residue:
                pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
                
                for data in shash.nearby(pos, distance):
                    if data[1] not in neighbor_list:
                        neighbor_list.append(data[1])
                neighbor_list.sort()
        return neighbor_list

    def fastneighbors2(self, distance, chain_residues, atom = None, resid_list = None):  

        # Create the spatial hash and construct a list of positions matching chain_residue
        
        #chainResPositions holds all positions related to a chain residue (A1234) defined on ATOM lines
        chainResPositions = {}
        for res in chain_residues:
            chainResPositions[res] = []
        
        shash = spatialhash.SpatialHash3D(distance)
                
        # This could be made fast by inlining atomlines and avoiding creating line[21:26] twice and by reusing resids rather than recomputing them
        # However, the speedup may not be too great and would need profiling
        for line in self.atomlines(resid_list):
            if line[17:20] in residues:
                if atom == None or line[12:16] == atom:                    
                    resid = line[21:26]
                    pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
                    shash.insert(pos, resid)
                    if resid in chain_residues:
                        chainResPositions[resid].append(pos)
        
        neighbors = {}
        # for all residues ids (A1234) in chain residues and all their positions,
        #   get a list of all ((x,y,z),resid) tuples within a radius of distance and add them uniquely to neighbor_list
        #   sort the list and store in neighbors
        for resid in chain_residues:
            neighbor_list = {}
            for pos in chainResPositions[resid]:               
                for data in shash.nearby(pos):
                    neighbor_list[data[1]] = True
            neighbors[resid] = neighbor_list.keys()
                
        return neighbors
        
    def neighbors3(self, distance, chain_residue, atom = None, resid_list = None):
      '''this is used by the sequence tolerance scripts to find the sc-sc interactions only'''
      
      backbone_atoms = [' N  ',' CA ',' C  ',' O  ']
                
      lines = [line for line in self.atomlines(resid_list) if line[12:16] not in backbone_atoms] # this excludes backbone atoms
      lines = [line for line in lines if line[13] != 'H'] # exclude hydrogens too!
      
      shash = spatialhash.SpatialHash(distance)

      #resid_pos = []

      for line in lines:
          pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
          shash.insert(pos, line[21:26])

      neighbor_list = []        # 
      for line in lines:
          resid = line[21:26]
          if resid == chain_residue:
              pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
              for data in shash.nearby(pos, distance):
                  if data[1] not in neighbor_list:
                      neighbor_list.append(data[1])
              neighbor_list.sort()
      return neighbor_list
    

    def get_stats(self):
      counts = {}
      counts["models"]   = self.number_of_models()
      counts["residues"] = len(self.aa_resids())
      counts["chains"]   = len(self.chain_ids())
      counts["atoms"]    = len(self.atomlines())
      counts["cys"]      = len([line for line in self.lines if line[0:4] == "ATOM" and line[13:16] == 'CA ' and line[17:20] == "CYS" and line[26] == ' '])
      
      return counts
    
    # This function can be expanded to allow us to use non-standard PDB files such as the ones given
    # as examples in the RosettaCon 2010 sequence tolerance protocol based on Smith, Kortemme 2010. 
    def check_custom_format(self, line, lineidx):
        if line[0:9] == "FOLD_TREE":
            return True
        return False          
    
    def check_format(self, usingClassic):
        
        warnings = []
        errors = []
        lineidx = 1
        # remove leading and trailing empty lines
        for line in self.lines:
            if len(line.strip()) == 0:
                self.lines.remove(line)
                lineidx = lineidx + 1
            else:
                break
      
        for line in reversed(self.lines):
            if len(line.strip()) == 0:
                self.lines.remove(line)
            else:
                break
      
        currentChain = None
        oldChain = None
        TERidx = 0
        ATOMidx = 0
        
        # Unused but handy to have for debugging
        residueNumber = 0
        
        # Variables for checking missing backbone residues
        # todo: We quit at the moment on first error. We should return a list of errors.
        missingBackboneResidues = False
        lastResidue = None
        currentResidue = None
        NFOUND = 2 ** 0
        OFOUND = 2 ** 1
        CFOUND = 2 ** 2
        CAFOUND = 2 ** 3
        CBFOUND = 2 ** 4
        bbatoms = ["N", "O", "C", "CA", "CB"]
        # todo: Use Bitarray or similar when Python is upgraded to 2.5 or higher
        ALLFOUND = NFOUND + OFOUND + CFOUND + CAFOUND + CBFOUND
        backboneAtoms = {}
        backboneAtoms[" "] = ALLFOUND
        oldres = ""
        
        # Check for bad resfile input to classic
        resfileEntries = {}
        classicErrors = []
        
        for line in self.lines:

            if line[0:4] == "ATOM":
                alternateConformation = line[16]
                residue = line[17:20]
                currentChain = line[21]
                currentResidue = line[21:27]
                classicCurrentResidue = line[21:26] # classic did not handle the insertion code in resfiles until revision 29386
                            
                
                if usingClassic and (not allowedResidues.get(residue)):
                    # Check for residues outside the list classic can handle
                    classicErrors.append("Residue %s on line %d is not recognized by classic." % (residue, lineidx))
                elif (oldChain != None) and (currentChain == oldChain):
                    # Check for bad TER fields
                    oldChain = None    
                    errors.append("A TER field on line %d interrupts two ATOMS on lines %d and %d with the same chain %s." % (TERidx, ATOMidx, lineidx, currentChain))
                ATOMidx = lineidx
                
                if lastResidue != currentResidue:
                    residueNumber += 1
                
                    # Check for malformed resfiles for classic
                    if usingClassic:
                        if not resfileEntries.get(classicCurrentResidue):
                            resfileEntries[classicCurrentResidue] = (currentResidue, lineidx)
                        else:
                            oldRes = resfileEntries[classicCurrentResidue][0]
                            oldLine = resfileEntries[classicCurrentResidue][1]
                            if currentResidue == resfileEntries[classicCurrentResidue][0]:
                                classicErrors.append("Residue %(currentResidue)s on line %(lineidx)d was already defined on line %(oldLine)d." % vars())
                            else:
                                classicErrors.append("Residue %(currentResidue)s on line %(lineidx)d has the same sequence number (ignoring iCode) as residue %(oldRes)s on line %(oldLine)d." % vars())
                    
                    # Check for missing backbone residues
                    # Add the backbone atoms common to all alternative conformations to the common conformation 
                    if not usingClassic:
                        commonToAllAlternatives = (2 ** 5) -1
                        for conformation, bba in backboneAtoms.items():
                            if conformation != " ":
                                commonToAllAlternatives &= backboneAtoms[conformation]
                        backboneAtoms[" "] |= commonToAllAlternatives
                    
                    ps = ""
                    for conformation, bba in backboneAtoms.items():
                        # Add the backbone atoms of the common conformation to all alternatives
                        if not usingClassic:
                            backboneAtoms[conformation] |= backboneAtoms[" "]
                        
                        if backboneAtoms[conformation] != (2 ** 5) - 1:
                            missing = []
                            for m in range(len(bbatoms)):
                                if not(backboneAtoms[conformation] & (2 ** m)):
                                    missing.append(bbatoms[m])
                            s = ""
                            if len(missing) > 1:
                                s = "s"
                            missing = string.join(missing, ",")
                            
                            failedClassic = False
                            if backboneAtoms[conformation] | backboneAtoms[" "] == (2 ** 5) - 1:
                                failedClassic = True
                                ps = " The common conformation correctly has these atoms." 
                            if conformation == " ":
                                conformation = "common"
                            
                            errstring = "The '%s' residue on line %d is missing the backbone atom%s %s in the %s conformation.%s" % (oldres, lineidx - 1, s, missing, conformation, ps)
                            if ps:
                                classicErrors.append(errstring)
                            else:
                                errors.append(errstring)
                    backboneAtoms = {}
                    backboneAtoms[" "] = 0
                    lastResidue = currentResidue
                oldres = residue
                atom = line[12:16]
                backboneAtoms[alternateConformation] = backboneAtoms.get(alternateConformation) or 0
                if atom == ' N  ':
                    backboneAtoms[alternateConformation] |= NFOUND
                elif atom == ' O  ' or atom == ' OT1' or atom == ' OT2':
                    backboneAtoms[alternateConformation] |= OFOUND
                elif atom == ' C  ':
                    backboneAtoms[alternateConformation] |= CFOUND
                elif atom == ' CA ':
                    backboneAtoms[alternateConformation] |= CAFOUND
                if atom == ' CB ' or residue == 'GLY':
                    backboneAtoms[alternateConformation] |= CBFOUND
                
            elif line[0:3] == "TER":
                oldChain = currentChain
                TERidx = lineidx            
    
    # print len(line),'\t', line[0:6]
            # remove all white spaces, and check if the line is empty or too long:
            if len(line.strip()) == 0:
                errors.append("Empty line found on line %d." % lineidx)
            elif len(line.rstrip()) > 81:
                errors.append("Line %d is too long." % lineidx)
            # check if the file contains tabs
            elif '\t' in line:
                errors.append("The file contains tabs on line %d." % lineidx)
            # check whether the records in the file are conform with the PDB format
            elif not line[0:6].rstrip() in records:
                if not self.check_custom_format(line, lineidx):
                    errors.append("Unknown record (%s) on line %d." % (line[0:6], lineidx))
                else:
                    warnings.append("The PDB file contains the following non-standard line which is allowed by the server:\n  line %d: %s" % (lineidx, line))
            lineidx = lineidx + 1
                    
        if classicErrors:
            errors.insert(0, "The PDB is incompatible with the classic version of Rosetta. Try using the mini version of Rosetta or else altering the PDB.<br>")
            errors.append("<br>The classic-specific errors are as follows:<ul style='text-align:left'>")
            errors.append("<li>%s" % string.join(classicErrors, "<li>"))
            errors.append("</ul>")
        
        if errors:
            return errors, None

        return True, warnings
        

if __name__ == "__main__":

    pdbobj = PDB(sys.argv[1])
    
    # print pdbobj.check_format()
    
    # print pdbobj.get_stats()
    d = float(sys.argv[2])
    
    all = []
    all.extend(pdbobj.neighbors3(d, 'A  26'))
    all.extend(pdbobj.neighbors3(d, 'A  44'))
    all.extend(pdbobj.neighbors3(d, 'A  48'))
    all.extend(pdbobj.neighbors3(d, 'A  64'))
    all.extend(pdbobj.neighbors3(d, 'A 157'))
    all.extend(pdbobj.neighbors3(d, 'A 163'))
    
    all.sort()
    new = []
    for x in all:
      if x not in new:
        new.append(x)
        print x

    
    print pdbobj.neighbors2(d, 'A  26')
    print pdbobj.neighbors2(d, 'A  44')
    print pdbobj.neighbors2(d, 'A  48')
    print pdbobj.neighbors2(d, 'A  64')
    print pdbobj.neighbors2(d, 'A 157')
    print pdbobj.neighbors2(d, 'A 163')
    # print pdbobj.aa_resid2type()
    
    # pdbobj.remove_hetatm()
    # #pdbobj.fix_chain_id()
    # 
    # pdbobj.fix_residue_numbering()
    # 
    # for line in pdbobj.atomlines():
    #     print line,
    # 
    # print pdbobj.chain_ids()
    
    #pdbobj.fix_chain_id()
    
    #import rosettaplusplus
    
    #rosetta = rosettaplusplus.RosettaPlusPlus(tempdir = "temp", auto_cleanup = False)
    
    #mutations = {}
    
    #for resid in pdbobj.aa_resids():
    #    mutations[resid] = "ALA"
    #    print resid

    #import chainsequence
    #seqs = chainsequence.ChainSequences()
    #chain_resnums = seqs.parse_atoms(pdbobj)
    #print chain_resnums

    #pdb_cb = rosetta.mutate(pdbobj, mutations)
    #for x in pdbobj.atomlines():
        #print x[21:26], x[26]
    
    #neighbors = pdbobj.neighbors(6.0, 225) #" CA ")
    
    #print neighbors
    #for key, value in neighbors.iteritems():
        #print key + ":", value
