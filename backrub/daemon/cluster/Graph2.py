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
from rosettahelper import writeFile
import ClusterTask  

#upgradetodo use this to pretty print the JSON import simplejson

JITSpaceTree = '''
var labelType, useGradients, nativeTextSupport, animate;

(function() {
  var ua = navigator.userAgent,
      iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
      typeOfCanvas = typeof HTMLCanvasElement,
      nativeCanvasSupport = (typeOfCanvas == 'object' || typeOfCanvas == 'function'),
      textSupport = nativeCanvasSupport 
        && (typeof document.createElement('canvas').getContext('2d').fillText == 'function');
  //I'm setting this based on the fact that ExCanvas provides text support for IE
  //and that as of today iPhone/iPad current text support is lame
  labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
  nativeTextSupport = labelType == 'Native';
  useGradients = nativeCanvasSupport;
  animate = !(iStuff || !nativeCanvasSupport);
})();

var Log = {
  elem: false,
  write: function(text){
    if (!this.elem) 
      this.elem = document.getElementById('log');
    this.elem.innerHTML = text;
    this.elem.style.left = (500 - this.elem.offsetWidth / 2) + 'px';
  }
};


function init(){
    //init data
    %s
    //end
    //init Node Types
    //Create a node rendering function that plots a fill
    //rectangle and a stroke rectangle for borders
    $jit.ST.Plot.NodeTypes.implement({
      'stroke-rect': {
        'render': function(node, canvas) {
          var width = node.getData('width'),
              height = node.getData('height'),
              pos = this.getAlignedPos(node.pos.getc(true), width, height),
              posX = pos.x + width/2,
              posY = pos.y + height/2;
          this.nodeHelper.rectangle.render('fill', {x: posX, y: posY}, width, height, canvas);
          this.nodeHelper.rectangle.render('stroke', {x: posX, y: posY}, width, height, canvas);
        }
      }
    });
    //end
    //init Spacetree
    //Create a new ST instance
    var st = new $jit.ST({
        //id of viz container element
        injectInto: 'infovis',
        //set duration for the animation
        duration: 800,
        //set animation transition type
        transition: $jit.Trans.Quart.easeInOut,
        //set distance between node and its children
        levelDistance: 50,
        //enable panning
        Navigation: {
          enable:true,
          panning:true
        },
        //set node and edge styles
        //set overridable=true for styling individual
        //nodes or edges
        Node: {
            height: 20,
            width: 60,
            type: 'rectangle',
            CanvasStyles: {
              fillStyle: '#daa',
              strokeStyle: '#ffc',
              lineWidth: 2
            },
            overridable: true
        },
        
        Edge: {
            type: 'bezier',
            overridable: true
        },
        
        onBeforeCompute: function(node){
            Log.write("loading " + node.name);
        },
        
        onAfterCompute: function(){
            Log.write("done");
        },
        
        //This method is called on DOM label creation.
        //Use this method to add event handlers and styles to
        //your node.
        onCreateLabel: function(label, node){
            label.id = node.id;            
            label.innerHTML = node.name;
            label.onclick = function(){
                if(normal.checked) {
                  st.onClick(node.id);
                } else {
                st.setRoot(node.id, 'animate');
                }
            };
            //set label styles
            var style = label.style;
            style.width = 60 + 'px';
            style.height = 17 + 'px';            
            style.cursor = 'pointer';
            style.color = '#333';
            style.fontSize = '0.8em';
            style.textAlign= 'center';
            style.paddingTop = '3px';
        },
        
        //This method is called right before plotting
        //a node. It's useful for changing an individual node
        //style properties before plotting it.
        //The data properties prefixed with a dollar
        //sign will override the global node style properties.
        onBeforePlotNode: function(node){
            //add some color to the nodes in the path between the
            //root node and the selected node.
            if (node.selected) {
                node.data.$color = "#ff7";
                //node.setCanvasStyle('fillStyle', '#0f0');
                //node.data.$height = 30;
                //node.data.$width = 70;
                node.data.$lineWidth = 5;
            }
            else {
                //node.data.$height = 20;
                //node.data.$width = 60;
            }
        },
        
        //This method is called right before plotting
        //an edge. It's useful for changing an individual edge
        //style properties before plotting it.
        //Edge data proprties prefixed with a dollar sign will
        //override the Edge global style properties.
        onBeforePlotLine: function(adj){
            if (adj.nodeFrom.selected && adj.nodeTo.selected) {
                adj.data.$color = "#eed";
                adj.data.$lineWidth = 3;
            }
            else {
                delete adj.data.$color;
                delete adj.data.$lineWidth;
            }
        }
    });
    //load json data
    st.loadJSON(json);
    //compute node positions and layout
    st.compute();
    //optional: make a translation of the tree
    st.geom.translate(new $jit.Complex(-200, 0), "current");
    //emulate a click on the root node.
    st.onClick(st.root);
    //end
    //Add event handlers to switch spacetree orientation.
    var top = $jit.id('r-top'), 
        left = $jit.id('r-left'), 
        bottom = $jit.id('r-bottom'), 
        right = $jit.id('r-right'),
        normal = $jit.id('s-normal');
        
    
    function changeHandler() {
        if(this.checked) {
            top.disabled = bottom.disabled = right.disabled = left.disabled = true;
            st.switchPosition(this.value, "animate", {
                onComplete: function(){
                    top.disabled = bottom.disabled = right.disabled = left.disabled = false;
                }
            });
        }
    };
    
    top.onchange = left.onchange = bottom.onchange = right.onchange = changeHandler;
    //end

}'''

