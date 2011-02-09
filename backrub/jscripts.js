
var numMPM = 0; // Multiple Point Mutations
var numSeqTol = 0; // Mutation SeqTol
var numSeqTolSK = 1; // Mutation SeqTolSK
var numSeqTolSKPremutations = 0; // Mutation SeqTolSK
const initNumSeqTolSKChains = 2;
const minSeqTolSKMutations = 1;
const minSeqTolSKPremutations = 0;
var numSeqTolSKChains = initNumSeqTolSKChains; // Initial number of chains for SeqTolSK

// Constants

// Sequence Tolerance (Humphris and Kortemme, Smith and Kortemme)
// todo: add these on the fly using Python constants
const HK_MaxMutations = 10;

function startup(query)
{
	// Round the corners using Nifty
	if (query == "submit" || query == "submitted") 
	{
		Nifty("ul#about li","big fixed-height");
        Nifty("div#box","big transparent fixed-height");
    }
	else if (query == "index" || query == "login") 
    {
    	Nifty("div#login_box","big transparent fixed-height");
    }
	else if (query == "queue" ) 
    {
    	Nifty("div#queue_bg","big transparent fixed-height");
    }
	else if (query == "jobinfo") 
    {
    	Nifty("div#jobinfo","big transparent fixed-height");
    }
    //updateCellSize2();
}

function ValidateFormRegister()
{ 
	if ( document.myForm.username.value == "" ||
			document.myForm.firstname.value == "" ||
            document.myForm.lastname.value == "" ||
            document.myForm.password.value == "" ||
            document.myForm.confirmpassword.value == "")
	{
		alert("Please complete all required fields.");
        return false;
	}
    
	if ( document.myForm.email.value.indexOf("@") == -1 ||
            document.myForm.email.value.indexOf(".") == -1 ||
            document.myForm.email.value.indexOf(" ") != -1 ||
            document.myForm.email.value.length < 6 )
	{
		alert("Your email address is not valid.");
        return false;
	}
	if ( document.myForm.password.value != document.myForm.confirmpassword.value  )
    {
		alert("Your password does not match your password confirmation.");
        return false;
    }
    return true;
}

function isNumeric(elem)
{
	var numericExpression = /^[0-9\.]+$/;
	if(elem.value.match(numericExpression))
	{
		elem.style.background="white";
		return true;
	}
	else
	{
    // alert(helperMsg);
		elem.focus();
		elem.style.background="red";
		return false;
	}
}

function isAlpha(elem)
{
	var numericExpression = /^[A-Za-z]+$/;
	if(elem.value.match(numericExpression))
	{
		elem.style.background="white";
		return true;
	}
	else
	{
		// alert(helperMsg);
		elem.focus();
		elem.style.background="red";
		return false;
	}
}

function isAA(elem)
{
	var numericExpression = /^[ACDEFGHIKLMNOPQRSTUVWY]+$/;
	if(elem.value.match(numericExpression))
	{
		elem.style.background="white";
		return true;
	}
	else
	{
		// alert(helperMsg);
		elem.focus();
		elem.style.background="red";
		return false;
	}
}

function isCYS(elem)
{
	if(elem.value == "C")
	{
		alert("We're sorry, but mutation to Cystein is not allowed.");
		elem.focus();
		elem.style.background="red";
		return false;
	}
	else
	{
		elem.style.background="white";
		return true;
	}
}


function isPDB(elem){
	var numericExpression = /^[A-Za-z0-9]+$/;
	if(elem.value.match(numericExpression))
	{
		elem.style.background="white";
		return true;
	}
	else
	{
		// alert(helperMsg);
		elem.focus();
		elem.style.background="red";
		return false;
	}
}

function checkIsEmpty(elem)
{
	return elem.value.length == 0;
}

function checkIsAlpha(elem)
{
	var numericExpression = /^[A-Za-z]+$/;
	if(elem.value.match(numericExpression))
	{
		return true;
	}
	else
	{
		return false;
	}
}

function markError(elem)
{
	elem.focus();
	elem.style.background="red";
}

function notEmpty(elem)
{
	if(elem.value.length == 0)
	{
		// alert(helperMsg);
		elem.focus();
		elem.style.background="red";
		return false;
	}
	elem.style.background="white";
	return true;
}

function isEmpty(elem)
{
    if (elem == "" || elem == null || !isNaN(elem) || elem.charAt(0) == '' )
    {
        return true;
    }
    return false;
}


function allWhite()
{
	for(i = 0; i < document.submitform.elements.length; i++)
	{
		var elem = document.submitform.elements[i];
		if ((elem.disabled == false) || (elem.name == "UserName"))
		{
			elem.style.background = "white";
		}
		else
		{
			elem.style.background = "grey";
		}
	}
}

