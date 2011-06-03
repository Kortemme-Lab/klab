// Copyright (c) 2010, Nicolas Garcia Belmonte. 
// This code has been modified from the JIT examples for use on the RosettaBackrub server by Shane O'Connor.

/*
  Copyright (c) 2010, Nicolas Garcia Belmonte
  All rights reserved

  > Redistribution and use in source and binary forms, with or without
  > modification, are permitted provided that the following conditions are met:
  >      * Redistributions of source code must retain the above copyright
  >        notice, this list of conditions and the following disclaimer.
  >      * Redistributions in binary form must reproduce the above copyright
  >        notice, this list of conditions and the following disclaimer in the
  >        documentation and/or other materials provided with the distribution.
  >      * Neither the name of the organization nor the
  >        names of its contributors may be used to endorse or promote products
  >        derived from this software without specific prior written permission.
  >
  >  THIS SOFTWARE IS PROVIDED BY NICOLAS GARCIA BELMONTE ``AS IS'' AND ANY
  >  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  >  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
  >  DISCLAIMED. IN NO EVENT SHALL NICOLAS GARCIA BELMONTE BE LIABLE FOR ANY
  >  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
  >  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
  >  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
  >  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
  >  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
  >  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

var labelType, useGradients, nativeTextSupport, animate;

var kortemmelabBlue = '#00b5f9';
var kortemmelabShadow = '#002d3d';

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
    this.elem.style.left = (400 - this.elem.offsetWidth / 2) + 'px';
  }
};

function componentToHex(c) {
    var hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgb2Hex(r, g, b) {
	return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

function hex2Rgb(hex) {
	return {r: parseInt(hex.substring(1, 3), 16),
			g: parseInt(hex.substring(3, 5), 16), 
			b: parseInt(hex.substring(5, 7), 16)};
}

function parsetime(timeinsec)
{
	tm = ""
	if (timeinsec > 60*60*24)
	{
		tm += Math.floor(timeinsec / 60*60*24) + "d ";
		timeinsec = timeinsec %% 60*60*24;
	}
	if (timeinsec > 60*60)
	{
		tm += Math.floor(timeinsec / 60*60) + "h ";
		timeinsec = timeinsec %% 60*60;
	}
	if (timeinsec > 60)
	{
		tm += Math.floor(timeinsec / 60) + "m ";
		timeinsec = timeinsec %% 60;
	}
	if (timeinsec > 0)
	{
		tm += Math.floor(timeinsec) + "s";
	}
	return tm;	
}

var st;
function init(){
    //init data
    %s
    //end
    //init Node Types
    //Create a node rendering function that plots a fill
    //rectangle and a stroke rectangle for borders
    $jit.ST.Plot.NodeTypes.implement({
      'stroke-rect2': {
        'render': function(node, canvas) {
          var width = node.getData('width'),
              height = node.getData('height'),
              pos = this.getAlignedPos(node.pos.getc(true), width, height),
              posX = pos.x + width/2,
              posY = pos.y + height/2;
          this.nodeHelper.rectangle.render('fill', {x: posX, y: posY}, width, height, canvas);
          this.nodeHelper.rectangle.render('stroke', {x: posX, y: posY}, width, height, canvas);
        }
      },
      'stroke-rect': {
          'render': function(node, canvas) {
            var width = node.getData('width'),
                height = node.getData('height'),
                pos = this.getAlignedPos(node.pos.getc(true), width, height),
                posX = pos.x + width/2,
                posY = pos.y + height/2;
            this.nodeHelper.rectangle.render('fill', {x: posX, y: posY}, width, height, canvas);
            
            var pos = node.pos.getc(true), nconfig = this.node, data = node.data;
            var algnPos = this.getAlignedPos(pos, width, height);
            
            var progress = node.getData('progress');
            if(progress) {
              var ctx = canvas.getCtx();
              ctx.save();
              var rgb = hex2Rgb(node.getData('color'));
              
              var rgbdark = rgb2Hex(Math.floor(rgb.r * 0.3), Math.floor(rgb.g * 0.3), Math.floor(rgb.b * 0.3));
              var lgradient = ctx.createLinearGradient(algnPos.x, algnPos.y + 0, algnPos.x + width -1, algnPos.y + 0 );
               
              var progress2 = progress + 0.1;
              lgradient.addColorStop(0, node.getData('color'));
              lgradient.addColorStop(progress, node.getData('color'));
              if (progress2 < 1.0)
              {
    			lgradient.addColorStop(progress2, rgbdark);
                lgradient.addColorStop(1, rgbdark);
              }
    		  else
    		  {
                  lgradient.addColorStop(1, rgbdark);    			  
    		  }
               
              ctx.fillStyle = lgradient;
              ctx.fillRect(algnPos.x, algnPos.y + 0, width, height);
            
              ctx.restore();
            }
            this.nodeHelper.rectangle.render('stroke', {x: posX, y: posY}, width, height, canvas);
            
            
          }
        }

    });
    var clicknum = 0;
    
    //end
    //init Spacetree
    //Create a new ST instance
    st = new $jit.ST({
        //id of viz container element
        injectInto: 'infovis',
        //set duration for the animation
        duration: 250,
        levelsToShow: 3,
        constrained: false,
        //set animation transition type
        transition: $jit.Trans.Quart.easeInOut,
        //set distance between node and its children
        levelDistance: 25,
        //enable panning
        Navigation: {
          enable:true,
          panning:true
        },
        //set node and edge styles
        //set overridable=true for styling individual
        //nodes or edges
        Node: { 
            height: 27,
            width: 80,
            type: 'stroke-rect',
            overridable: true,
            //canvas specific styles
            CanvasStyles: {
              strokeStyle: kortemmelabBlue,
              lineWidth: 2,
              shadowColor: kortemmelabShadow,
              shadowBlur: 4,
             }
        },
        
        Edge: {
            type: 'bezier',
            overridable: true
        },
        
        Events: {
            enable: true,
            //Change cursor style when hovering a node
            onMouseEnter: function() {
              st.canvas.getElement().style.cursor = 'move';
            },
            onMouseLeave: function() {
              st.canvas.getElement().style.cursor = '';
            },
            //Update node positions when dragged
            onDragMove: function(node, eventInfo, e) {
                var pos = eventInfo.getPos();
                node.pos.setc(pos.x, pos.y);
                st.plot();
            },
            //Implement the same handler for touchscreens
            onTouchMove: function(node, eventInfo, e) {
              $jit.util.event.stop(e); //stop default touchmove event
              this.onDragMove(node, eventInfo, e);
            }
          },
          
        onBeforeCompute: function(node){
            //Log.write("loading " + node.name);
        },
        
        onAfterCompute: function(){
            //Log.write("done");
        },
        
        //This method is called on DOM label creation.
        //Use this method to add event handlers and styles to
        //your node.
        onCreateLabel: function(label, node){
            label.id = node.id;            
            label.innerHTML = node.name;
            label.onclick = function(){
                  st.onClick(node.id);
                  if(!node) return;
                  
                  // little hack to get the centering to the left of the root on load but then reset to the JIT default on the first user click
                  //if (clicknum == 1)
                  //{
                  //	  st.canvas.translate(150, 0)
                  //}
                  clicknum += 1;
                  //
                  
                  // Build the right column relations list.
                  // This is done by traversing the clicked node connections.
                  
                  // dependents
                  dependentlist = [];
                  node.eachSubnode(
                      	function(adj)
                      	{
                      		dep = "<font color='" + adj.data.$color + "'>" + adj.name + "</font>"
                      		if (adj.data.$exclusive > 0)
                      		{
                      			dep += " (" + parsetime(adj.data.$exclusive) + ")";
                      		}
                      		else
                      		{
                      			dep += " (" + parsetime(adj.data.$inclusive) + ")";
                      		}
                      		dependentlist.push(dep)                        	  
                      	});
                  
                  // parents
                  parentlist = [];
                  var parents = $jit.Graph.Util.getParents(node);
                  for (i = 0; i < parents.length; i++)
                  {
                	  par = parents[i]
                	  parstr = "<font color='" + par.data.$color + "'>" + par.name + "</font>"
                	  if (par.data.$exclusive > 0)
                	  {
                		  parstr += " (" + parsetime(par.data.$exclusive) + ")";
                	  }
                	  parentlist.push(parstr)                          	  
                  }
                  
                  // HTML
                  // task information
                  var html = "<p><font color='black'><b>" + node.name + "</b>"
                  if (node.data.$inclusive > 0)
                  {
                	  html += "<br>Inclusive time: " + parsetime(node.data.$inclusive);
                  }
                  if (node.data.$exclusive > 0)
                  {
                	  html += "<br>Exclusive time: " + parsetime(node.data.$exclusive);
                  }
                  if (node.data.$totaltasks > 1)
                  {
                	  html += "<br>Tasks completed: " + node.data.$tasksdone + "/" + node.data.$totaltasks;
                  }
                	  
                  html += "</font></p>"

                  // profile details
                  profile = node.data.$profile;
                  if (profile.length > 0)
                  {
                	  profilestr = []
                	  for (i = 0 ; i < profile.length; i++)
                	  {
                		  profilestr.push(profile[i][0] + ": " + parsetime(profile[i][1]))
                	  }
                	  html = html + "<b>Timer breakdown:</b><font color='black'><ul><li>" + profilestr.join("</li><li>") + "</li></ul></font>";                	  
                  }
                  
                  // related task information
                  if (dependentlist.length > 0)
                  {
                	  html = html + "<b>Dependent jobs:</b><ul><li>" + dependentlist.join("</li><li>") + "</li></ul>";
                  }
                  if (parentlist.length > 0)
                  {
                	  html = html + "<b>Parent jobs:</b><ul><li>" + parentlist.join("</li><li>") + "</li></ul>";
                  }
                        
                  //append connections information
                  //$jit.id('inner-details').innerHTML = html
                  $jit.id('right-container').innerHTML = html
                
            };
            //set label styles
            var style = label.style;
            
            CSSStyleDeclaration
            style.width = 60 + 'px';
            style.height = 17 + 'px';            
            style.cursor = 'pointer';
            style.color = node.getData('textcolor')
            style.fontSize = '0.9em';
            style.fontFamily = 'times';
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
                node.setCanvasStyle('strokeStyle', '#fff');   // todo reverse this below
                node.data.$lineWidth = 5;
            }
            else {
            	node.setCanvasStyle('strokeStyle', kortemmelabBlue);   // todo reverse this below
                node.data.$lineWidth = 2;
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
    // shift canvas to the left - little hack, see above
    //st.canvas.translate(-150, 0)

    // click the root label to populate the right panel
    // the timeout seems to be necessary from what I'm guessing is a threading issue
    // the graph isn't always set up properly by this stage
    setTimeout('st.labels.getLabel("start0").onclick()', 1000)
    
    //end

}