JITForceDirected = '''
var labelType, useGradients, nativeTextSupport, animate;

(function() {
  var ua = navigator.userAgent,
      iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
      typeOfCanvas = typeof HTMLCanvasElement,
      nativeCanvasSupport = (typeOfCanvas == 'object' || typeOfCanvas == 'function'),
      textSupport = nativeCanvasSupport 
        && (typeof document.createElement('canvas').getContext('2d').fillText == 'function');
  //I'm setting this based on the fact that ExCanvas provides text support for IE
  //and that as of today iPhone/iPad current text support is lame
  labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
  nativeTextSupport = labelType == 'Native';
  useGradients = nativeCanvasSupport;
  animate = !(iStuff || !nativeCanvasSupport);
})();

var Log = {
  elem: false,
  write: function(text){
    if (!this.elem) 
      this.elem = document.getElementById('log');
    this.elem.innerHTML = text;
    this.elem.style.left = (500 - this.elem.offsetWidth / 2) + 'px';
  }
};


function init(){
  // init data
  %s

  // end
  // init ForceDirected
  var fd = new $jit.ForceDirected({
    //id of the visualization container
    injectInto: 'infovis',
    //Enable zooming and panning
    //by scrolling and DnD
    Navigation: {
      enable: true,
      //Enable panning events only if we're dragging the empty
      //canvas (and not a node).
      panning: 'avoid nodes',
      zooming: 10 //zoom speed. higher is more sensible
    },
    // Change node and edge styles such as
    // color and width.
    // These properties are also set per node
    // with dollar prefixed data-properties in the
    // JSON structure.
    Node: {
      overridable: true
    },
    Edge: {
      overridable: true,
      color: '#23A4FF',
      lineWidth: 0.4
    },
    //Native canvas text styling
    Label: {
      type: labelType, //Native or HTML
      size: 10,
      style: 'bold'
    },
    //Add Tips
    Tips: {
      enable: true,
      onShow: function(tip, node) {
        //count connections
        var count = 0;
        node.eachAdjacency(function() { count++; });
        //display node info in tooltip
        tip.innerHTML = "<div class=\\"tip-title\\">" + node.name + "</div>"
          + "<div class=\\"tip-text\\"><b>connections:</b> " + count + "</div>";
      }
    },
    // Add node events
    Events: {
      enable: true,
      //Change cursor style when hovering a node
      onMouseEnter: function() {
        fd.canvas.getElement().style.cursor = 'move';
      },
      onMouseLeave: function() {
        fd.canvas.getElement().style.cursor = '';
      },
      //Update node positions when dragged
      onDragMove: function(node, eventInfo, e) {
          var pos = eventInfo.getPos();
          node.pos.setc(pos.x, pos.y);
          fd.plot();
      },
      //Implement the same handler for touchscreens
      onTouchMove: function(node, eventInfo, e) {
        $jit.util.event.stop(e); //stop default touchmove event
        this.onDragMove(node, eventInfo, e);
      },
      //Add also a click handler to nodes
      onClick: function(node) {
        if(!node) return;
        // Build the right column relations list.
        // This is done by traversing the clicked node connections.
        var html = "<h4>" + node.name + "</h4><b> connections:</b><ul><li>",
            list = [];
        node.eachAdjacency(function(adj){
          list.push(adj.nodeTo.name);
        });
        //append connections information
        $jit.id('inner-details').innerHTML = html + list.join("</li><li>") + "</li></ul>";
      }
    },
    //Number of iterations for the FD algorithm
    iterations: 200,
    //Edge length
    levelDistance: 130,
    // Add text to the labels. This method is only triggered
    // on label creation and only for DOM labels (not native canvas ones).
    onCreateLabel: function(domElement, node){
      domElement.innerHTML = node.name;
      var style = domElement.style;
      style.fontSize = "0.8em";
      style.color = "#ddd";
    },
    // Change node styles when DOM labels are placed
    // or moved.
    onPlaceLabel: function(domElement, node){
      var style = domElement.style;
      var left = parseInt(style.left);
      var top = parseInt(style.top);
      var w = domElement.offsetWidth;
      style.left = (left - w / 2) + 'px';
      style.top = (top + 10) + 'px';
      style.display = '';
    }
  });
  // load JSON data.
  fd.loadJSON(json);
  // compute positions incrementally and animate.
  fd.computeIncremental({
    iter: 40,
    property: 'end',
    onStep: function(perc){
      Log.write(perc + '%% loaded...');
    },
    onComplete: function(){
      Log.write('done');
      fd.animate({
        modes: ['linear'],
        transition: $jit.Trans.Elastic.easeOut,
        duration: 2500
      });
    }
  });
  // end
}'''