function ValidateForm()
{
	allWhite();
	var returnvalue = new Array(); // we collect all the return values, if only one is "false" in the end, we return false
    returnvalue.push( notEmpty(document.submitform.JobName) );
    if (document.submitform.PDBComplex.value == "" && document.submitform.PDBID.value == "" ) 
    {
    	document.submitform.PDBComplex.style.background="red";
    	document.submitform.PDBID.style.background="red";
    	// alert("Please upload a structure or enter a PDB identifier.");
    	returnvalue.push(false);
    }
    else 
    {
    	document.submitform.PDBComplex.style.background="white";
    	document.submitform.PDBID.style.background="white";
    	returnvalue.push(true);
    }
    if ( document.submitform.PDBComplex.value == "" ) 
    {
    	if ( document.submitform.PDBID.value.length < 4 ) 
    	{
    		document.submitform.PDBID.style.background="red";
    		returnvalue.push(false);
    	}
    	else
    	{
    		returnvalue.push(isPDB(document.submitform.PDBID));
    	}
    }

    if ( notEmpty(document.submitform.nos) && isNumeric(document.submitform.nos) ) 
    {
    	if ( document.submitform.nos.value < 2 || document.submitform.nos.value > 50 ) 
    	{
            document.submitform.nos.style.background="red";
            returnvalue.push(false);
        }
    }
    else 
    {
    	returnvalue.push(false); 
    }

    if ( document.submitform.task.value == "parameter1_1" ) {
      returnvalue.push(notEmpty(document.submitform.PM_chain)); 
      returnvalue.push(isAlpha(document.submitform.PM_chain));
      returnvalue.push(notEmpty(document.submitform.PM_resid)); 
      returnvalue.push(isNumeric(document.submitform.PM_resid));
      returnvalue.push(notEmpty(document.submitform.PM_newres));
      returnvalue.push(isAA(document.submitform.PM_newres));
      returnvalue.push(notEmpty(document.submitform.PM_radius));
      returnvalue.push(isNumeric(document.submitform.PM_radius));
      if ( document.submitform.Mini.value == 'mini') {
          returnvalue.push(isCys(document.submitform.PM_newres));          
      }
    }
    
    if ( document.submitform.task.value == "parameter1_2" ) {
      var i=0;
      for (i=0;i<=30;i=i+1) {
        // check if row is empty
        if ( isEmpty(document.submitform.elements['PM_chain' + '' + i].value) && 
             isEmpty(document.submitform.elements['PM_resid' + '' + i].value) && 
             isEmpty(document.submitform.elements['PM_newres'+ '' + i].value) && 
             isEmpty(document.submitform.elements['PM_radius'+ '' + i].value) ) {
           // break the loop
           if ( i==0 ) {
               returnvalue.push(false);
               document.submitform.elements['PM_chain' + '' + i].style.background="red";
               document.submitform.elements['PM_resid' + '' + i].style.background="red";
               document.submitform.elements['PM_newres'+ '' + i].style.background="red";
               document.submitform.elements['PM_radius'+ '' + i].style.background="red";
           }
           break;
        }
        // if not empty, check if ALL values are entered correctly.
        returnvalue.push( notEmpty(document.submitform.elements['PM_chain' + '' + i]));
        returnvalue.push( isAlpha(document.submitform.elements['PM_chain' + '' + i]));
        returnvalue.push( notEmpty(document.submitform.elements['PM_resid' + '' + i]));
        returnvalue.push( isNumeric(document.submitform.elements['PM_resid' + '' + i]));
        returnvalue.push( notEmpty(document.submitform.elements['PM_newres'+ '' + i]));
        returnvalue.push( isAlpha(document.submitform.elements['PM_newres'+ '' + i]));
        if ( document.submitform.Mini.value == 'mini' ) { returnvalue.push(isCys(document.submitform.elements['PM_newres' + '' + i])); }
        returnvalue.push( notEmpty(document.submitform.elements['PM_radius'+ '' + i]));
        returnvalue.push( isNumeric(document.submitform.elements['PM_radius'+ '' + i]));
      }
    }
    
    if ( document.submitform.task.value == "parameter2_2" ) {
      returnvalue.push( notEmpty(document.submitform.ENS_temperature) ); 
      returnvalue.push( isNumeric(document.submitform.ENS_temperature) );
      if ( parseFloat(document.submitform.ENS_temperature.value) < 0.0 || parseFloat(document.submitform.ENS_temperature.value) > 4.8) { 
          returnvalue.push(false);  
          document.submitform.ENS_temperature.style.background="red";
          }
      returnvalue.push( notEmpty(document.submitform.ENS_num_designs_per_struct) ); 
      returnvalue.push( isNumeric(document.submitform.ENS_num_designs_per_struct) );
      returnvalue.push( notEmpty(document.submitform.ENS_segment_length) ); 
      returnvalue.push( isNumeric(document.submitform.ENS_segment_length) );
    }
    
    if ( document.submitform.task.value == "parameter1_3" ) {
            returnvalue.push( notEmpty(document.submitform.Mutations) );
    }
    
    if ( document.submitform.task.value == "parameter3_1" ) {
        returnvalue.push( notEmpty( document.submitform.seqtol_chain1) );
        returnvalue.push( isAlpha( document.submitform.seqtol_chain1) );
        returnvalue.push( notEmpty( document.submitform.seqtol_chain2) );
        returnvalue.push( isAlpha( document.submitform.seqtol_chain2) );
        // notEmpty( document.submitform.seqtol_weight_chain1, "Please enter a weight for Partner 1");
        // notEmpty( document.submitform.seqtol_weight_chain2, "Please enter a weight for Partner 2");
        // notEmpty( document.submitform.seqtol_weight_interface, "Please enter a weight for the interface") ;
        var i=0;
        for (i = 0; i <= HK_MaxMutations ; i = i + 1) {
          // check if row is empty
          if ( document.submitform.elements['seqtol_mut_c_' + '' + i].value.length == 0 && 
               document.submitform.elements['seqtol_mut_r_' + '' + i].value.length == 0 ) {
            break;
          }
          returnvalue.push( notEmpty(document.submitform.elements['seqtol_mut_c_' + '' + i]));
          returnvalue.push( isAlpha(document.submitform.elements['seqtol_mut_c_' + '' + i]));
          returnvalue.push( notEmpty(document.submitform.elements['seqtol_mut_r_' + '' + i]));
          returnvalue.push( isNumeric(document.submitform.elements['seqtol_mut_r_' + '' + i]));
        }
    }
    
    if ( document.submitform.task.value == "parameter3_2" ) 
    {        
    	// Highlight Partner 1 if no partners are specified
    	var allempty = true;
    	chainList = new Array();
    	for (i = 0; i < SK_max_seqtol_chains ; i = i + 1) 
    	{
    		var c = document.submitform.elements["seqtol_SK_chain" + i];
    		var cval = c.value;
    		var cIsEmpty = (cval.length == 0);
    		allempty = allempty && cIsEmpty;
    		
    		// require unique chain names
    		if (!cIsEmpty)
    		{
    			if (chainList[cval])
    			{
    				markError(c);
    				returnvalue.push(false);
    			}
    			chainList[cval] = true;
    		}
    	}
    	if (allempty == true)
    	{
    		returnvalue.push( notEmpty( document.submitform.seqtol_SK_chain0) );
    		returnvalue.push( isAlpha ( document.submitform.seqtol_SK_chain0) );
    	}
    
    	// Highlight Boltzmann factor if missing or invalid
		if (!document.submitform.elements["customBoltzmann"].checked)
		{
			returnvalue.push( notEmpty( document.submitform.seqtol_SK_Boltzmann) );
			returnvalue.push( isNumeric ( document.submitform.seqtol_SK_Boltzmann) );
		}
		
		// Highlight any blank premutation rows
        var i=0;
        for (i = 0; i < SK_MaxPremutations ; i = i + 1) {
        	var row =  document.getElementById("seqtol_SK_pre_row_" + i);
        	if (row.style.display != "none")
	        {
        		// check if row is empty
        		if ( document.submitform.elements['seqtol_SK_pre_mut_c_' + '' + i].value.length == 0 && 
        			document.submitform.elements['seqtol_SK_pre_mut_r_' + '' + i].value.length == 0 &&
        			document.submitform.elements['premutatedAA' + i].value.length != 3) 
        		{
        			continue;
                }
                returnvalue.push( notEmpty (document.submitform.elements['seqtol_SK_mut_c_' + i]));
	            returnvalue.push( isAlpha  (document.submitform.elements['seqtol_SK_mut_c_' + i]));
	            returnvalue.push( notEmpty (document.submitform.elements['seqtol_SK_mut_r_' + i]));
	            returnvalue.push( isNumeric(document.submitform.elements['seqtol_SK_mut_r_' + i]));
	            /* Note: The next line depends on the fact that the default option is not 
	             		 alphabetic (as it contains spaces) and that the valid values are alphabetic */
	            returnvalue.push( isAlpha (document.submitform.elements['premutatedAA' + i]));
        	}
        }
        
    	// Highlight any blank mutation rows
        var i=0;
        for (i = 0; i < SK_MaxMutations ; i = i + 1) {
        	var row =  document.getElementById("seqtol_SK_row_" + i);
        	if (row.style.display != "none")
	        {
        		//alert(""+document.submitform.elements['seqtol_SK_mut_c_' + '' + i].value.length);
        		// check if row is empty
        		if ( document.submitform.elements['seqtol_SK_mut_c_' + '' + i].value.length == 0 && 
        			document.submitform.elements['seqtol_SK_mut_r_' + '' + i].value.length == 0 ) 
        		{
        			continue;
                }
                returnvalue.push( notEmpty (document.submitform.elements['seqtol_SK_mut_c_' + i]));
	            returnvalue.push( isAlpha  (document.submitform.elements['seqtol_SK_mut_c_' + i]));
	            returnvalue.push( notEmpty (document.submitform.elements['seqtol_SK_mut_r_' + i]));
	            returnvalue.push( isNumeric(document.submitform.elements['seqtol_SK_mut_r_' + i]));
        	}
        }
        
        // Highlight any missing weights
        for (i = 0; i < SK_max_seqtol_chains ; i = i + 1) 
        {
        	for (j = i; j < SK_max_seqtol_chains ; j = j + 1) 
            {
        		var c = document.submitform.elements["seqtol_SK_kP" + i + "P" + j]; 
        		if (c.style.background == "white")
            	{
            		returnvalue.push( notEmpty(c));
    	            returnvalue.push( isNumeric(c));
            	}	
            }
        }		
    }
    
    // if there's only one false, return false
    var j=0;
    for (j=0;j<=returnvalue.length;j=j+1) {
    	if (returnvalue[j] == false )
    	{
    		return false; 
    	}
    }
    return true;
}

