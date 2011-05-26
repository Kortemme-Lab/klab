#!/usr/bin/python2.4
# encoding: utf-8
"""
Graph.py

Created by Shane O'Connor 2011.
Copyright (c) 2011 __UCSF__. All rights reserved.
"""

import sys
sys.path.insert(0, "../")
sys.path.insert(0, "../../common/")
import traceback
from string import join
from rosettahelper import readFile, writeFile
import ClusterTask  

#upgradetodo use this to pretty print the JSON import simplejson

JITSpaceTree = readFile("JITSpaceTree.js")
JITForceDirected = readFile("JITForceDirected.js")
JITHTML = readFile("JIThtml.html")

# todo: move all color constants into one file
green = "#00FF00"                
red = "#FF0000"
white = "#FFFFFF"
grassgreen = "#408080"
darkgrey = "#808080"
darkergrey = "#404040"
yellow = "#FFFF44"
black = "#000000"
    
class Node(object):
    schema = {
      #‘circle’, ‘rectangle’, ‘square’, ‘ellipse’, ‘triangle’, ‘star’
      ClusterTask.INITIAL_TASK: ("start", white, black, "circle"),
      ClusterTask.INACTIVE_TASK: ("inactive", grassgreen, white, "circle"),
      ClusterTask.QUEUED_TASK: ("queued", yellow, black, "circle"),
      ClusterTask.ACTIVE_TASK: ("active", green, black, "circle"),
      ClusterTask.RETIRED_TASK: ("retired", darkgrey, white, "triangle"),
      ClusterTask.COMPLETED_TASK: ("completed", darkergrey, white, "square"),
      ClusterTask.FAILED_TASK: ("failed", red, white, "star")
      }
    
    def __init__(self, id, name, shortname, status, tasksdone, totaltasks, profile, initial):
        self.id = id
        self.name = name
        self.shortname = shortname  
        scheme = self.schema[status]
        self.status = scheme[0]
        self.tasksdone = float(tasksdone)
        self.totaltasks = float(totaltasks)
        if totaltasks > 0: # sanity check
            if status == ClusterTask.ACTIVE_TASK and totaltasks > 1:
                self.progress = max(0.02, self.tasksdone/self.totaltasks)
            else:
                self.progress = None    
        self.color = scheme[1]
        self.textcolor = scheme[2]
        self.shape = scheme[3]
        self.profile = profile
        self.inclusiveTime = 0
        for _step in self.profile:
            self.inclusiveTime += _step[1]
        self.exclusiveTime = self.inclusiveTime
        if initial:
            self.shape = self.schema[ClusterTask.INITIAL_TASK][2]
                
class ExpectedException(Exception): pass  
    