# todo: move all color constants into one file
green = "#00FF00"                
red = "#FF0000"
white = "#FFFFFF"
grassgreen = "#408080"
darkgrey = "#808080"
darkergrey = "#404040"
yellow = "#FFFF44"

class Node(object):
    schema = {
      #‘circle’, ‘rectangle’, ‘square’, ‘ellipse’, ‘triangle’, ‘star’
      ClusterTask.INITIAL_TASK: ("inactive", white, "circle"),
      ClusterTask.INACTIVE_TASK: ("inactive", grassgreen, "circle"),
      ClusterTask.QUEUED_TASK: ("queued", yellow, "circle"),
      ClusterTask.ACTIVE_TASK: ("active", green, "circle"),
      ClusterTask.RETIRED_TASK: ("retired", darkgrey, "triangle"),
      ClusterTask.COMPLETED_TASK: ("completed", darkergrey, "square"),
      ClusterTask.FAILED_TASK: ("failed", red, "star")
      }

    def __init__(self, id, name, shortname, status, tasksdone, totaltasks, initial):
        self.id = id
        self.name = name
        self.shortname = shortname  
        scheme = self.schema[status]
        self.status = scheme[0]
        self.tasksdone = float(tasksdone)
        self.totaltasks = float(totaltasks)
        if status == ClusterTask.ACTIVE_TASK and totaltasks > 0:
            # Override - always use a shade of green here
            self.color = '#00%02x00' % (45 + int(210.0 * float(tasksdone)/float(totaltasks)))
        else:    
            self.color = scheme[1]
        self.shape = scheme[2]
        if initial:
            self.shape = self.schema[ClusterTask.INITIAL_TASK][2]
            
class ExpectedException(Exception): pass  
    
