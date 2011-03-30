class References:
    
    def __init__(self):
        self.refs = {
            "DavisEtAl:2006"        :   'Davis IW, Arendall III WB, Richardson DC, Richardson JS. <i>The Backrub Motion: How Protein Backbone Shrugs When a Sidechain Dances</i>.<br><a href="http://dx.doi.org/10.1016/j.str.2005.10.007" style="font-size: 10pt">Structure, Volume 14, Issue 2, 2<sup>nd</sup>  February 2006, Pages 265-274</a>',
            "SmithKortemme:2008"    :   'Smith CA, Kortemme T. <i>Backrub-Like Backbone Simulation Recapitulates Natural Protein Conformational Variability and Improves Mutant Side-Chain Prediction</i>.<br><a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 10pt"> Journal of Molecular Biology, Volume 380, Issue 4, 18<sup>th</sup> July 2008, Pages 742-756 </a>',
            "HumphrisKortemme:2008" :   'Humphris EL, Kortemme T. <i>Prediction of Protein-Protein Interface Sequence Diversity using Flexible Backbone Computational Protein Design</i>.<br><a href="http://dx.doi.org/10.1016/j.str.2008.09.012" style="font-size: 10pt"> Structure, Volume 16, Issue 12, 12<sup>th</sup> December 2008, Pages 1777-1788</a>',
            "FriedlandEtAl:2009"    :   'Friedland GD, Lakomek NA, Griesinger C, Meiler J, Kortemme T. <i>A Correspondence between Solution-State Dynamics of an Individual Protein and the Sequence and Conformational Diversity of its Family</i>.<br><a href="http://dx.doi.org/10.1371/journal.pcbi.1000393" style="font-size: 10pt"> PLoS Computational Biology, May 2009</a>',
            "LauckEtAl:2010"        :   'Lauck F, Smith CA, Friedland GD, Humphris EL, Kortemme T. <i>RosettaBackrub - A web server for flexible backbone protein structure modeling and design</i>.<br><a href="http://dx.doi.org/10.1093/nar/gkq369" style="font-size: 10pt">Nucleic Acids Research, Volume 38, Issue suppl. 2, Pages W569-W575</a>',
            "SmithKortemme:2010"    :   'Smith CA, Kortemme T. <i>Structure-Based Prediction of the Peptide Sequence Space Recognized by Natural and Synthetic PDZ Domains</i>.<br><a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 10pt">Journal of Molecular Biology, Volume 402, Issue 2, 17<sup>th</sup> September 2010, Pages 460-474</a>',
        }
    
    def __getitem__(self, index):
        return self.refs[index]
    
    def iteritems(self):
        return self.refs.iteritems()
    
    def getReferences(self):
        i = 0
        refIDs = {}
        refs = sorted(self.refs.iteritems())
        for reftag, reference in refs:
            i += 1
            refIDs[reftag] = i
        return refIDs

        # Add the default version of Rosetta to be used as the first element in the tuple of binaries
        protocolGroups = []
        refIDs = self.getReferences()

class RosettaProtocolGroup:
    def __init__(self, name, color):
        self.name = name
        self.protocols = []
        self.size = 0
        self.color = color
        self.description = ""
    
    def __getitem__(self, index):
        return self.protocols[index]

    def getProtocols(self):
        return self.protocols

    def setDescription(self, description):
        self.description = description

    def getDescription(self):
        return self.description

    def add(self, protocol):
        self.protocols.append(protocol)
        protocol.setGroup(self)
        self.size += 1
        
    def getSize(self):
        return self.size

    def getName(self):
        return self.name
        
# todo: I access some of these class members directly - use getters/setters for all
class RosettaProtocol:
    def __init__(self, name, dbname):
        self.name = name
        self.dbname = dbname
        self.group = None
        self.datadirfunction = None
        self.submitfunction = None
        self.binaries = None
        self.references = None
        self.nos = None
        self.StoreFunction = None
        self.resultsfunction = None
        
    def setStoreFunction(self, storefunction):
        self.StoreFunction = storefunction
        
    def setSubmitFunction(self, submitfunction):
        self.submitfunction = submitfunction
    
    def setShowResultsFunction(self, resultsfunction):
        self.resultsfunction = resultsfunction
    
    def getShowResultsFunction(self):
        return self.resultsfunction 
    
    def setBinaries(self, *binaries):
        self.binaries = binaries
            
    def setReferences(self, *references):
        self.references = references
        
    def getNumStructures(self):
        return self.nos
    
    def setNumStructures(self, minimum, recommended, maximum):
        self.nos = (minimum, recommended, maximum)
    
    def setGroup(self, group):
        self.group = group

    def setDataDirFunction(self, datadirfunction):
        self.datadirfunction = datadirfunction

    def getDataDirFunction(self):
        return self.datadirfunction
        
    def getName(self):
        return self.name

    def getSubmitfunction(self):
        return self.submitfunction

    def getReferences(self):
        return self.references
    

RosettaBinaries = {        
    "classic"   :{  # 2.3.0 was released 2008-04-21, this revision dates 2008-12-27
                    "mini"      : False,
                    "backrub" : "rosetta_20090109.gcc", 
                    "revision" : 26316, 
                    "name"   :   "Rosetta++ 2.32 (classic), as published",
                 },
    "mini"      :{  # Revision is clear here
                    "mini"      : True,
                    "backrub" : "backrub_r32532", 
                    "postprocessing" : "score_jd2_r32532", 
                    "revision" : 32532, 
                    "name" : "Rosetta 3.1 (mini)",
                 },
    "ensemble"  :{  # based solely on the date, roughly between revisions 22709 - 22736
                    "mini"      : False,
                    "backrub" : "ros_052208.gcc",
                    "revision" : 22736, 
                    "name" : "Rosetta++ 2.30 (classic), as published",
                 },
    "seqtolHK"  :{  # based solely on the date, roughly between revisions 24967 - 24980
                    "mini"      : False,
                    "backrub" : "rosetta_classic_elisabeth_backrub.gcc", 
                    "sequence_tolerance" : "rosetta_1Oct08.gcc",
                    "revision" : 24980, 
                    "name" : "Rosetta++ 2.30 (classic), as published",
                 },
    "seqtolJMB" :{  # based solely on the date, roughly between revisions 24967 - 24980
                    "mini"      : True,
                    "backrub" : "backrub_r39284", 
                    "sequence_tolerance" : "sequence_tolerance_r39284",
                    "revision" : 39284, 
                    "name" : "Rosetta 3.2 (mini), as published",
                 },
    "seqtolP1"  :{  # based solely on the date, roughly between revisions 24967 - 24980
                    "mini"      : True,
                    "backrub" : "backrub_r", 
                    "sequence_tolerance" : "sequence_tolerance_r",
                    "revision" : 0, 
                    "name" : "Rosetta 3.2 (mini), as published",
                 },
}