class Graph(object):
    
    def __init__(self, tasks, testonly = False):
        self.vertices = {}
        self.edges = {}
        #initv = {"id" :0, "edges"[], "start", "initial", "#FFFFFF", "doublecircle", 1, 1, "start")
        self.vertices["init"] = Node(0, "start", "start", ClusterTask.INITIAL_TASK, 1, 1, [], True)
        self.edges["init"] = tasks
        self.numvertices = 1
        self._assimilate(tasks, testonly, initial = True) # Get exclusive time
        self.vertices["init"].exclusiveTime = max([self.vertices[t].exclusiveTime for t in tasks] or [0]) or 0     
        self._isATree = True
    
    def _getLegend(self):
        root = self.vertices["init"]
        html = ["<h4>Legend</h4><p>"] 
        for state in ClusterTask.status:
            scheme = root.schema[state]
            htmlcolor = scheme[1]
            statusname = scheme[0]
            html.append('''<font color='%s'>&#9632</font>&nbsp;%s<br>''' % (htmlcolor, statusname))
            #html.append('''<font color='%s'><li type=square></font>%s''' % (htmlcolor, statusname))
        html.append("</p>")
        return join(html, "\n")

    def isATree(self):
        self.tt = {}
        self._isATree = True
        try:
            self._treeTest(["init"])
        except ExpectedException, e:
            self._isATree = False
        self.tt = {}
        return self._isATree
        
    def _treeTest(self, tasks):
        for t in tasks:
            if not self.tt.get(t):
                self.tt[t] = True
                es = self.edges.get(t)
                if es:
                    self._treeTest(es)    
            else:
                print("failed on %s" % t)
                raise ExpectedException()
        
    def _assimilate(self, tasks, testonly, initial = False):
        for t in tasks:
            if not self.vertices.get(t):
                # Add vertex
                # (0=id, 1=Name, 2=shortname, 3=state name, 4=state color, 5=state shape in graph, 6=profile, 7=tasks completed, 8=total number of tasks)
                #todo: self.vertices[t] = (self.numvertices, status[0], status[1], scheme[0], scheme[1], scheme[2], status[3], status[4], status[5])
                #getstatus (self.name, self.shortname, st, profile, tasksCompleted, numtasks)
                testing = True
                
                if testonly:
                    t.state = random.randint(ClusterTask.INITIAL_TASK, ClusterTask.FAILED_TASK)
                    state = t.state
                    if state == ClusterTask.ACTIVE_TASK:
                        totaljobs = random.randint(1, 10)
                        donejobs = random.randint(0, totaljobs)    
                    else:
                        totaljobs = 1
                        donejobs = random.randint(0, totaljobs)
                    profile = t.getprofile(warn = False)
                    # create a fake profile
                    profile[0] = (profile[0][0], profile[0][1] * 10000)
                    profile.append(('Run', random.random() * 30))

                    status = (t.name, t.shortname, state, profile, donejobs, totaljobs)
                else:
                    status = t.getStatus()
                    
                clongname = status[0]
                cshortname = status[1]
                cstatus = status[2]
                cprofile = status[3]
                cdonetasks = status[4]
                ctotaltasks = status[5]
                
                
                self.vertices[t] = Node(self.numvertices, clongname, cshortname, cstatus, cdonetasks, ctotaltasks, cprofile, initial)
                self.numvertices +=1
                
                #vertices: ClusterTask -> Node
                #edges: ClusterTask -> [ClusterTask]
                
                # Add edges
                dependents = t.getDependents()
                self.edges[t] = dependents
                
                # Recurse
                self._assimilate(dependents, testonly)
                
                # Get exclusive time
                dependentTime = 0
                for dependent in self.edges[t]:
                    dependentTime = max([self.vertices[dependent].exclusiveTime for dependent in self.edges[t]] or [0]) or 0
                self.vertices[t].exclusiveTime += dependentTime
                 
            else:
                self.isATree = False
                
    def output(self):
        vs = self.vertices
        es = self.edges
        str = []
        str.append("vertices")
        for v, n in sorted(vs.iteritems()):
            str.append("v%d : %s, %s, %d, %d, %s, %s" % (n.id, n.shortname, n.status, n.tasksdone, n.totaltasks, n.color, n.shape))
                
        str.append("edges")
        for v, adjacents in sorted(es.iteritems()):
            for v2 in adjacents:
                str.append("v%d -> v%d" % (vs[v].id, vs[v2].id))    
        return join(str, "\n")