function set_Boltzmann()
{
	var b = document.submitform.elements["seqtol_SK_Boltzmann"];
	if (document.submitform.elements["customBoltzmann"].checked)
	{
		b.style.background="silver";
		b.disabled = true;
	}
	else
	{
		b.style.background="white";
		b.disabled = false;
	}
	/*
	var i = 0;
    for (i = 0; i < SK_MaxMutations ; i = i + 1) 
    {
    	var row =  document.getElementById("seqtol_SK_row_" + i);
    	if (row.style.display == "none")
    	{
    		break;
    	}
    }
    //document.submitform.seqtol_SK_Boltzmann.value = SK_InitialBoltzmann + SK_BoltzmannIncrease * i;
    */
}

var columnElements;

function buildSKColumns()
{	
	if (!columnElements)
	{
		columnElements = new Array();
		for (i = 0; i < SK_max_seqtol_chains; i = i + 1)
		{
			columnElements[i] = new Array();
		}

		if (document.getElementsByClassName == undefined)
		{
			alert("here")
			var integralExpression = /^[0-9]+$/;
						
			var tds = document.getElementsByTagName("td");
			for (j = 0; j < tds.length; j++)
			{
				var cn = tds[j].className;
				if (cn && cn.indexOf("seqtol_SK_kP") == 0)
				{
					var idx = cn.substring(11);
					if (idx.match(integralExpression))
					{
						idx = parseInt(idx);
						if (idx < SK_max_seqtol_chains - 1)
						{
							alert("add " + columnElements[idx].className + " to list " + idx)
						}
					}
				}
			}
		}
		else
		{
			for (i = 0; i < SK_max_seqtol_chains - 1 ; i = i + 1)
			{
				columnElements[i] = document.getElementsByClassName("seqtol_SK_kP" + i)
			}
		}
	}
}