class Graph(object):
    
    def __init__(self, tasks):
        self.vertices = {}
        self.edges = {}
        #initv = {"id" :0, "edges"[], "start", "initial", "#FFFFFF", "doublecircle", 1, 1, "start")
        self.vertices["init"] = Node(0, "start", "start", ClusterTask.INITIAL_TASK, 1, 1, True)
        self.edges["init"] = tasks
        self.numvertices = 1
        self._assimilate(tasks, initial = True)
        self._isATree = True
    
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
        
    def _assimilate(self, tasks, initial = False):
        for t in tasks:
            if not self.vertices.get(t):
                # Add vertex
                # (0=id, 1=Name, 2=shortname, 3=state name, 4=state color, 5=state shape in graph, 6=profile, 7=tasks completed, 8=total number of tasks)
                #todo: self.vertices[t] = (self.numvertices, status[0], status[1], scheme[0], scheme[1], scheme[2], status[3], status[4], status[5])
                #getstatus (self.name, self.shortname, st, profile, tasksCompleted, numtasks)
                status = t.getStatus()
                clongname = status[0]
                cshortname = status[1]
                cstatus = status[2]
                cdonetasks = status[4]
                ctotaltasks = status[5]
                self.vertices[t] = Node(self.numvertices, clongname, cshortname, cstatus, cdonetasks, ctotaltasks, initial)
                self.numvertices +=1
                
                #vertices: ClusterTask -> Node
                #edges: ClusterTask -> [ClusterTask]
                
                # Add edges
                dependents = t.getDependents()
                self.edges[t] = dependents
                
                # Recurse
                self._assimilate(dependents)
            else:
                self.isATree = false
                
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

    def __init__(self, tasks):
        super(JITGraph, self).__init__(tasks)
    
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

#%sdata : {
#%s"$color": "%s",  

    def _getSpaceTreeNode(self, parent, indent):
        vs = self.vertices
        es = self.edges
        indent2 = "%s  " % indent
        indent3 = "%s    " % indent
        n = vs[parent]
        nodestr = []
        nodestr.append('''%s{
%sid : "%s%d",
%sname : "%s",
%sCanvasStyles: {fillStyle: '#00f', strokeStyle: '#0ff', lineWidth: 2},
%sdata : {
//%s"$CanvasStyles": "{fillStyle: '%s', strokeStyle: '%s', lineWidth: 2}",
//%s"$CanvasStyles.$fillStyle": "%s",
%scolor: "%s",  
//%s"$type": "%s",  
//%s"$dim": 10  
%s}'''        % (indent, indent2, n.shortname, n.id, indent2, n.shortname, indent2, indent2, indent3, green, n.color, indent3, green, indent3, n.color, indent3, n.shape, indent3, indent2))

        nodestr = []
        nodestr.append('''%s{
%sid : "%s%d",
%sname : "%s",
%sdata : {
%scolor: "%s",  
%s}'''        % (indent, indent2, n.shortname, n.id, indent2, n.shortname, indent2, indent3, green, indent2))
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
        if not g.isATree():
            #upgradetodo: we need to embed the html here as well
            return self.getForceDirected()
        JITdata = "var json = %s;" % self._getSpaceTreeNode("init", "  ")
        return JITSpaceTree % JITdata
    
if __name__ == "__main__":
    g = JITGraph([])
    #initv = (0, "start", "initial", "#FFFFFF", "doublecircle", 1, 1, "start")
    #self.vertices[t] = (self.numvertices, cshortname, cstatus, ccolor, cshape, cdonetasks, ctotaltasks, clongname)
    g.vertices["backrub0"] = Node(1, 'backrub', 'backrub', ClusterTask.ACTIVE_TASK, 8, 8, False)
    g.vertices["backrub1"] = Node(3, 'backrub', 'backrub', ClusterTask.RETIRED_TASK, 0, 1, False)
    g.vertices["backrub2"] = Node(5, 'backrub', 'backrub', ClusterTask.COMPLETED_TASK, 0, 1, False)
    g.vertices["seqtol0"] = Node(2, 'seqtol', 'seqtol', ClusterTask.FAILED_TASK, 3, 10, False)
    g.vertices["seqtol1"] = Node(4, 'seqtol', 'seqtol', ClusterTask.QUEUED_TASK, 5, 10, False)
    g.vertices["seqtol2"] = Node(6, 'seqtol', 'seqtol', ClusterTask.INACTIVE_TASK, 8, 10, False)
    g.edges["init"] = ["backrub0", "backrub1", "backrub2"]
    g.edges["backrub0"] = ["seqtol0"]
    g.edges["backrub1"] = ["seqtol1"]
    g.edges["backrub2"] = ["seqtol2"]
    
    if g.isATree():
        #print(g.getSpaceTree())
        writeFile("/var/www/html/rosettaweb/backrub/images/JIT/Examples/Spacetree/example1.js", g.getSpaceTree())
    else:
        writeFile("/var/www/html/rosettaweb/backrub/images/JIT/Examples/ForceDirected/example1.js", g.getForceDirected())