class JITGraph(Graph):

    def __init__(self, tasks, testonly = False):
        super(JITGraph, self).__init__(tasks, testonly)
    
    def getForceDirected(self):
        vs = self.vertices
        es = self.edges
        str = []
        for v, n in sorted(vs.iteritems()):
            nodestr = []
            nodestr.append('''\t{
\t\t"id" : "%s%d",
\t\t"name" : "%s",
\t\t"data" : {
\t\t\t"$color": "%s",  
\t\t\t"$type": "%s",  
\t\t\t"$dim": 10  
\t\t}'''        % (n.shortname, n.id, n.shortname, n.color, n.shape))
            #print("%s%d: %s" % (n.shortname, n.id, n.shape))
            #v%d : %s, %s, %d, %d, %s, %s" % (n.id, n.shortname, n.status, n.tasksdone, n.totaltasks, n.color, n.shape))
            es = self.edges.get(v)
            if es:
                adj = []
                for v2 in sorted(es):
                    adj.append('''\t\t\t{  
\t\t\t\t"nodeFrom": "%s%d",  
\t\t\t\t"nodeTo": "%s%d",  
\t\t\t\t"data": {  
\t\t\t\t\t"$color": "#557EAA",  
\t\t\t\t\t"$type": "arrow"  
\t\t\t\t}  
\t\t\t}'''              % (vs[v].shortname, vs[v].id, vs[v2].shortname, vs[v2].id))
                nodestr.append(''',\n\t\t"adjacencies": [
%s
\t\t]'''            % join(adj, ",\n"))
            nodestr.append('''\n\t}''')
            str.append(join(nodestr,""))
        
        JITdata = "var json = [\n%s\n];" % join(str, ",\n")
        return JITForceDirected % JITdata

    def _getSpaceTreeNode(self, parent, indent):
        vs = self.vertices
        es = self.edges
        indent2 = "%s  " % indent
        indent3 = "%s    " % indent
        n = vs[parent]
        
        pstr = ""
        if n.progress:
            pstr = "\n%s$progress: %f," % (indent3, n.progress)
        pexct = ""
        if n.exclusiveTime != n.inclusiveTime:
            pexct = "\n%s$exclusive: %f," % (indent3, n.exclusiveTime)
        #else:
        #    pexct = "\n%s$exclusive: %f," % (indent3, n.exclusiveTime)
        profstr = "[%s]" % (join(["['%s', %f]" % (timer[0], timer[1]) for timer in n.profile], ","))
        nodestr = []
        nodestr.append('''%s{
%sid : "%s%d",
%sname : "%s",
%sdata: {%s%s 
%s$profile : %s,  
%s$inclusive : %f,  
%s$color: '%s',
%s$textcolor: '%s'
%s}'''        % (indent, indent2, n.shortname, n.id, indent2, n.shortname, indent2, pstr, pexct, indent3, profstr, indent3, n.inclusiveTime, indent3, n.color, indent3, n.textcolor, indent2))
        

              #print("%s%d: %s" % (n.shortname, n.id, n.shape))
        #v%d : %s, %s, %d, %d, %s, %s" % (n.id, n.shortname, n.status, n.tasksdone, n.totaltasks, n.color, n.shape))
        es = self.edges.get(parent)
        if es:
            childstr = []
            for child in sorted(es):
                childstr.append(self._getSpaceTreeNode(child, indent3))
            nodestr.append(''',\n%schildren: [
%s
%s]'''            % (indent2, join(childstr, ",\n" ), indent2))
        nodestr.append('''\n%s}''' % indent)
        return join(nodestr, "")
        
    def getSpaceTree(self):
        if not self.isATree():
            #upgradetodo: we need to embed the html here as well
            return self.getForceDirected()
        JITdata = "var json = %s;" % self._getSpaceTreeNode("init", "  ")
        return JITSpaceTree % JITdata
    
    def getHTML(self):
        return JITHTML % self._getLegend()
    
        
if __name__ == "__main__":
    #initv = (0, "start", "initial", "#FFFFFF", "doublecircle", 1, 1, "start")
    #self.vertices[t] = (self.numvertices, cshortname, cstatus, ccolor, cshape, cdonetasks, ctotaltasks, clongname)
    import os
    import ClusterScheduler
    import RosettaTasks
    from rosettahelper import *
    import pprint
    import random
    
    inputDirectory = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/test/"

    mini = "multiseqtol"
    ID = 1234
    pdb_filename = "1ki1.pdb"
    output_handle = open(os.path.join(inputDirectory, pdb_filename),'r')
    pdb_info = output_handle.read()
    output_handle.close()
    nstruct = 100
    allAAsExceptCysteine = ROSETTAWEB_SK_AAinv.keys()
    allAAsExceptCysteine.sort()
    allAAsExceptCysteine.remove('C')
    sgec = None
    netappRoot = None
    cluster_dltest = None
    #allAAsExceptCysteine = ['A', 'D']
    params = {
        "cryptID"           : "cryptic",
        "binary"            : mini,
        "ID"                : ID,
        "pdb_filename"      : pdb_filename,
        "pdb_info"          : pdb_info,
        "nstruct"           : nstruct,
        "radius"            : 10,
        "kT"                : 0.228 + 0.021,
        "Partners"          : ["A", "B"],
        "Weights"           : [0.4, 0.4, 0.4, 1.0],
        "Premutated"        : {"A" : {56 : allAAsExceptCysteine}},
        "Designed"          : {"B" : [1369, 1373, 1376, 1380]}
        }
    clusterjob = RosettaTasks.SequenceToleranceMultiJobSK(sgec, params, netappRoot, cluster_dltest, testonly = True)
    
    ts = clusterjob.scheduler._getAllTasks()       
        
    # Create a graph
    g = JITGraph(clusterjob.scheduler._initialtasks, testonly = True)
        
    if g.isATree():
        writeFile("/var/www/html/rosettaweb/backrub/images/JIT/Examples/Spacetree/example1.js", g.getSpaceTree())
    else:
        writeFile("/var/www/html/rosettaweb/backrub/images/JIT/Examples/ForceDirected/example1.js", g.getForceDirected())
    
    writeFile("/var/www/html/rosettaweb/backrub/images/JIT/Examples/Spacetree/example1.html", g.getHTML())
