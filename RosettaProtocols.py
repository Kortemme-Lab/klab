class References:
    
    def __init__(self):
        self.refs = {
            "DavisEtAl:2006"        :   'Davis IW, Arendall III WB, Richardson DC, Richardson JS. <i>The Backrub Motion: How Protein Backbone Shrugs When a Sidechain Dances</i>.<br><a href="http://dx.doi.org/10.1016/j.str.2005.10.007" style="font-size: 10pt">Structure, Volume 14, Issue 2, 2<sup>nd</sup>  February 2006, Pages 265-274</a>',
            "SmithKortemme:2008"    :   'Smith CA, Kortemme T. <i>Backrub-Like Backbone Simulation Recapitulates Natural Protein Conformational Variability and Improves Mutant Side-Chain Prediction</i>.<br><a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 10pt"> Journal of Molecular Biology, Volume 380, Issue 4, 18<sup>th</sup> July 2008, Pages 742-756 </a>',
            "HumphrisKortemme:2008" :   'Humphris EL, Kortemme T. <i>Prediction of Protein-Protein Interface Sequence Diversity using Flexible Backbone Computational Protein Design</i>.<br><a href="http://dx.doi.org/10.1016/j.str.2008.09.012" style="font-size: 10pt"> Structure, Volume 16, Issue 12, 12<sup>th</sup> December 2008, Pages 1777-1788</a>',
            "FriedlandEtAl:2009"    :   'Friedland GD, Lakomek NA, Griesinger C, Meiler J, Kortemme T. <i>A Correspondence between Solution-State Dynamics of an Individual Protein and the Sequence and Conformational Diversity of its Family</i>.<br><a href="http://dx.doi.org/10.1371/journal.pcbi.1000393" style="font-size: 10pt"> PLoS Computational Biology, May 2009</a>',
            "LauckEtAl:2010"        :   'Lauck F, Smith CA, Friedland GD, Humphris EL, Kortemme T. <i>RosettaBackrub - A web server for flexible backbone protein structure modeling and design</i>.<br><a href="http://dx.doi.org/10.1093/nar/gkq369" style="font-size: 10pt">Nucleic Acids Research, Volume 38, Issue suppl. 2, Pages W569-W575</a>',
            "SmithKortemme:2010"    :   'Smith CA, Kortemme T. <i>Structure-Based Prediction of the Peptide Sequence Space Recognized by Natural and Synthetic PDZ Domains</i>.<br><a href="http://dx.doi.org/10.1016/j.jmb.2010.07.032" style="font-size: 10pt">Journal of Molecular Biology, Volume 402, Issue 2, 17<sup>th</sup> September 2010, Pages 460-474</a>',
            "SmithKortemme:2011"    :   'Smith CA, Kortemme T. <i>Predicting the Tolerated Sequences for Proteins and Protein Interfaces Using Rosetta Backrub Flexible Backbone Design</i>.<br><a href="http://dx.doi.org/10.1371/journal.pone.0020451" style="font-size: 10pt">PLoS ONE 6(7): e20451. doi:10.1371/journal.pone.0020451</a>',
        }
        
        # todo: This was hacked in. Really the refs table above should be separated out to look as below using tuples
        self.refsDOIs = {
            "DavisEtAl:2006"        :   ('Davis et al.', 'http://dx.doi.org/10.1016/j.str.2005.10.007'),
            "SmithKortemme:2008"    :   ('Smith and Kortemme, 2008', 'http://dx.doi.org/10.1016/j.jmb.2008.05.023'),
            "HumphrisKortemme:2008" :   ('Humphris and Kortemme, 2008', 'http://dx.doi.org/10.1016/j.str.2008.09.012'),
            "FriedlandEtAl:2009"    :   ('Friedland et al., 2008', 'http://dx.doi.org/10.1371/journal.pcbi.1000393'),
            "LauckEtAl:2010"        :   ('Lauck et al., 2010', 'http://dx.doi.org/10.1093/nar/gkq369'),
            "SmithKortemme:2010"    :   ('Smith and Kortemme, 2010', 'http://dx.doi.org/10.1016/j.jmb.2010.07.032'),
            "SmithKortemme:2011"    :   ('Smith and Kortemme, 2011', 'http://dx.doi.org/10.1371/journal.pone.0020451'),
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
    def __init__(self, name, color, public = True):
        self.name = name
        self.protocols = []
        self.size = 0
        self.color = color
        self.public = public
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
        
# todo: At some stage, tidy up all member access with use getters/setters
# todo: Split this over be/fe like the WebserverProtocols class
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
        self.startFunction = None
        self.checkFunction = None
        self.endFunction = None
        self.description = None
        self.progressDisplayHeight = None
        
    # Setters and getters
    def setBackendFunctions(self, startFunction, checkFunction, endFunction):
        self.startFunction = startFunction
        self.checkFunction = checkFunction
        self.endFunction = endFunction
    
    def getDescription(self):
        return self.description

    def setDescription(self, desc):
        self.description = desc
        
    def setStoreFunction(self, storefunction):
        self.StoreFunction = storefunction
    #    
    def setSubmitFunction(self, submitfunction):
        self.submitfunction = submitfunction
    
    def getSubmitfunction(self):
        return self.submitfunction
    #
    def setShowResultsFunction(self, resultsfunction):
        self.resultsfunction = resultsfunction
    
    def getShowResultsFunction(self):
        return self.resultsfunction 
    #
    def setBinaries(self, *binaries):
        self.binaries = binaries
    #        
    def setReferences(self, *references):
        self.references = references
    #    
    def setNumStructures(self, minimum, recommended, maximum):
        self.nos = (minimum, recommended, maximum)
    
    def getNumStructures(self):
        return self.nos
    #    
    def setGroup(self, group):
        self.group = group
    #
    def setDataDirFunction(self, datadirfunction):
        self.datadirfunction = datadirfunction

    def getDataDirFunction(self):
        return self.datadirfunction
    #    
    def getName(self):
        return self.name
    #
    def getReferences(self):
        return self.references
    # Utility functions
    def canUseMini(self):
        miniAvailable = False
        for binary in self.binaries:
            miniAvailable = miniAvailable or RosettaBinaries[binary]["mini"]
        return miniAvailable

    
# All cluster binaries should have the same name format based on the clusterrev field in RosettaBinaries: 
#    i) they are stored in the subdirectory of home named <clusterrev>
#   ii) they are named <somename>_<clusterrev>_static
# Furthermore, the related database should be in a subdirectory of the bindir named "rosetta_database"
# The "static" in the name is a reminder that these binaries must be built statically.

#todo: Ask Greg and Elisabeth for exact revisions

RosettaBinaries = {        
    # Webserver jobs
    "classic"   :{  # 2.3.0 was released 2008-04-21, this revision dates 2008-12-27
                    "name"      : "Rosetta++, as published", # 2.32
                    "queuename" : "Rosetta++",
                    "revision"  : 26316, 
                    "mini"      : False,
                    "runOnCluster"      : False,
                    "backrub"   : "rosetta_20090109.gcc", 
                    "database"  : "rosetta_database"
                 },
    "mini"      :{  # Revision is clear here
                    "name"          : "Rosetta 3.1",
                    "queuename"     : "Rosetta 3.1",
                    "revision"      : 32532, 
                    "mini"          : True,
                    "runOnCluster"      : False,
                    "backrub"       : "backrub_r32532_static_patched_34477",
                    "postprocessing": "score_jd2_r32532", 
                    "database"      : "minirosetta_database"
                 },
    "ensemble"  :{  # based solely on the date, roughly between revisions 22709 - 22736
                    "name"      : "Rosetta++, as published", #  2.30
                    "queuename" : "Rosetta++",
                    "revision"  : 22736, 
                    "mini"      : False,
                    "runOnCluster"      : False,
                    "backrub"   : "ros_052208.gcc",
                 },
    # Cluster jobs Rosetta++ 2.30
    "seqtolHK"  :{  "name"              : "Rosetta++, as published",
                    "queuename"         : "Rosetta++",
                    "revision"          : 17289,  # based on the sequence tolerance database revision
                    "mini"              : False,
                    "runOnCluster"      : True,
                    "clusterrev"        : "rElisabeth",
                    "cluster_databases" : ["rosetta_database_r15286", "rosetta_database_r17289"],
                 },
    "seqtolJMB" :{  # This is the revision used in the paper. 
                    # Note: The backrub binary used is the backrub_pilot application, not the backrub application.
                    "name"      : "JMB 2010 (PDZ-optimized)",
                    "queuename" : "JMB 2010",
                    "revision"  : 33982,
                    "mini"      : True,
                    "runOnCluster" : True,
                    "clusterrev": "r33982"
                 },
    "seqtolP1"  :{  # This is the revision used in the paper. 
                    "name"      : "PLoS ONE 2011 (generalized)",
                    "queuename" : "PLoS ONE 2011",
                    "revision"  : 39284, 
                    "mini"      : True,
                    "runOnCluster" : True,
                    "clusterrev": "r39284"
                 },
    "multiseqtol" :{  
                    "name"      : "Rosetta 3.2",
                    "queuename" : "Rosetta 3.2",
                    "revision"  : 39284,
                    "mini"      : True,
                    "runOnCluster" : True,
                    "clusterrev": "r39284"
                 },
}

# This class and its child classes set up all the protocol data.
# The idea is to reduce redundancy in data descriptions, avoid updating errors, and make it easier to add new protocols.         
class WebserverProtocols(object):
    
    protocols = None
    protocolGroups = None
    
    def __init__(self):
        protocols = []
        protocolGroups = []
        
        protocolGroups.append(RosettaProtocolGroup("Point Mutation", "#DCE9F4"))
                
        proto = RosettaProtocol("One Mutation", "point_mutation")
        proto.setBinaries("mini", "classic")
        proto.setNumStructures(2,10,50)
        protocolGroups[0].add(proto)
    
        proto = RosettaProtocol("Multiple Mutations", "multiple_mutation")
        proto.setBinaries("mini", "classic")
        proto.setNumStructures(2,10,50)
        protocolGroups[0].add(proto)
        
        protocolGroups.append(RosettaProtocolGroup("Backrub Ensemble", "#B7FFE0"))
        
        proto = RosettaProtocol("Backrub Ensemble", "no_mutation")
        proto.setBinaries("classic", "mini")
        proto.setNumStructures(2,10,50)
        protocolGroups[1].add(proto)
        
        proto = RosettaProtocol("Backrub Ensemble Design", "ensemble")
        proto.setBinaries("ensemble")
        proto.setNumStructures(2,10,50)
        protocolGroups[1].add(proto)
        
        protocolGroups.append(RosettaProtocolGroup("Sequence Tolerance", "#FFE2E2"))
                
        proto = RosettaProtocol("Interface Sequence Tolerance", "sequence_tolerance")
        proto.setBinaries("seqtolHK")
        proto.setNumStructures(2,10,50)
        protocolGroups[2].add(proto)
        
        proto = RosettaProtocol("Generalized Protocol<br>(Fold / Interface)<br>Sequence Tolerance", "sequence_tolerance_SK")
        proto.setBinaries("seqtolJMB", "seqtolP1") 
        proto.setNumStructures(20,50,150)
        protocolGroups[2].add(proto)
        
        # Private protocols for the lab go here
        protocolGroups.append(RosettaProtocolGroup("Private Protocols", "#ffe2ba", public = False))
                
        proto = RosettaProtocol("Multiple Sequence Tolerance", "multi_sequence_tolerance")
        proto.setBinaries("multiseqtol")
        proto.setNumStructures(2,20,100)
        protocolGroups[3].add(proto)        

        # A flat list of the protocols 
        protocols = []
        
        for i in range(len(protocolGroups)):
            protocols.extend(protocolGroups[i].getProtocols())
                
        self.protocolGroups = protocolGroups
        self.protocols = protocols
        
    def getProtocols(self):
        return self.protocolGroups, self.protocols
    
    def getProtocolDBNames(self):
        dbnames = []
        for p in self.protocols:
            dbnames.append(p.dbname)
        return dbnames
            



       
