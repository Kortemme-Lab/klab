
var numMPM = 0; // Multiple Point Mutations
var numSeqTol = 0; // Mutation SeqTol
var numSeqTolSK = 1; // Mutation SeqTolSK
var numSeqTolSKPremutations = 0; // Mutation SeqTolSK
const initNumSeqTolSKChains = 1;
const minSeqTolSKMutations = 1;
const minSeqTolSKPremutations = 0;
var numSeqTolSKChains = initNumSeqTolSKChains; // Initial number of chains for SeqTolSK
var subtask = 0;

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
        subtask = 0;
    }
	else if (query == "parsePDB")
	{
		Nifty("ul#about li","big fixed-height");
        Nifty("div#box","big transparent fixed-height");
		// todo: get this value (3,2) from the form
		subtask = 1;
		changeApplication(3, 2, 2 );
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

function isInteger(n)
{
	var integralExpression = /^[0-9]+$/;
	return n.match(integralExpression);
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
		elem.focus();
		elem.style.background="red";
		return false;
	}
}

function isCYS(elem)
{
	if(elem.value == "C")
	{
		alert("We are sorry but mutation to Cystein is not allowed.");
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


function isStoredPDB(str)
{
	var expr = /^[A-Za-z0-9]+\/[^\/\\]\.pdb$/i;
	return str.match(expr);		
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
		elem.focus();
		elem.style.background="red";
		return false;
	}
}

function checkIsEmpty(elem)
{
	return elem.value.length == 0;
}

function checkIsAlpha(v)
{
	var alphaExpression = /^[A-Za-z]+$/;
	if(v.match(alphaExpression))
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
	var sbmtform = document.submitform;
	var elems = sbmtform.elements;
	
	// return value - if false then we do not submit the job
	var ret = notEmpty(sbmtform.JobName);
	
	if (sbmtform.PDBComplex.value == "" && sbmtform.PDBID.value == "" && sbmtform.StoredPDB.value == "") 
    {
    	sbmtform.PDBComplex.style.background="red";
    	sbmtform.PDBID.style.background="red";
    	//alert("Please upload a structure or enter a PDB identifier.");
    	ret = false;
    }
    else 
    {
    	sbmtform.PDBComplex.style.background="white";
    	sbmtform.PDBID.style.background="white";
    }
	
	if ( sbmtform.PDBComplex.value == "" ) 
    {
		if ( sbmtform.StoredPDB.value != "" ) 
	    {
			ret = ret && isStoredPDB(sbmtform.StoredPDB.value);
	    }
		else if ( sbmtform.PDBID.value.length < 4 ) 
    	{
    		sbmtform.PDBID.style.background="red";
    		ret = false;
    	}
    	else
    	{
    		ret = ret && isPDB(sbmtform.PDBID);
    	}
    }
	
    if ( notEmpty(sbmtform.nos) && isNumeric(sbmtform.nos) ) 
    {
    	if ( sbmtform.task.value == "parameter3_2" )
    	{
    		// todo: These values (10, 100, 2, 50) should be set by Python to centralize them
    		// todo: min should be 10 but I've allowed 2 for testing
	    	if ( sbmtform.nos.value < 2 || sbmtform.nos.value > 100 ) 
	    	{
	    		sbmtform.nos.style.background="red";
	            ret = false;
	        }
    	}
    	else
    	{
	    	if ( sbmtform.nos.value < 2 || sbmtform.nos.value > 50 ) 
	    	{
	    		sbmtform.nos.style.background="red";
	            ret = false;
	        }
    	}
    }
    else 
    {
    	ret = false; 
    }
	
    if ( sbmtform.task.value == "parameter1_1" )
    {
    	ret = ret && (notEmpty(sbmtform.PM_chain)); 
    	ret = ret && (isAlpha(sbmtform.PM_chain));
    	ret = ret && (notEmpty(sbmtform.PM_resid)); 
    	ret = ret && (isNumeric(sbmtform.PM_resid));
    	ret = ret && (notEmpty(sbmtform.PM_newres));
    	ret = ret && (isAA(sbmtform.PM_newres));
    	ret = ret && (notEmpty(sbmtform.PM_radius));
    	ret = ret && (isNumeric(sbmtform.PM_radius));
    	if ( sbmtform.Mini.value == 'mini') {
    		ret = ret && (isCys(sbmtform.PM_newres));          
    	}
    }
    
    if ( sbmtform.task.value == "parameter1_2" ) {
    	var i=0;
    	for (i=0;i<=30;i=i+1) 
    	{
	        // check if row is empty
	        if ( isEmpty(elems['PM_chain' + '' + i].value) && 
	             isEmpty(elems['PM_resid' + '' + i].value) && 
	             isEmpty(elems['PM_newres'+ '' + i].value) && 
	             isEmpty(elems['PM_radius'+ '' + i].value) ) 
	        {
	           // break the loop
	           if ( i==0 ) 
	           {
	               ret = false;
	               elems['PM_chain' + '' + i].style.background="red";
	               elems['PM_resid' + '' + i].style.background="red";
	               elems['PM_newres'+ '' + i].style.background="red";
	               elems['PM_radius'+ '' + i].style.background="red";
	           }
	           break;
	        }
	        // if not empty, check if ALL values are entered correctly.
	        ret = ret && ( notEmpty(elems['PM_chain' + '' + i]));
	        ret = ret && ( isAlpha(elems['PM_chain' + '' + i]));
	        ret = ret && ( notEmpty(elems['PM_resid' + '' + i]));
	        ret = ret && ( isNumeric(elems['PM_resid' + '' + i]));
	        ret = ret && ( notEmpty(elems['PM_newres'+ '' + i]));
	        ret = ret && ( isAlpha(elems['PM_newres'+ '' + i]));
	        if ( sbmtform.Mini.value == 'mini' )
	        { 
	        	ret = ret && (isCys(elems['PM_newres' + '' + i]));
	        }
	        ret = ret && ( notEmpty(elems['PM_radius'+ '' + i]));
	        ret = ret && ( isNumeric(elems['PM_radius'+ '' + i]));
    	}
    }
    
    if ( sbmtform.task.value == "parameter2_2" ) 
    {
    	ret = ret && ( notEmpty(sbmtform.ENS_temperature) ); 
    	ret = ret && ( isNumeric(sbmtform.ENS_temperature) );
    	if ( parseFloat(sbmtform.ENS_temperature.value) < 0.0 || parseFloat(sbmtform.ENS_temperature.value) > 4.8) 
    	{ 
    		ret = false;  
    		sbmtform.ENS_temperature.style.background="red";
        }
    	ret = ret && ( notEmpty(sbmtform.ENS_num_designs_per_struct) ); 
    	ret = ret && ( isNumeric(sbmtform.ENS_num_designs_per_struct) );
    	ret = ret && ( notEmpty(sbmtform.ENS_segment_length) ); 
    	ret = ret && ( isNumeric(sbmtform.ENS_segment_length) );
    }
    
    if ( sbmtform.task.value == "parameter1_3" ) 
    {
    	ret = ret && ( notEmpty(sbmtform.Mutations) );
    }
    
    if ( sbmtform.task.value == "parameter3_1" ) 
    {
    	ret = ret && ( notEmpty( sbmtform.seqtol_chain1) );
    	ret = ret && ( isAlpha( sbmtform.seqtol_chain1) );
    	ret = ret && ( notEmpty( sbmtform.seqtol_chain2) );
    	ret = ret && ( isAlpha( sbmtform.seqtol_chain2) );
        // notEmpty( sbmtform.seqtol_weight_chain1, "Please enter a weight for Partner 1");
        // notEmpty( sbmtform.seqtol_weight_chain2, "Please enter a weight for Partner 2");
        // notEmpty( sbmtform.seqtol_weight_interface, "Please enter a weight for the interface") ;
        var i=0;
        for (i = 0; i <= HK_MaxMutations ; i = i + 1) 
        {
        	// check if row is empty
        	if ( elems['seqtol_mut_c_' + '' + i].value.length == 0 && elems['seqtol_mut_r_' + '' + i].value.length == 0 ) 
        	{
        		break;
        	}
        	ret = ret && ( notEmpty(elems['seqtol_mut_c_' + '' + i]));
        	ret = ret && ( isAlpha(elems['seqtol_mut_c_' + '' + i]));
        	ret = ret && ( notEmpty(elems['seqtol_mut_r_' + '' + i]));
        	ret = ret && ( isNumeric(elems['seqtol_mut_r_' + '' + i]));
        }
    }
    
    if ( sbmtform.task.value == "parameter3_2" ) 
    {       
    	// Highlight Partner 1 if no partners are specified
    	var allempty = true;
    	chainList = new Array();

    	// iterate through the displayed chains only
    	for (i = 0; i < numSeqTolSKChains ; i = i + 1) 
    	{
    		var c = elems["seqtol_SK_chain" + i];
    		var cval = c.value;
    		
    		var cIsEmpty = (cval.length == 0);
    		allempty = allempty && cIsEmpty;
    		
    		// require unique chain names
    		if (!cIsEmpty)
    		{
    			if (cval == "invalid")
    			{
    				markError(c);
    				ret = false;
    			}
    			else if (cval != "ignore" && chainList[cval])
    			{
    				markError(c);
    				ret = false;
    			}
    			chainList[cval] = true;
    		}
    	}
    	
    	if (allempty == true)
    	{
    		ret = ret && ( notEmpty( sbmtform.seqtol_SK_chain0) );
    		ret = ret && ( isAlpha ( sbmtform.seqtol_SK_chain0) );
    	}
    
    	// Highlight Boltzmann factor if missing or invalid
		if (!elems["customBoltzmann"].checked)
		{
			ret = ret && ( notEmpty( sbmtform.seqtol_SK_Boltzmann) );
			ret = ret && ( isNumeric ( sbmtform.seqtol_SK_Boltzmann) );
		}
		
		var validResidues = getValidResidues();
		var validPremutations = validResidues["premutated"]
		var validDesigned = validResidues["designed"]
		
   		// Highlight any invalid premutation rows
		for (i = 0; i < validPremutations.length; i++)
		{
			if (!validPremutations[i])
			{
				markError(elems['seqtol_SK_pre_mut_c_' + i]);
				markError(elems['seqtol_SK_pre_mut_r_' + i]);
				markError(elems['premutatedAA' + i]);
				ret = false;
	        }
		}
		// Highlight any invalid designed residue rows
		for (i = 0; i < validDesigned.length; i++)
		{
			if (!validDesigned[i])
			{
				markError(elems['seqtol_SK_mut_c_' + i]);
				markError(elems['seqtol_SK_mut_r_' + i]);
				ret = false;
	        }
		}
		// Require at least one designed residue
		if (validDesigned[-1] == 0) // if the number of valid designed residues is zero 
		{
			markError(elems['seqtol_SK_mut_c_0']);
			markError(elems['seqtol_SK_mut_r_0']);
			ret = false;
		}
                
        // Highlight any missing weights
        for (i = 0; i < SK_max_seqtol_chains ; i = i + 1) 
        {
        	for (j = i; j < SK_max_seqtol_chains ; j = j + 1) 
            {
        		var c = elems["seqtol_SK_kP" + i + "P" + j]; 
        		if (c.style.background == "white")
            	{
        			ret = ret && ( notEmpty(c));
        			ret = ret && ( isNumeric(c));
            	}	
            }
        }		
    }
    return ret;
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
}

function validChain(c)
{
	// todo: The use of this function by callers is pretty inefficient. Consider return an associative array of chains instead.
	// todo: Use PDB to determine validity of chain (pass pdb info from Python to JS)
	if (checkIsAlpha(c))
	{
		var elems = document.submitform.elements;
		for (i = 0 ; i < numSeqTolSKChains; i++)
		{
			if (elems["seqtol_SK_chain" + i].value == c)
			{
				return true;
			}
		}
	}
	return false;
}

function validResidueID(i)
{
	// todo: Use PDB to determine validity of chain (pass pdb info from Python to JS)
	return i != '' && isInteger(i);
}

// *** Sequence Tolerance *** 
// Returns an array of two arrays.
// The first array maps the displayed (numSeqTolSKPremutations) premutation indices to one of the values (true, false, "").
// 		true means that the premutation is valid (todo: check against actual PDB - at present we just check the syntax and existing chains)
//		false means that the premutation is invalid
//		-1 means that the premutation fields are empty
// The second array holds similar information for the designed residues
function getValidResidues()
{
	var validResidues = new Array();
	
	var premutated = new Array();
	var designed = new Array();
	
	var existingPremutations = new Array();
	var existingDesignedResidues = new Array();
	
	var i = 0;
	var numValidPremutations = 0;
	var numValidDesignedResidues = 0;
	var elems = document.submitform.elements;
	for (i = 0; i < numSeqTolSKPremutations ; i = i + 1) 
	{
		premutated[i] = false; 
		var chain = "" + elems["seqtol_SK_pre_mut_c_" + i].value.replace(/^\s+|\s+$/g, '');
		var resid = "" + elems["seqtol_SK_pre_mut_r_" + i].value.replace(/^\s+|\s+$/g, '');
		var AA = "" + elems["premutatedAA" + i].value;
        
		if (chain == "invalid" && resid == "" && AA.length != 3)
		{
			premutated[i] = -1;
		}
		else if (validChain(chain) && validResidueID(resid) && AA.length == 3)
		{
			if (!existingPremutations[chain+resid])
			{
				numValidPremutations = numValidPremutations + 1;
				premutated[i] = true; 
			}
			existingPremutations[chain+resid] = true;
		}
	}
	for (i = 0; i < numSeqTolSK ; i = i + 1) 
	{
		designed[i] = false; 
		var chain = "" + elems["seqtol_SK_mut_c_" + i].value.replace(/^\s+|\s+$/g, '');
		var resid = "" + elems["seqtol_SK_mut_r_" + i].value.replace(/^\s+|\s+$/g, '');
		
		if (chain == "invalid" && resid == "")
		{
			designed[i] = -1;
		}
		else if (validChain(chain) && validResidueID(resid))
		{
			if (!existingDesignedResidues[chain+resid])
			{
				numValidDesignedResidues = numValidDesignedResidues + 1;
				designed[i] = true; 
			}
			existingDesignedResidues[chain+resid] = true;
		}
	}
	premutated[-1] = numValidPremutations
	designed[-1] = numValidDesignedResidues
	validResidues["premutated"] = premutated
	validResidues["designed"] = designed
	return validResidues;
}

function updateBoltzmann()
{
	if (document.submitform.elements["customBoltzmann"].checked)
	{
		var validPremuations = getValidResidues()["premutated"]
       	document.submitform.seqtol_SK_Boltzmann.value = SK_InitialBoltzmann + validPremuations[-1] * SK_BoltzmannIncrease;
	}
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
			//todo: test this
			alert("here")
			var integralExpression = /^[0-9]+$/;
						
			var tds = document.getElementsByTagName("td");
			for (j = 0; j < tds.length; j++)
			{
				var cn = tds[j].className;
				if (cn && cn.indexOf("seqtol_SK_kP") == 0)
				{
					var idx = cn.substring(11);
					if (isInteger(idx))
					{
						idx = parseInt(idx);
						//columnElements[][]
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
				// todo: Could optimize this by asking for elements of table rather than document
				columnElements[i] = document.getElementsByClassName("seqtol_SK_kP" + i)
			}
		}
	}
}

// todo: deprecated
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

// todo: deprecated
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
	if (checkIsAlpha(c.value))
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
	var numvalidchains = 0;
	for (i = 0; i < SK_max_seqtol_chains ; i = i + 1)
	{
		var c = document.submitform.elements["seqtol_SK_chain" + i];
		var invalid = checkIsEmpty(c) || (c.value.length > 1) || !checkIsAlpha(c.value);
		chainIsInvalid[i] = invalid;
		if (!invalid)
		{
			numvalidchains = numvalidchains + 1;
			if (i > highestValidChain)
			{
				highestValidChain = i;
			}
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
			new Effect.Appear( 'seqtol_SK_weight_' + i, { duration: 0.0 } ) ;
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
	
	if ((numSeqTolSKChains > 1) && ((chainIsInvalid[0] && numvalidchains > 0) || (numvalidchains >= 2)))
	{
		Effect.Appear("seqtol_SK_IEHeader", { duration: 0.0 } );
	}
	else
	{
		Effect.Fade("seqtol_SK_IEHeader", { duration: 0.0 } );
	}
	updateBoltzmann();
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

// todo: These two functions are similar. Parameterize them on the classname and handle extras (UploadedPDB)
function showGeneralSettings(visible)
{
	//todo: may not work on all browsers - test
	nonPDBelems = document.getElementsByClassName("PostPDBSubmission")
	// Display the general section
	if (visible)
	{
		for (var k = 0; k < nonPDBelems.length; k++)
		{
			new Effect.Appear( nonPDBelems[k] , { duration: 0.5, queue: { scope: 'task' } });
		}
	}
	else
	{
		//todo: may not work on all browsers - test
		for (var k = 0; k < nonPDBelems.length; k++)
		{
			new Effect.Fade( nonPDBelems[k] , { duration: 0.0 } );
		}	
	}
}


function showPDBUploadElements(visible)
{
	//todo: may not work on all browsers - test
	PDBelems = document.getElementsByClassName("PDBSelector")

	// Display the PDB uploading section
	if (visible)
	{
		for (var k = 0; k < PDBelems.length; k++)
		{
			new Effect.Appear( PDBelems[k] , { duration: 0.0 } );
		}
		new Effect.Fade('UploadedPDB' , { duration: 0.0 } );
		// todo: Hacky special case. This can be tidied up when all protocols use the preuploading
		if (document.submitform.task.value != 'parameter3_2')
		{
			new Effect.Fade( "SKSpecial", { duration: 0.0} )
		}
		else
		{
			new Effect.Appear( "SKSpecial", { duration: 0.0} )
		}
	}
	else
	{
		//todo: may not work on all browsers - test
		for (var k = 0; k < PDBelems.length; k++)
		{
			new Effect.Fade( PDBelems[k] , { duration: 0.0 } );
		}	
		new Effect.Appear('UploadedPDB' , { duration: 0.0 } );
		new Effect.Fade( "SKSpecial", { duration: 0.0} )
	}
}

// This function shows the input form for the protocol <_task> of protocol series <app>.
// This includes a logo and parameter fields for the protocol.
// The _override parameter is used for the demo data 
function changeApplication( app, _task, _extra, _override ) {

	// Clear all form fields
	var elems = document.submitform.elements;
	var numPartners = elems["numPartners"].value
	
	// Remember any persistent fields here
	persistent = new Array("JobName", "nos");
	previousValues = new Array();
	for (var i= 0; i < persistent.length; i++ ) 
	{
		k = persistent[i];
		v = elems[k].value;
		if (v != '')
		{
			previousValues[k] = v;
		}
	}
	
	// White out the form
	document.submitform.reset();
	allWhite();
	
	// Recover any persistent fields now
	for (var k in previousValues) 
	{
		if (elems[k])
		{
			//alert(previousValues[k]);
			elems[k].value = previousValues[k];
		}
	}
	
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
	
	// Display the PDB uploading section
	if (task != 'parameter3_2')
	{
		subtask = 0;
	}
	else
	{
		elems["numPartners"].value = numPartners
	}
	
	showPDBUploadElements(subtask == 0);
	showGeneralSettings(task != 'parameter3_2' || subtask != 0);
	
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
	
	if ( task == 'parameter3_2' )
	{ 
		if (subtask == 0)
		{
			new Effect.Fade( "parameter3_2_header" );
			new Effect.Fade( "parameter3_2_body", { duration: 0.0} );
		}
		else if (subtask == 1)
		//todo: check load demo values if (!_override && (!_extra || document.getElementById("parameter3_2_header").style.display == "none"))
		{
			new Effect.Appear( "parameter3_2_header" );		
			new Effect.Fade( "parameter3_2_body", { duration: 0.0} );
			document.submitform.nos.value = RecommendedNumStructuresSeqTolSK;
		}
		else if (subtask == 2)
		{
			//new Effect.Fade( "parameter3_2_header", { duration: 0.0} );		
			
			var i;
			if (_extra < initNumSeqTolSKChains)
			{
				_extra = initNumSeqTolSKChains;
			}
			for (i = 0; i < _extra; i++)
			{
				new Effect.Appear("seqtol_SK_chainrow_" + "" + i);
			}
			for (; i < SK_max_seqtol_chains; i++)
			{
				new Effect.Fade("seqtol_SK_chainrow_" + "" + i, { duration: 0.0} );
			}
			numSeqTolSKChains = _extra
			//todo: seqtol_SK_addchain seems deprecated now
			new Effect.Fade("seqtol_SK_addchain", { duration: 0.0 } );
			
			if (!_override)
			{
				chainsChanged();
				reset_seqtolSKData();
			}
		  	document.submitform.Mini[0].disabled=true;
		    document.submitform.Mini[0].checked=false;
		    document.submitform.Mini[1].disabled=false;
		    document.submitform.Mini[1].checked=true;
		    document.getElementById('rv0').style.color='#D8D8D8';
		    document.getElementById('rv1').style.color='#000000';
			new Effect.Appear( "parameter3_2_body" );			
		}
		new Effect.Appear( "ref4" ); 	    
	    //new Effect.Fade("seqtol_SK_addrow", { duration: 0.0 } );
		new Effect.Fade( "recNumStructures", { duration: 0.0 } );
		new Effect.Appear( "recNumStructuresSeqTolSK" );
	}
	else 
	{ 
		new Effect.Appear( "recNumStructures" );
		new Effect.Fade( "recNumStructuresSeqTolSK", { duration: 0.0 } );
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
	chainsChanged();
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
		//new Effect.Fade( "seqtol_SK_chainrow_" + i, { duration: 0.0 } );
	}
	//numSeqTolSKChains = initNumSeqTolSKChains;
	if (numSeqTolSKChains < SK_max_seqtol_chains)
	{
		//new Effect.Appear("seqtol_SK_addchain");
	}
}

// Fills in sample data for the protocols when 'Load sample data' is clicked
function set_demo_values() 
{
	actual_task = getTask();
	
	if ( actual_task == 'parameter1_1')
	{
		document.submitform.PDBID.value = "1ABE";
		document.submitform.nos.value = RecommendedNumStructures;
		document.submitform.PM_chain.value = "A";
		document.submitform.PM_resid.value = "108";
		document.submitform.PM_newres.value = "L";
	}
	else if ( actual_task == 'parameter1_2') 
	{
		document.submitform.PDBID.value = "2PDZ";
		document.submitform.nos.value = RecommendedNumStructures;
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
		document.submitform.nos.value = RecommendedNumStructures;  
	}
	else if ( actual_task == 'parameter2_2')
	{
		document.submitform.PDBID.value = "1UBQ";
		document.submitform.nos.value = RecommendedNumStructures;
		document.submitform.ENS_temperature.value = "1.2";
		document.submitform.ENS_num_designs_per_struct.value = "20";
		document.submitform.ENS_segment_length.value = "12";
	}
	else if ( actual_task == 'parameter3_1')
	{
		document.submitform.PDBID.value = "2PDZ";
		document.submitform.nos.value = RecommendedNumStructures;
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
		reset_seqtolSKData();
		subtask = 2
		changeApplication(3, 2, 2, true);
		document.submitform.StoredPDB.value = '';
	    document.submitform.PDBID.value = "2PDZ";
	    showPDBUploadElements(true);
		document.submitform.nos.value = RecommendedNumStructuresSeqTolSK;
		
		elemA = document.submitform.seqtol_SK_chain0
		elemB = document.submitform.seqtol_SK_chain1
		elemNumPartners = document.submitform.numPartners
		// todo: Fix this up using an array
		for (i = elemA.length; i >= 0; i--)
		{
			elemA.options[i] = null;
		}
		for (i = elemB.length; i >= 0; i--)
		{
			elemB.options[i] = null;
		}
		for (i = elemNumPartners.length; i >= 0; i--)
		{
			elemNumPartners.options[i] = null;
		}
		elemA.options[0] = new Option('A','A')
		elemB.options[0] = new Option('B','B')
		elemNumPartners.options[0] = new Option('2 Partners (Interface)','2')
		elemA.value = "A";
		elemA.value = "B";
		//todo: loop here over residues and add choices for A and B
		
		//todo: loop here over chains
		//document.submitform.seqtol_SK_chain2.value = "";
		document.submitform.seqtol_SK_kP0P0.value = "0.4";
		document.submitform.seqtol_SK_kP1P1.value = "0.4";
		document.submitform.seqtol_SK_kP0P1.value = "1.0";
		//todo: loop here over chains
		//document.submitform.seqtol_SK_kC.value = "";
		//document.submitform.seqtol_SK_kAC.value = "";
		//document.submitform.seqtol_SK_kBC.value = "";
		//document.submitform.seqtol_SK_Boltzmann.value = SK_InitialBoltzmann;
		chainsChanged();
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





