#!/usr/bin/python2.4

import re
import types
import UserDict
import spatialhash

residues = ["ALA", "CYS", "ASP", "ASH", "GLU", "GLH", "PHE", "GLY", "HIS", 
            "HIE", "HIP", "ILE", "LYS", "LYN", "LEU", "MET", "ASN", "PRO", 
            "GLN", "ARG", "ARN", "SER", "THR", "VAL", "TRP", "TYR"]

class ChainSequences(UserDict.DictMixin):
  """A class for holding PDB chain sequences"""
  
  def __init__(self):
    self.seqs = {}
    self.chains = []
  
  def __getitem__(self, key):
    if type(key) == types.IntType:
      return self.seqs[self.chains[key]]
    else:
      return self.seqs[key]
  
  def __setitem__(self, key, value):
    if type(key) == types.IntType:
      self.seqs[self.chains[key]] = value
    else:
      self.seqs[key] = value
      if key not in self.chains:
        self.chains += [key]
  
  def __delitem__(self, key):
    if type(key) == types.IntType:
      del self.seqs[self.chains[key]]
      del self.chains[key]
    else:
      del self.seqs[key]
      self.chains.remove(key)
    
  def keys(self):
    return self.chains
  
  def parse_seqres(self, pdb):
    """Parse the SEQRES entries into the object"""
    
    seqresre = re.compile("SEQRES")
    
    seqreslines = [line for line in pdb.lines if seqresre.match(line)]
    
    for line in seqreslines:
      chain = line[11]
      resnames = line[19:70].strip()
      self.setdefault(chain, [])
      self[chain] += resnames.split()

  def parse_atoms(self, pdb):
    """Parse the ATOM entries into the object"""
    
    atomre = re.compile("ATOM")
    
    atomlines = [line for line in pdb.lines if atomre.match(line)]
    
    chainresnums = {}
    
    for line in atomlines:
      chain = line[21]
      resname = line[17:20]
      resnum = line[22:27]
      #print resnum
      chainresnums.setdefault(chain, [])
      
      if resnum in chainresnums[chain]:
        assert self[chain][chainresnums[chain].index(resnum)] == resname
      else:
        if resnum[-1] == ' ':
          self.setdefault(chain, [])
          self[chain] += [resname]
          chainresnums[chain] += [resnum]
    
    return chainresnums

  def seqres_lines(self):
    """Generate SEQRES lines representing the contents"""
  
    lines = []
  
    for chain in self.keys():
      seq = self[chain]
      serNum = 1
      startidx = 0
      while startidx < len(seq):
        endidx = min(startidx+13, len(seq))
        lines += ["SEQRES  %2i %s %4i  %s\n" % (serNum, chain, len(seq), " ".join(seq[startidx:endidx]))]
        serNum += 1
        startidx += 13
    
    return lines
  
  def replace_seqres(self, pdb, update_atoms = True):
    """Replace SEQRES lines with a new sequence, optionally removing 
    mutated sidechains"""
  
    newpdb = PDB()
    inserted_seqres = False
    entries_before_seqres = set(["HEADER", "OBSLTE", "TITLE",  "CAVEAT", "COMPND", "SOURCE", 
                                 "KEYWDS", "EXPDTA", "AUTHOR", "REVDAT", "SPRSDE", "JRNL", 
                                 "REMARK", "DBREF",  "SEQADV"])
  
    mutated_resids = {}
    
    if update_atoms:
      old_seqs = ChainSequences()
      chainresnums = old_seqs.parse_atoms(pdb)
    
      assert self.keys() == old_seqs.keys()
      
      for chain in self.keys():
        assert len(self[chain]) == len(old_seqs[chain])
        for i in xrange(len(self[chain])):
          if self[chain][i] != old_seqs[chain][i]:
            resid = chain + chainresnums[chain][i]
            mutated_resids[resid] = self[chain][i]
    
    for line in pdb.lines:
    
      entry = line[0:6]
      if (not inserted_seqres) and entry not in entries_before_seqres:
        inserted_seqres = True
        newpdb.lines += self.seqres_lines()
      
      if update_atoms and entry == "ATOM  ":
        resid = line[21:27]
        atom = line[12:16].strip()
        if not mutated_resids.has_key(resid):
          newpdb.lines += [line]
        else:
          newpdb.lines += [line[:17] + mutated_resids[resid] + line[20:]]
      elif entry != "SEQRES":
        newpdb.lines += [line]
    
    if update_atoms:
      newpdb.remove_nonbackbone_atoms(mutated_resids.keys())
    
    return newpdb