function addChain(_key)
{
	var elems = document.submitform.elements;
	var firstblank;
	for (i = 0; i < numSeqTolSKChains; i++)
	{
		var e = elems["seqtol_SK_chain" + i];
		var ev = e.value;
		if (ev == _key)
	    {
	    	return;
	    }
		if (ev == "" && !firstblank)
		{
			firstblank = e;
		}
	}
	if (firstblank)
	{
		firstblank.value = _key;
		chainsChanged();
	}
	else
	{
		if (numSeqTolSKChains < SK_max_seqtol_chains)
		{
			elems["seqtol_SK_chain" + numSeqTolSKChains].value = _key;
			addOneMoreChainSK();
		}
		chainsChanged();
	}
} 

function chainAddedSK(idx, type)
{
	var c;
	if (type == 0)
	{
		c = document.submitform.elements["seqtol_SK_pre_mut_c_" + idx];
	}
	else if (type == 1)
	{
		c = document.submitform.elements["seqtol_SK_mut_c_" + idx];
	}
	else
	{
		// Should never occur
		return;
	}
	if (checkIsAlpha(c))
	{
		cv = c.value;
		// todo: If chain ids are always uppercase, enable this line: cv = c.value.toUpperCase();
		c.value = cv;
		addChain(cv);
	}
}

function chainsChanged()
{
	var i;
	var chainIsInvalid = new Array();
	
	buildSKColumns();
	
	var highestValidChain = initNumSeqTolSKChains - 1;
	for (i = 0; i < SK_max_seqtol_chains ; i = i + 1)
	{
		var c = document.submitform.elements["seqtol_SK_chain" + i];
		var invalid = checkIsEmpty(c) || !checkIsAlpha(c);
		chainIsInvalid[i] = invalid
		if (!invalid && (i > highestValidChain))
		{
			highestValidChain = i
		}
	}
			
	for (i = 0; i < SK_max_seqtol_chains ; i = i + 1)
	{
		// Hide the rows and columns of any invalid chains
		if (chainIsInvalid[i] && i >= initNumSeqTolSKChains)
		{
			new Effect.Fade( "seqtol_SK_weight_" + i , { duration: 0.0 } );
			
			for (var k = 0; k < columnElements[i].length; k++)
			{
				new Effect.Fade( columnElements[i][k] , { duration: 0.0 } );
			}				
		}
		else
		{
			
			new Effect.Appear( 'seqtol_SK_weight_' + i, { duration: 0.5, queue: { scope: 'task' } } ) ;
			if ((highestValidChain > i) && i < (SK_max_seqtol_chains - 1))
			{
				for (var k = 0; k < columnElements[i].length; k++)
				{
					new Effect.Appear( columnElements[i][k] , { duration: 0.0 } );
				}
			}
		}
		if (initNumSeqTolSKChains > 1 && highestValidChain < initNumSeqTolSKChains)
		{
			for (var k = 0; k < columnElements[initNumSeqTolSKChains - 1].length; k++)
			{
				new Effect.Fade( columnElements[initNumSeqTolSKChains - 1][k] , { duration: 0.0 } );
			}
		}
		
		for (j = i; j < SK_max_seqtol_chains ; j = j + 1)
		{
			var pself = "seqtol_SK_kP" + i + "P" + j;
			if (chainIsInvalid[i] || chainIsInvalid[j])
			{
				document.submitform.elements[pself].style.background="silver";
				document.submitform.elements[pself].disabled = true;
			}
			else
			{
				document.submitform.elements[pself].style.background="white";
				document.submitform.elements[pself].disabled = false;
			}
		}	
	}	
}
	
function ValidateFormEmail()
{
	if ( document.myForm.Email.value.indexOf("@") == -1 ||
		document.myForm.Email.value.indexOf(".") == -1 ||
        document.myForm.Email.value.indexOf(" ") != -1 ||
        document.myForm.Email.value.length < 6 )
	{
		alert("Your email address is not valid.");
        return false;
    }
    return true;
}

// This function shows the input form for the protocol <_task> of protocol series <app>.
// This includes a logo and parameter fields for the protocol.
function changeApplication( app, _task ) {

	// Clear all form fields
	document.submitform.reset();
	allWhite();
	
	// Names of HTML elements defined in rosettahtml.py for defining specialized protocol parameters
	// Change these two arrays if you change the table in rosettahtml.py
	myParameter = new Array("parameter1_1","parameter1_2","parameter1_3",
	                        "parameter2_1","parameter2_2",
	                        "parameter3_1","parameter3_2");
  
	// Names of images (logo) and HTML elements defined in rosettahtml.py for describing the protocols
 	myFields = new Array( "logo1","logo2","logo3",
 							"text1","text2","text3",
 							"ref1","ref2","ref3" );

  	// Hide the description of the protocol series #app
  	new Effect.Fade( "text" + app , { duration: 0.0 } );
  	//new Effect.Fade( "ref" + app, { duration: 0.0 } );

  	task = "parameter" + app + "_" + _task;
  	
  	// Set the form's "task" value
	setTask(task);
	
	// Show the HTML elements for entering parameters and submitting the form
  	new Effect.Appear( 'parameter_common', { duration: 0.5, queue: { scope: 'task' } } ) ;
	new Effect.Appear( task, { duration: 0.5 } )
  	new Effect.Appear( 'parameter_submit', { duration: 0.5, queue: { scope: 'task' } } ) ;
  
	// Hide all other specialized parameters
	for ( i = 0; i < myParameter.length; i++ ) 
	{
		if ( myParameter[i] != task) 
		{
			new Effect.Fade( myParameter[i], { duration: 0.0 } );
		}
	}
	
	// Fix up the default Rosetta versions for the different protocols and hide non-applicable versions
	if ( task == 'parameter1_1' || task == 'parameter1_2' || task == 'parameter2_1' ) 
	{ 
		new Effect.Appear( "ref1" );
	  	document.submitform.Mini[0].checked=true;
	  	document.submitform.Mini[0].disabled=false;
	    document.submitform.Mini[1].disabled=false;
	    // 
	    document.getElementById('rv0').style.color='#000000';
	    document.getElementById('rv1').style.color='#000000';
  	}
  	else 
  	{ 
    	new Effect.Fade( "ref1", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
  	}
	if ( task == 'parameter2_2' ) 
	{  
		new Effect.Appear( "ref2" ); 
	  	new Effect.Appear( "rosetta_remark" );
	  	document.submitform.Mini[0].checked=true;
	    document.submitform.Mini[1].disabled=true;
	    document.getElementById('rv0').style.color='#000000';
	    document.getElementById('rv1').style.color='#D8D8D8';
	}
	else
	{ 
		new Effect.Fade( "ref2", { duration: 0.0, queue: { position: '0', scope: 'task' } } ); 
    	new Effect.Fade( "rosetta_remark", { duration: 0.0, queue: { position: '20', scope: 'task' } } );
    }
	if ( task == 'parameter3_1' ) { 
		new Effect.Appear( "ref3" ); 
	  	document.submitform.Mini[0].disabled=false;
	    document.submitform.Mini[0].checked=true;
	    document.submitform.Mini[1].disabled=true;
	    document.getElementById('rv1').style.color='#D8D8D8';
	    document.getElementById('rv0').style.color='#000000';
	    // todo: Is this intentional?
	    //document.getElementById('rv1').style.color='#000000';	  
	}
	else 
	{ 
	  new Effect.Fade( "ref3", { duration: 0.0, queue: { position: '0', scope: 'task' } } ); 
	}
	if ( task == 'parameter3_2' ) { 
		chainsChanged();
		reset_seqtolSKData();
		new Effect.Appear( "ref4" ); 
	  	document.submitform.Mini[0].disabled=true;
	    document.submitform.Mini[0].checked=false;
	    document.submitform.Mini[1].disabled=false;
	    document.submitform.Mini[1].checked=true;
	    document.getElementById('rv0').style.color='#D8D8D8';
	    document.getElementById('rv1').style.color='#000000';
	    
	    //new Effect.Fade("seqtol_SK_addrow", { duration: 0.0 } );
	    
	}
	else 
	{ 
	  new Effect.Fade( "ref4", { duration: 0.0, queue: { position: '0', scope: 'task' } } ); 
	}

	// Change the colour of the box depending on the series and add the appropriate logo
	mycolor = "";
	if (task == 'parameter1_1' || task == 'parameter1_2') {
		mycolor = "#DCE9F4" ;
	    new Effect.Appear("pic1");
	    new Effect.Fade( "pic2", { duration: 0.0, queue: { position: '0', scope: 'img' } } );
	    new Effect.Fade( "pic3", { duration: 0.0, queue: { position: '0', scope: 'img' } } );   
	}
	else if (task == 'parameter2_1' || task == 'parameter2_2') {
	    mycolor = "#B7FFE0" ;
	    new Effect.Appear("pic2");
	    new Effect.Fade( "pic1", { duration: 0.0, queue: { position: '0', scope: 'img' } } );
	    new Effect.Fade( "pic3", { duration: 0.0, queue: { position: '0', scope: 'img' } } );
	}
	else if (task == 'parameter3_1' || task == 'parameter3_2') {
	    mycolor = "#FFE2E2" ;
	    new Effect.Appear("pic3");
	    new Effect.Fade( "pic1", { duration: 0.0, queue: { position: '0', scope: 'img' } } );
	    new Effect.Fade( "pic2", { duration: 0.0, queue: { position: '0', scope: 'img' } } );
	}
  
	document.getElementById("box").style.background = mycolor;
}

// This function shows the preliminary screen for each protocol series.
// This includes a logo and descriptive text but no input form.
function showMenu( menu_id ) {
	
    document.submitform.reset();
    /* This function extends or hides the menu on the left */
    
    // Names of HTML elements defined in rosettahtml.py for describing the protocols
    myTasks = new Array("pic1","pic2","pic3",
                        "text1","text2","text3"); // ,
                        //"ref1","ref2","ref3" );
    
    // Names of HTML elements defined in rosettahtml.py for defining generalised and specialized protocol parameters
    myParameter = new Array("parameter_common", "parameter_submit",
                            "parameter1_1", "parameter1_2", "parameter1_3",
  	                        "parameter2_1", "parameter2_2",
  	                        "parameter3_1", "parameter3_2");
    
    // this builds an dictionary that supports the in operator
    myFields = oc(['pic', 'text','ref'], menu_id);

    // The background colors for the protocol series
    mycolor = "";     
    if (menu_id == "1")
    {
    	mycolor = "#DCE9F4" ;
    } 
    else if (menu_id == "2") 
    {
    	mycolor = "#B7FFE0" ;
    }
    else if (menu_id = "3")
    {
    	mycolor = "#FFE2E2" ;
    }
    
    // box contains the pici, texti, common parameters, parameteri_j, parameter submission, and refi elements where i = menu_id
    // Essentially, it is the right column in the description (resp. submission pages) for protocol series (resp. protocols)   
    // Set the color as above and the minimum height.
    document.getElementById("box").style.background = mycolor;
    document.getElementById("box").style.minHeight = document.getElementById("columnLeft").style.offsetHeight;
    Nifty("div#box","big transparent fixed-height");
     
    // Hide the common submission page text
    new Effect.Fade( "text0", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
    
    // new Effect.Appear( "parameter_common", { queue: { position: '0', scope: 'task' } } );
    // new Effect.Appear( "parameter_submit", { queue: { position: '0', scope: 'task' } } );
    
    // Display any elements of myTasks suffixed with menu_id and hide all others
    // This will just display the logo and descriptive text. 
	for ( i=0; i < myTasks.length; i++ )
    {
    	if ( myTasks[i] in myFields )
    	{
    		new Effect.Appear( myTasks[i] );
        }
    	else
    	{
    		new Effect.Fade( myTasks[i], { duration: 0.0, queue: { position: '0', scope: 'task' } } );
        }
    }
    // Hide all parameter fields (used on the submission pages)
    for ( i = 0; i < myParameter.length; i++ )
    {
    	new Effect.Fade( myParameter[i], {duration: 0.0, queue: {position: '0', scope: 'parameter'} } );
    }
    
    // Hide all reference elements
    new Effect.Fade( "ref1", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
  	new Effect.Fade( "ref2", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
  	new Effect.Fade( "ref3", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
        
    return true;
}

/************************************
 * helper functions 
 ************************************/

// Creates a dictionary/hashtable mapping keys which are a concatenation of an element of a with (the number) n 
// e.g. oc(['pic','text',...],3) returns ['pic3' -> '', 'text3'->'',...]
function oc(a, n)
 {
   var o = {};
   for(var i=0;i<a.length;i++)
   {
     o[a[i]+n]='';
   }
   return o;
 }

// Setter and getter for document.submitform.task
function getTask()
{
	return document.submitform.task.value
}

function setTask(mode)
{
    document.submitform.task.value = mode;
    //alert(mode);
    return true;
}

// todo: unused at present - make use of this or delete
function setMini( disable )
{
	if ( disable == 1 ) 
	{
	    document.submitform.Mini[0].disabled=true;
	    document.submitform.Mini[1].disabled=true;
	    //document.submitform.keep_output.disabled=true;
	    document.getElementById('rosetta1').style.color='#D8D8D8';
	    //document.getElementById('rosetta2').style.color='#D8D8D8';
    }
	else 
	{
	    document.submitform.Mini[0].disabled=false;
	    document.submitform.Mini[1].disabled=false;
	    //document.submitform.keep_output.disabled=false;
	    document.getElementById('rosetta1').style.color='#000000';
	    //document.getElementById('rosetta2').style.color='#000000';
    }
    return true;
}

// todo: Unused - delete
function updateCellSize1( task )
{
    var high = document.getElementById( 'pic' ).offsetHeight + document.getElementById( 'common_form' ).offsetHeight + document.getElementById( 'submit_button' ).offsetHeight + document.getElementById( task ).offsetHeight ;
    document.getElementById('empty_box').style.height = high ;
}

//todo: Unused - delete
function updateCellSize2()
{
    var high = document.getElementById( 'pic' ).offsetHeight + document.getElementById( 'task_init' ).offsetHeight;
    document.getElementById('empty_box').style.height = high ;
}

// Adds a residue input field for Multiple point mutations
// todo: Add delete functionality
function addOneMore()
{
    numMPM = numMPM + 1;
    //document.write("row_PM");
    //document.write(numMPM);
    new Effect.Appear("row_PM" + "" + numMPM);
    //return "row_PM" + "" + numMPM;
    
    return true;
}

//Adds a residue input field for Humphris and Kortemme's Interface Sequence Plasticity Prediction
//todo: Add delete functionality
function addOneMoreSeqtol()
{
    numSeqTol = numSeqTol + 1;
    new Effect.Appear("seqtol_row_" + "" + numSeqTol);
    return true;
}

//Adds a residue input field for Smith and Kortemme's Interface Sequence Plasticity Prediction
//todo: Add delete functionality
function addOneMoreSeqtolSK()
{
  new Effect.Appear("seqtol_SK_row_" + "" + numSeqTolSK);
  numSeqTolSK = numSeqTolSK + 1;
  if (numSeqTolSK >= SK_MaxMutations)
  {
	  new Effect.Fade("seqtol_SK_addrow", { duration: 0.0 } );
  }
  return true;
}

function addOneMoreSeqtolSKPremutated()
{
	new Effect.Appear("seqtol_SK_pre_row_" + "" + numSeqTolSKPremutations);
	// todo: Should only increase on valid input
	//var i = parseFloat(document.submitform.seqtol_SK_Boltzmann.value);
	//if (i != '0' && (i+'') != 'NaN')
	//{
	//	document.submitform.seqtol_SK_Boltzmann.value = parseFloat(i) + SK_BoltzmannIncrease;
	//}
	numSeqTolSKPremutations = numSeqTolSKPremutations + 1;
	if (numSeqTolSKPremutations >= SK_MaxPremutations)
	{
		new Effect.Fade("seqtol_SK_pre_addrow", { duration: 0.0 } );
	}
	return true;
}

//Adds a residue input field for Smith and Kortemme's Interface Sequence Plasticity Prediction
//todo: Add delete functionality
function addOneMoreChainSK()
{
	new Effect.Appear("seqtol_SK_chainrow_" + "" + numSeqTolSKChains);
	
	numSeqTolSKChains = numSeqTolSKChains + 1;
	if (numSeqTolSKChains >= SK_max_seqtol_chains)
	{
		  new Effect.Fade("seqtol_SK_addchain", { duration: 0.0 } );
	}
	return true;
}

//todo: Unused - delete
function writeRow( numbr ) 
{
    x = numbr + 1
    var s = '<td align="center">' + '' + x + '</td>';
    s = s + '<td align="center"><input type="text" name="PM_chain'  + '' + numbr + '" maxlength=1 SIZE=5 VALUE=""></td>';
    s = s + '<td align="center"><input type="text" name="PM_resid'  + '' + numbr + '" maxlength=4 SIZE=5 VALUE=""></td>';
    s = s + '<td align="center"><input type="text" name="PM_newres' + '' + numbr + '" maxlength=1 SIZE=2 VALUE=""></td>';
    s = s + '<td align="center"><input type="text" name="PM_radius' + '' + numbr + '" maxlength=4 SIZE=7 VALUE=""></td>';
    document.write(s);
    return true;
}

//todo: Unused - delete
function writeRowDEMO( numbr, chain, resid, newres, radius ) 
{
    x = numbr + 1
    var s = '<td align="center">' + '' + x + '</td>';
    s = s + '<td align="center"><input type="text" name="PM_chain'  + '' + numbr + '" maxlength=1 SIZE=5 VALUE="' + '' + chain + '"></td>';
    s = s + '<td align="center"><input type="text" name="PM_resid'  + '' + numbr + '" maxlength=4 SIZE=5 VALUE="' + '' + resid + '"></td>';
    s = s + '<td align="center"><input type="text" name="PM_newres' + '' + numbr + '" maxlength=1 SIZE=2 VALUE="' + '' + newres + '"></td>';
    s = s + '<td align="center"><input type="text" name="PM_radius' + '' + numbr + '" maxlength=4 SIZE=7 VALUE="' + '' + radius + '"></td>';
    document.write(s);
    addOneMore();
    return true;
}

/************************************
 * helper functions  END
 ************************************/

function confirm_delete(jobID)
{
  var r=confirm("Delete Job " + jobID + "?");
  if (r==true) {
    //document.write("You pressed OK!");
    window.location.href = "rosettaweb.py?query=delete&jobID=" + jobID + "&button=Delete" ; }
//  else {
//    window.location.href = "rosettaweb.py?query=queue" ; }
}

function reset_form ()
{
	document.submitform.reset();
	allWhite();
	reset_seqtolSKData();
}

function reset_seqtolSKData ()
{
	var oSubmitForm = document.forms["submitform"];
	
	// Premutations for design
	for (i = 0; i < minSeqTolSKPremutations; i++)
	{
		oSubmitForm.elements["seqtol_SK_pre_mut_c_" + i].value = "";
		new Effect.Appear( "seqtol_SK_pre_row_" + i, { duration: 0.0 } );
	}
	for (i = minSeqTolSKPremutations; i < SK_MaxPremutations; i++)
	{
		oSubmitForm.elements["seqtol_SK_pre_mut_c_" + i].value = "";
		new Effect.Fade( "seqtol_SK_pre_row_" + i, { duration: 0.0 } );
	}
	new Effect.Appear("seqtol_SK_pre_addrow");
	numSeqTolSKPremutations = minSeqTolSKPremutations;
	
	// Mutations for design
	for (i = 0; i < minSeqTolSKMutations; i++)
	{
		oSubmitForm.elements["seqtol_SK_mut_c_" + i].value = "";
		new Effect.Appear( "seqtol_SK_row_" + i, { duration: 0.0 } );
	}
	for (i = minSeqTolSKMutations; i < SK_MaxMutations; i++)
	{
		oSubmitForm.elements["seqtol_SK_mut_c_" + i].value = "";
		new Effect.Fade( "seqtol_SK_row_" + i, { duration: 0.0 } );
	}
	new Effect.Appear("seqtol_SK_addrow");
	numSeqTolSK = minSeqTolSKMutations;
	
	// Chains
	for (i = initNumSeqTolSKChains; i < SK_max_seqtol_chains; i++)
	{
		oSubmitForm.elements["seqtol_SK_chain" + i].value = "";
		new Effect.Fade( "seqtol_SK_chainrow_" + i, { duration: 0.0 } );
	}
	numSeqTolSKChains = initNumSeqTolSKChains;
	if (numSeqTolSKChains < SK_max_seqtol_chains)
	{
		new Effect.Appear("seqtol_SK_addchain");
	}
}

// Fills in sample data for the protocols when 'Load sample data' is clicked
function set_demo_values() 
{
	actual_task = getTask();
	
	if ( actual_task == 'parameter1_1')
	{
		document.submitform.PDBID.value = "1ABE";
		document.submitform.nos.value = "10";
		document.submitform.PM_chain.value = "A";
		document.submitform.PM_resid.value = "108";
		document.submitform.PM_newres.value = "L";
	}
	else if ( actual_task == 'parameter1_2') 
	{
		document.submitform.PDBID.value = "2PDZ";
		document.submitform.nos.value = "10";
		document.submitform.PM_chain0.value = "A";
		document.submitform.PM_resid0.value = "17";
		document.submitform.PM_newres0.value = "A";
		document.submitform.PM_radius0.value = "6.0";
		addOneMore();
		document.submitform.PM_chain1.value = "A";
		document.submitform.PM_resid1.value = "32";
		document.submitform.PM_newres1.value = "A";
		document.submitform.PM_radius1.value = "6.0";
		addOneMore();
		document.submitform.PM_chain2.value = "A";
		document.submitform.PM_resid2.value = "65";
		document.submitform.PM_newres2.value = "A";
		document.submitform.PM_radius2.value = "6.0";
		addOneMore();
		document.submitform.PM_chain3.value = "A";
		document.submitform.PM_resid3.value = "72";
		document.submitform.PM_newres3.value = "A";
		document.submitform.PM_radius3.value = "6.0";
		addOneMore();
	}
	else if ( actual_task == "parameter2_1")
	{
		document.submitform.PDBID.value = "1UBQ";
		document.submitform.nos.value = "10";  
	}
	else if ( actual_task == 'parameter2_2')
	{
		document.submitform.PDBID.value = "1UBQ";
		document.submitform.nos.value = "10";
		document.submitform.ENS_temperature.value = "1.2";
		document.submitform.ENS_num_designs_per_struct.value = "20";
		document.submitform.ENS_segment_length.value = "12";
	}
	else if ( actual_task == 'parameter3_1')
	{
		document.submitform.PDBID.value = "2PDZ";
		document.submitform.nos.value = "10";
		document.submitform.seqtol_chain1.value = "A";
		document.submitform.seqtol_chain2.value = "B";
		// document.submitform.seqtol_radius.value = "4.0";
		// document.submitform.seqtol_weight_chain1.value = "1";
		// document.submitform.seqtol_weight_chain2.value = "1";      
		// document.submitform.seqtol_weight_interface.value = "2";
		document.submitform.seqtol_mut_c_0.value = "B";
		document.submitform.seqtol_mut_r_0.value = "3";
		addOneMoreSeqtol();
		document.submitform.seqtol_mut_c_1.value = "B";
		document.submitform.seqtol_mut_r_1.value = "4";
		addOneMoreSeqtol();
		document.submitform.seqtol_mut_c_2.value = "B";
		document.submitform.seqtol_mut_r_2.value = "5";
		addOneMoreSeqtol();
		document.submitform.seqtol_mut_c_3.value = "B";
		document.submitform.seqtol_mut_r_3.value = "6";
		addOneMoreSeqtol();
	}
	else if ( actual_task == 'parameter3_2')
	{
		document.submitform.PDBID.value = "2PDZ";
		document.submitform.nos.value = "10";
		document.submitform.seqtol_SK_chain0.value = "A";
		document.submitform.seqtol_SK_chain1.value = "B";
		//todo: loop here over chains
		document.submitform.seqtol_SK_chain2.value = "";
		document.submitform.seqtol_SK_kP0P0.value = "0.4";
		document.submitform.seqtol_SK_kP1P1.value = "0.4";
		document.submitform.seqtol_SK_kP0P1.value = "1.0";
		//todo: loop here over chains
		//document.submitform.seqtol_SK_kC.value = "";
		//document.submitform.seqtol_SK_kAC.value = "";
		//document.submitform.seqtol_SK_kBC.value = "";
		//document.submitform.seqtol_SK_Boltzmann.value = SK_InitialBoltzmann;
		chainsChanged();
		reset_seqtolSKData();
	}
	return true;
}

/*
 todo: Delete
 disabled 
else if ( actual_task == 'upload_mutation') {
    document.submitform.nos.value = "10"
    
    document.submitform..value = "";
    document.submitform..value = "";
    document.submitform..value = "";

} */


// obsolete:

// function popUp( obj ) {
//     my_obj = document.getElementById(obj).style;
//     if ( my_obj.visibility == "visible" || my_obj.visibility == "show" ) {
//         my_obj.visibility = "hidden";
//     }
//     else { if ( my_obj.visibility == "hidden" ) {
//         my_obj.visibility = "visible";
//     }
//     }
// }

// todo: Delete
function popUp( obj ) {
    my_obj = document.getElementById(obj).style;
    offset=10
    if ( my_obj.visibility == "visible" || my_obj.visibility == "show" ) {
        my_obj.top  = e.clientY + offset;
        my_obj.left = e.clientX + offset*2;
        my_obj.visibility = "hidden";
    }
    else {
        my_obj.visibility = "visible";
    }
}





