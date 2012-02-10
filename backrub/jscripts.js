/*******************************************************************************
 * Constants and globals Note: some constants are passed in by rosettahtml.py
 ******************************************************************************/

// Constants used by validation functions
var integralExpression 	= /^-*[0-9]+$/; // const
var numericExpression 	= /^([0-9]+[\.]*[0-9]*|[0-9]*[\.]*[0-9]+)$/; // const
var alphaExpression 		= /^[A-Za-z]+$/; // const
var chainExpression 		= /^[A-Za-z]$/; // const
var emptyExpression 		= /^\s*$/; // const
var PDBExpression 		=   /^[@]?[-()\sA-Z_a-z0-9]+$/; // const
var StoredPDBExpression 	= /^pdbs\/[-()\sA-Z_a-z0-9\/]+[^\.]+\.pdb$/i; // const
var CysteineExpression 	= /^CYS$/i; // const
var CysteinMutationError = "We are sorry but mutation to Cysteine is not allowed in Rosetta 3." // const

/* Protocol variables */
// Multiple Point Mutations
var numMPM = 1;

// SeqTolHK
var numSeqTol = 1;	// Mutations

// SeqTolSK
var numSeqTolSK = 1; // Mutations
var numSeqTolSKPremutations = 0; // Premutations
var initNumSeqTolSKChains = 1; // const
var numSeqTolSKChains = initNumSeqTolSKChains; // Initial number of chains
var columnElements;
var minSeqTolSKMutations = 1; // const
var minSeqTolSKPremutations = 0; // const

// SeqTolSK
var numSeqTolSKMultiPremutations = 0; // Premutations
var minSeqTolSKMultiPremutations = 0; // const


// An array of validation functions for the protocols
protocolValidators = 
[ 
	[validateOneMutation, validateMultipleMutations],
	[validateEnsemble, validateEnsembleDesign],
	[validateSeqtolHK, validateSeqtolSK],
	[validateSeqtolSKMulti]
]

// An array of functions to set demo values for the protocols
setDemoValues = 
[ 
	[demoOneMutation, demoMultipleMutations],
	[demoEnsemble, demoEnsembleDesign],
	[demoSeqtolHK, demoSeqtolSK],
	[demoSeqtolSKMulti]
]

otherParameterForms = ["parameterSeqtolSK"]

// An array of functions to handle protocol-specific GUI setup
var numSubTasks = 3; // const
function noop(app, task, extra){}
additionalGUISetup = new Array(protocolTasks.length)
for (var i = 0; i < protocolTasks.length; i++)
{
	additionalGUISetup[i] = new Array(protocolTasks[i])
	for (var j = 0; j < protocolTasks[i]; j++)
	{
		additionalGUISetup[i][j] = new Array(numSubTasks)
		for (var k = 0; k < numSubTasks; k++)
		{
			additionalGUISetup[i][j][k] = noop
		}
	}
}

// IE fix for extra protocols on test server
additionalGUISetup[3] = [[noop]]
// Additional GUI setup
function showMutationRowAdder(app, task, extra)
{
	new Effect.Appear("addmrow_" + app + "_" + task, { duration: 0.0 } );
}
additionalGUISetup[2][1][1] = changeApplicationToSeqtolSK1
additionalGUISetup[2][1][2] = changeApplicationToSeqtolSK2
additionalGUISetup[3][0][1] = changeApplicationToSeqtolSK1
additionalGUISetup[3][0][2] = changeApplicationToSeqtolSK2
additionalGUISetup[0][1][1] = showMutationRowAdder
additionalGUISetup[2][0][1] = showMutationRowAdder

/*******************************************************************************
 * Main functions
 ******************************************************************************/
var localquery = 0;

function startup(query)
{
	// Round the corners using Nifty
	if (query == "submit" || query == "submitted") 
	{
		Nifty("ul#about li","big fixed-height");
        Nifty("div#box","big transparent fixed-height");
    }
	else if (query == "parsePDB")
	{
		Nifty("ul#about li","big fixed-height");
        Nifty("div#box","big transparent fixed-height");
		protocol = getProtocol();
		changeApplication(protocol[0], protocol[1], 1, 2 );
	}	 
	else if (query == "sampleData")
	{
		localquery = query;
		Nifty("ul#about li","big fixed-height");
        Nifty("div#box","big transparent fixed-height");
		protocol = getProtocol();
		// @js1: Special case for sequence tolerance. Generalize and fix this
		// i.e. "jump to last stage"
		if (protocol[0] == 2 && protocol[1] == 1)
		{
			changeApplication(protocol[0], protocol[1], 2, 2, true );
		}
		else if (protocol[0] == 3 && protocol[1] == 0)
		{
			changeApplication(protocol[0], protocol[1], 2, 2, true );
		}
		else
		{
			changeApplication(protocol[0], protocol[1], 1, 2 );
		}
		set_demo_values(true);
	}	 
	else if (query == "index" || query == "login") 
    {
		Nifty("div#login_box","big transparent fixed-height");
		//todo: test this on the testserver to conditionally change div and use the same logic above to fix JS errors alert(document.getElementsByName("news_box_good"));
		//Nifty("div#news_box_good","big transparent fixed-height");
    }
	else if (query == "queue" ) 
    {
    	Nifty("div#queue_bg","big transparent fixed-height");
    }
	else if (query == "jobinfo") 
    {
    	Nifty("div#jobinfo","big transparent fixed-height");
    }
}

function changeSubApplication(subtask, extra, override )
{
	proto = getProtocol()
	changeApplication( proto[0], proto[1], subtask, extra, override );
}

// This function shows the input form for the protocol <_task> of protocol
// series <app>.
// This includes a logo and parameter fields for the protocol.
// The _override parameter is used for the demo data
function changeApplication( app, task, subtask, extra, override ) 
{
	// Reset to the start on protocol change
	if (!isProtocol(app, task) || subtask == undefined)
	{
		subtask = 0;
	}
	
	// Clear all form fields
	clearFormFields()

	// Set the form's protocol values
	setProtocol(app, task);

	// Show the specific message for point mutations
	if (app == 0)
	{
		new Effect.Appear( "pointMutationRecommendation", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
	}
	else
	{
		new Effect.Fade( "pointMutationRecommendation", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
	}
	
	// Hide the descriptions of the protocol series and the descriptions of
	// other protocol tasks
	thistask = hideInactiveProtocols(app, task);
		
	// Hide the common submission page text
	new Effect.Fade( "textintro", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
		
	// Fix up the default Rosetta versions for the different protocols and hide
	// non-applicable versions
	revisionFields = document.getElementsByClassName("bin_revisions");
	showRevisions = new Array(); 
	for ( i = 0; i < protocolBins[app][task].length; i++ )
	{
		showRevisions['rv' + protocolBins[app][task][i]] = true;
	}
	for ( i = 0; i < revisionFields.length; i++ )
	{
		if (showRevisions[revisionFields[i].id])
		{
			new Effect.Appear(revisionFields[i], { duration: 0.0, queue: { position: '0', scope: 'task' } });
		}
		else
		{
			new Effect.Fade(revisionFields[i], { duration: 0.0, queue: { position: '0', scope: 'task' } });
		}
	}
	
	// Display the PDB uploading section
	// Show the HTML elements for entering parameters and submitting the form
	showCommonElements(subtask);
	
	// Select the default binary (which should be defined as position 0)
	var miniGroup = document.submitform.Mini
	for (var i = 0; i < miniGroup.length; i++)
	{
		if (miniGroup[i].value == protocolBins[app][task][0])
		{
			miniGroup[i].checked = true;
			miniGroup[i].onchange();		// Set the MiniVersion form value
		}
	}
	
	// Display the GUI elements based on the subtask
	if (subtask == 0)
	{
		// Set the default number of structures
		document.submitform.nos.value = protocolNos[app][task][1];
		setSubmissionButtonsVisibility(false);
		new Effect.Fade( thistask + "_step1" );
		new Effect.Fade( thistask + "_step2", { duration: 0.0} );
		
		runningSeqtolSK = isProtocol(2, 1) || isProtocol(3, 0);
		if (runningSeqtolSK)
		{
			new Effect.Fade( "parameterSeqtolSK_step1", { duration: 0.0, queue: { scope: 'task' }} );		
			new Effect.Fade( "parameterSeqtolSK_step2", { duration: 0.0, queue: { scope: 'task' }} );
		}

	}
	else if (subtask == 1)
	{
		setSubmissionButtonsVisibility(true);
		additionalGUISetup[app][task][1](app, task, [extra, override])
		new Effect.Appear( thistask + "_step1", { duration: 0.0, queue: { scope: 'task' }} );		
		new Effect.Fade(   thistask + "_step2", { duration: 0.0, queue: { scope: 'task' }} );
	}
	if (subtask == 2)
	{ 
		additionalGUISetup[app][task][2](app, task, [extra, override])
		new Effect.Appear( thistask + "_step2" );
	}
}

function setSubmissionButtonsVisibility(visible)
{
	submissionButtons = document.getElementsByClassName("allStepsShown");
	for ( i = 0; i < submissionButtons.length; i++ )
	{
		if (visible)
		{
			new Effect.Appear(submissionButtons[i], { duration: 0.0, queue: { position: '0', scope: 'task' } });
		}
		else
		{
			new Effect.Fade(submissionButtons[i], { duration: 0.0, queue: { position: '0', scope: 'task' } });
		}
	}
}
// This function shows the preliminary screen for each protocol series.
// This includes a logo and descriptive text but no input form.
function showMenu( menu_id ) {
	
	document.submitform.reset();
	/* This function extends or hides the menu on the left */	

	// box contains the pici, texti, common parameters, parameteri_j, parameter
	// submission, and refi elements where i = menu_id
	// Essentially, it is the right column in the description (resp. submission
	// pages) for protocol series (resp. protocols)
	// Set the color as above and the minimum height.
	mycolor = colors[menu_id];
	document.getElementById("box").style.background = mycolor;
	document.getElementById("box").style.minHeight = document.getElementById("columnLeft").style.offsetHeight;
	Nifty("div#box","big transparent fixed-height");
	  
	// Hide the common submission page text
	new Effect.Fade( "textintro", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
	  
	// Display any elements pic and text suffixed with menu_id and hide all
	// others
	for ( i = 0; i < protocolTasks.length; i++ )
	{
		if (i == menu_id)
		{
			// This will display the logo and descriptive text.
			new Effect.Appear( "pic"  + i);
			new Effect.Appear( "text" + i);
		}
		else
		{
			new Effect.Fade( "pic"  + i, { duration: 0.0, queue: { position: '0', scope: 'task' } } );
			new Effect.Fade( "text" + i, { duration: 0.0, queue: { position: '0', scope: 'task' } } );
		}			

		for ( j = 0; j < protocolTasks[i]; j++ )
		{
			// Hide all reference elements
			new Effect.Fade( "ref" + i + "_" + j, { duration: 0.0, queue: { position: '0', scope: 'task' } } );
			new Effect.Fade( "parameter" + i + "_" + j, {duration: 0.0, queue: {position: '0', scope: 'parameter'} } );
		}
	}
	
	// Hide all other parameter fields (used on the submission pages)
	parameterDivs = new Array("PrePDBParameters", "PostPDBParameters", "parameter_submit");
	for ( i = 0; i < parameterDivs.length; i++ )
	{
		new Effect.Fade( parameterDivs[i], {duration: 0.0, queue: {position: '0', scope: 'parameter'} } );
	}
	for (i = 0; i < otherParameterForms.length; i++)
	{
		new Effect.Fade( otherParameterForms[i], {duration: 0.0, queue: {position: '0', scope: 'parameter'} } );
	}
	     
	return true;
}

function ValidateForm()
{
	allWhite();
	var sbmtform = document.submitform;
	var elems = sbmtform.elements;
	protocol = getProtocol();
	pgroup = protocol[0];
	ptask = protocol[1];

	// return value - if false then we do not submit the job
	var ret
	
	// Check the job name
	ret = validateNotEmpty(sbmtform.JobName);
	
	// Check that a PDB has been uploaded
	if (sbmtform.PDBComplex.value == "" && sbmtform.PDBID.value == "" && sbmtform.StoredPDB.value == "") 
    {
    	sbmtform.PDBComplex.style.background="red";
    	sbmtform.PDBID.style.background="red";
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
			ret = !!checkValue(sbmtform.StoredPDB.value, StoredPDBExpression) && ret;
	    }
		else if ( sbmtform.PDBID.value.length < 4 ) 
    	{
			sbmtform.PDBID.style.background="red";
    		ret = false;
    	}
    	else
    	{
    		if (sbmtform.PDBID.value.length != 4 && sbmtform.PDBID.value[0] != '@')
			{
    			sbmtform.PDBID.style.background="red";
        		alert("Invalid PDB ID " + sbmtform.PDBID.value + ". Please try uploading the file again.");
    			ret = false;
			}
    		ret = validateElem(sbmtform.PDBID, PDBExpression) && ret;
    	}
    }
	
	// Check the number of structures
    if ( validateElem(sbmtform.nos, integralExpression) ) 
    {
    	minNos = protocolNos[pgroup][ptask][0];
    	maxNos = protocolNos[pgroup][ptask][2];                   	                               		
    	if ( sbmtform.nos.value < minNos || sbmtform.nos.value > maxNos ) 
    	{
    		sbmtform.nos.style.background="red";
            ret = false;
        }
    }
    else 
    {
    	ret = false; 
    }
	ret = protocolValidators[pgroup][ptask]() && ret;
	return ret;
}

function checkPassword()
{
	mform = document.myForm;
	if (mform.confirmpassword.value == "")
	{
		mform.password.style.background = "#ffffff";
		mform.confirmpassword.style.background = "#ffffff";
	}
	else if ( mform.password.value == mform.confirmpassword.value  )
	{
		mform.password.style.background = "#77ff77"
		mform.confirmpassword.style.background = "#77ff77"
	}
	else
	{
		mform.password.style.background = "#ff5555"
		mform.confirmpassword.style.background = "#ff5555"
	}
}

function validateEmail()
{
	f = document.myForm.email
	str = f.value.replace(/^\s+|\s+$/g, '');	// strip trailing and leading whitespace
	ati = str.indexOf("@")
	doti = str.lastIndexOf(".")
	isValid = !(ati == -1 || doti == -1 || str.length < 6 || doti - 1 <= ati);
	if (!isValid)
	{
		f.style.background = "#ff5555";
	}
	else
	{
		f.style.background = "#ffffff";
	}
	return isValid;
}

function ValidateFormRegister()
{ 
	mform = document.myForm
	if (mform.username.value 		== "" ||
		mform.firstname.value 		== "" ||
		mform.lastname.value 		== "" ||
		mform.password.value 		== "" ||
		mform.confirmpassword.value == "" ||
		mform.city.value 			== "" ||
		mform.country.value 		== "")
	{
		alert("Please complete all required fields.");
		return false;
	}
	if (!validateEmail(mform.email.value))
	{
		alert("Your email address is not valid.");
		return false;
	}
	if ( mform.password.value != mform.confirmpassword.value  )
	{
		alert("Your password does not match your password confirmation.");
		return false;
	}
	return true;
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

// Fills in sample data for the protocols when 'Load sample data' is clicked
function set_demo_values(setAllData) 
{
	protocol = getProtocol();
	pgroup = protocol[0];
	ptask = protocol[1];
	
	document.submitform.nos.value = protocolNos[pgroup][ptask][1];
	setDemoValues[pgroup][ptask](setAllData)
	// return true;
}

/*******************************************************************************
 * Protocol-specific functions
 ******************************************************************************/

/*
 * All protocol-specific functions are defined here. Define at least the
 * validator and demo value setter
 */

/*******************************************************************************
 * Protocol-specific functions - Point Mutation
 ******************************************************************************/

function validateOneMutation()
{
    ret = true;
    var sbmtform = document.submitform;
		
	if (sbmtform.PM_chain.value == "invalid")
    {
    	ret = false;
    	sbmtform.PM_chain.style.background="red";
    }

	if ( usingMini() && validateElem(sbmtform.PM_newres, CysteineExpression))
	{
		alert(CysteinMutationError);
		ret = false;
	}
    
	ret = validateElem(sbmtform.PM_resid, integralExpression) && ret;
	ret = validateElem(sbmtform.PM_newres, alphaExpression) && ret;
	ret = validateElem(sbmtform.PM_radius, numericExpression) && ret;

    return ret;
}

function demoOneMutation(setAllData)
{
	var sbmtform = document.submitform;
	sbmtform.PDBID.value = "1ABE";
	sbmtform.PM_chain.value = "A";
	sbmtform.PM_resid.value = "108";
	sbmtform.PM_newres.value = "LEU";
	sbmtform.JobName.value = "One Mutation sample job"
}

/*******************************************************************************
 * Protocol-specific functions - Multiple Mutations
 ******************************************************************************/

function validateMultipleMutations()
{
	ret = true;
	var sbmtform = document.submitform;
	var elems = sbmtform.elements;
	
	for (var i = 0 ; i < numMPM ; i = i + 1) 
	{
		chain = elems['PM_chain' + i];
		resid = elems['PM_resid' + i];
		newres = elems['PM_newres' + i];
		radius = elems['PM_radius' + i];
		
		// break the loop on the first empty row (the radius is filled in
		// automatically and not checked)
        if ((chain.value == "invalid") && (resid.value.length == 0) && (newres.value.length == 0)) 
        {
           if ( i == 0 ) 
           {   
        	   ret = false;
               chain.style.background="red";
               resid.style.background="red";
               newres.style.background="red";
               radius.style.background="red";
           }
           break;
        }

        // if not empty, check if ALL values are entered correctly.=, including
		// the radius
        if (chain.value == "invalid")
        {
        	ret = false;
        	chain.style.background="red";
        }    	
    	
    	if ( usingMini() && validateElem(newres, CysteineExpression))
    	{
    		alert(CysteinMutationError);
    		ret = false;
    	}
    	
        ret = validateElem(resid, integralExpression) && ret;
        ret = validateElem(newres, alphaExpression) && ret;
        ret = validateElem(radius, numericExpression) && ret;
	}
	return ret;
}

function demoMultipleMutations(setAllData)
{
	var sbmtform = document.submitform;
	sbmtform.PDBID.value = "2PDZ";
	if (numMPM == 1) // This prevents new fields appearing if a user hits
						// load sample data when the sample data has already
						// been loaded
	{
		sbmtform.PM_chain0.value = "A";
		sbmtform.PM_resid0.value = "17";
		sbmtform.PM_newres0.value = "ALA";
		sbmtform.PM_radius0.value = "6.0";
		addOneMore();
		sbmtform.PM_chain1.value = "A";
		sbmtform.PM_resid1.value = "32";
		sbmtform.PM_newres1.value = "ALA";
		sbmtform.PM_radius1.value = "6.0";
		addOneMore();
		sbmtform.PM_chain2.value = "A";
		sbmtform.PM_resid2.value = "65";
		sbmtform.PM_newres2.value = "ALA";
		sbmtform.PM_radius2.value = "6.0";
		addOneMore();
		sbmtform.PM_chain3.value = "A";
		sbmtform.PM_resid3.value = "72";
		sbmtform.PM_newres3.value = "ALA";
		sbmtform.PM_radius3.value = "6.0";
		addOneMore();
	}
	sbmtform.JobName.value = "Multiple Mutations sample job"
}

/*******************************************************************************
 * Protocol-specific functions - Backrub Conformational Ensemble
 ******************************************************************************/

function validateEnsemble()
{
	return true;
}

function demoEnsemble(setAllData)
{
	var sbmtform = document.submitform;
	sbmtform.PDBID.value = "1UBQ";
	sbmtform.JobName.value = "Backrub Conformational Ensemble sample"
}

/*******************************************************************************
 * Protocol-specific functions - Backrub Ensemble Design
 ******************************************************************************/

function validateEnsembleDesign()
{
	ret = true;
	var sbmtform = document.submitform;
	var elems = sbmtform.elements;
	
	ret = validateElem(sbmtform.ENS_temperature, numericExpression) && ret
	if (ret && parseFloat(sbmtform.ENS_temperature.value) < 0.0 || parseFloat(sbmtform.ENS_temperature.value) > 4.8) 
	{ 
		ret = false;  
		sbmtform.ENS_temperature.style.background="red";
    }
	ret = validateElem(sbmtform.ENS_num_designs_per_struct, integralExpression) && ret
	ret = validateElem(sbmtform.ENS_segment_length, numericExpression) && ret
	return ret;
}   

function demoEnsembleDesign(setAllData)
{
	var sbmtform = document.submitform;
	sbmtform.PDBID.value = "1UBQ";
	sbmtform.ENS_temperature.value = "1.2";
	sbmtform.ENS_segment_length.value = "12";
	sbmtform.ENS_num_designs_per_struct.value = "20";
	sbmtform.JobName.value = "Backrub Ensemble Design sample job"
}

/*******************************************************************************
 * Protocol-specific functions -Sequence Tolerance HK
 ******************************************************************************/

function validateSeqtolHK()
{
	ret = true;
	var sbmtform = document.submitform;
	var elems = sbmtform.elements;
	
	ret = validateElem(sbmtform.seqtol_chain1, chainExpression) && ret;
	ret = validateElem(sbmtform.seqtol_chain2, chainExpression) && ret;
	
	// validateNotEmpty( sbmtform.seqtol_weight_chain1, "Please enter a weight
	// for Partner 1");
    // validateNotEmpty( sbmtform.seqtol_weight_chain2, "Please enter a weight
	// for Partner 2");
    // validateNotEmpty( sbmtform.seqtol_weight_interface, "Please enter a
	// weight for the interface") ;
	
	for (var i = 0; i < HK_MaxMutations ; i = i + 1) 
    {
    	chain = elems['seqtol_mut_c_' + '' + i];
    	resid = elems['seqtol_mut_r_' + '' + i];
    	
    	// check if row is empty
    	if ( chain.value == "invalid" && validateEmptyElem(resid)) 
    	{
    		break;
    	}
    	
    	ret = validateElem(chain, chainExpression) && ret;
    	ret = validateElem(resid, integralExpression) && ret;
    }
    
	
	var validResidues = getValidResidues();
	var validDesigned = validResidues["designed"]
	// Highlight any invalid designed residue rows
	for (i = 0; i < validDesigned.length; i++)
	{
		if (!validDesigned[i])
		{
			markError(elems['seqtol_mut_c_' + i]);
			markError(elems['seqtol_mut_r_' + i]);
			ret = false;
        }
	}
	// Require at least one designed residue
	if (validDesigned[-1] == 0) // if the number of valid designed residues is
								// zero
	{
		markError(elems['seqtol_mut_c_0']);
		markError(elems['seqtol_mut_r_0']);
		ret = false;
	}
	

	return ret;
}

function demoSeqtolHK(setAllData)
{
	var sbmtform = document.submitform;
	sbmtform.PDBID.value = "2PDZ";
	sbmtform.seqtol_chain1.value = "A";
	sbmtform.seqtol_chain2.value = "B";

	sbmtform.seqtol_mut_c_0.value = "B";
	sbmtform.seqtol_mut_r_0.value = "3";
	addOneMoreSeqtol();
	sbmtform.seqtol_mut_c_1.value = "B";
	sbmtform.seqtol_mut_r_1.value = "4";
	addOneMoreSeqtol();
	sbmtform.seqtol_mut_c_2.value = "B";
	sbmtform.seqtol_mut_r_2.value = "5";
	addOneMoreSeqtol();
	sbmtform.seqtol_mut_c_3.value = "B";
	sbmtform.seqtol_mut_r_3.value = "6";
	sbmtform.JobName.value = "Interface Sequence Tolerance sample job"
}

/*******************************************************************************
 * Protocol-specific functions - Sequence Tolerance SK
 ******************************************************************************/

function validateSeqtolSK()
{
	ret = true;
	var sbmtform = document.submitform;
	var elems = sbmtform.elements;
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
		ret = validateElem(sbmtform.seqtol_SK_chain0, alphaExpression) && ret;
	}

	// Highlight Boltzmann factor if missing or invalid
	if (!elems["customBoltzmann"].checked)
	{		
    	ret = validateElem(sbmtform.seqtol_SK_Boltzmann, numericExpression) && ret;
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
	if (validDesigned[-1] == 0) // if the number of valid designed residues is
								// zero
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
    			ret = validateElem(c, numericExpression) && ret;
        	}	
        }
    }
    
    return ret;
}

function demoSeqtolSK(setAllData)
{
	var sbmtform = document.submitform;
	
	sbmtform.StoredPDB.value = '';
	sbmtform.PDBID.value = "@2I0L_A_C_V2006";
 
    if (setAllData)
    {
    	elemA = sbmtform.seqtol_SK_chain0
		elemB = sbmtform.seqtol_SK_chain1
		elemNumPartners = sbmtform.numPartners
		
		// @js2
		// Clear automatically filled values
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
		
		for (i = 1; i < 5; i++)
		{
			new Effect.Appear("seqtol_SK_row_" + "" + i, { duration: 0.0, queue: { scope: 'task' }});
		}
		numSeqTolSK = 5

		sbmtform.seqtol_SK_mut_c_0.value = "B";
		sbmtform.seqtol_SK_mut_r_0.value = 2002;
		
		sbmtform.seqtol_SK_mut_c_1.value = "B";
		sbmtform.seqtol_SK_mut_r_1.value = 2003;
		
		sbmtform.seqtol_SK_mut_c_2.value = "B";
		sbmtform.seqtol_SK_mut_r_2.value = 2004;
		
		sbmtform.seqtol_SK_mut_c_3.value = "B";
		sbmtform.seqtol_SK_mut_r_3.value = 2005;
		
		sbmtform.seqtol_SK_mut_c_4.value = "B";
		sbmtform.seqtol_SK_mut_r_4.value = 2006;
		
		sbmtform.seqtol_SK_kP0P0.value = "0.4";
		sbmtform.seqtol_SK_kP1P1.value = "0.4";
		sbmtform.seqtol_SK_kP0P1.value = "1.0";
		sbmtform.seqtol_SK_Boltzmann.value = 0.228;
		chainsChanged();
    }
	sbmtform.JobName.value = "Interface Sequence Tolerance sample job"
}

/*******************************************************************************
 * Protocol-specific functions - Sequence Tolerance SK Multi
 ******************************************************************************/

function validateSeqtolSKMulti()
{
	ret = true;
	var sbmtform = document.submitform;
	var elems = sbmtform.elements;
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
		ret = validateElem(sbmtform.seqtol_SK_chain0, alphaExpression) && ret;
	}

	// Highlight Boltzmann factor if missing or invalid
	if (!elems["customBoltzmann"].checked)
	{		
    	ret = validateElem(sbmtform.seqtol_SK_Boltzmann, numericExpression) && ret;
	}

	var validResidues = getValidResidues();
	var validPremutations = validResidues["premutated"]
	var validDesigned = validResidues["designed"]
	
	// Highlight any invalid premutation rows
	for (i = 0; i < validPremutations.length; i++)
	{
		if (!validPremutations[i])
		{
			markError(elems['seqtol_SKMulti_pre_mut_c_' + i]);
			markError(elems['seqtol_SKMulti_pre_mut_r_' + i]);
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
	if (validDesigned[-1] == 0) // if the number of valid designed residues is
								// zero
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
    			ret = validateElem(c, numericExpression) && ret;
        	}	
        }
    }

    return ret;
}

function demoSeqtolSKMulti(setAllData)
{
	var sbmtform = document.submitform;
	
	sbmtform.StoredPDB.value = '';
	sbmtform.PDBID.value = "@1KI1";
	
	// @js14 "Premutated" : {"A" : {56 : allAAsExceptCysteine}},
    
    if (setAllData)
    {
    	elemA = sbmtform.seqtol_SK_chain0
		elemB = sbmtform.seqtol_SK_chain1
		elemNumPartners = sbmtform.numPartners
		
		// @js2
		// Clear automatically filled values
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
		
		for (i = 0; i < 1; i++)
		{
			new Effect.Appear("seqtol_SKMulti_pre_row_" + "" + i, { duration: 0.0, queue: { scope: 'task' }});
		}
		numSeqTolSKMultiPremutations = 1
		sbmtform.seqtol_SKMulti_pre_mut_c_0.value = "A";
		sbmtform.seqtol_SKMulti_pre_mut_r_0.value = 56;
		
		for (i = 1; i < 4; i++)
		{
			new Effect.Appear("seqtol_SK_row_" + "" + i, { duration: 0.0, queue: { scope: 'task' }});
		}
		numSeqTolSK = 4

		sbmtform.seqtol_SK_mut_c_0.value = "B";
		sbmtform.seqtol_SK_mut_r_0.value = 1369;
		
		sbmtform.seqtol_SK_mut_c_1.value = "B";
		sbmtform.seqtol_SK_mut_r_1.value = 1373;
		
		sbmtform.seqtol_SK_mut_c_2.value = "B";
		sbmtform.seqtol_SK_mut_r_2.value = 1376;
		
		sbmtform.seqtol_SK_mut_c_3.value = "B";
		sbmtform.seqtol_SK_mut_r_3.value = 1380;
				
		sbmtform.seqtol_SK_kP0P0.value = "0.4";
		sbmtform.seqtol_SK_kP1P1.value = "0.4";
		sbmtform.seqtol_SK_kP0P1.value = "1.0";
		sbmtform.seqtol_SK_Boltzmann.value = 0.228 + 0.021;
		chainsChanged();
    }
	sbmtform.JobName.value = "Sequence Tolerance Multi sample job"
}

/*******************************************************************************
 * Protocol-specific GUI functions
 ******************************************************************************/

// @js3

/* Multiple point mutations */

// Adds a residue input field
// @js4
function addOneMore()
{
	new Effect.Appear("row_PM" + "" + numMPM);
	numMPM = numMPM + 1;
	if (numMPM >= MaxMultiplePointMutations)
	{
		  new Effect.Fade("addmrow_0_1", { duration: 0.0 } );
	}
	return true;
}

/* Sequence Tolerance HK */

// Adds a residue input field
// @js5
function addOneMoreSeqtol()
{
	new Effect.Appear("seqtol_row_" + "" + numSeqTol);
	numSeqTol = numSeqTol + 1;
	if (numSeqTol >= HK_MaxMutations)
	{
		  new Effect.Fade("addmrow_2_0", { duration: 0.0 } );
	}
	return true;
}


/* Sequence Tolerance SK */

// Adds a residue input field
// @js6
function addOneMoreSeqtolSK()
{
	new Effect.Appear("seqtol_SK_row_" + "" + numSeqTolSK, { duration: 0.0, queue: { scope: 'task' }});
	numSeqTolSK = numSeqTolSK + 1;
	if (numSeqTolSK >= SK_MaxMutations)
	{
		  new Effect.Fade("addmrow_2_1", { duration: 0.0, queue: { scope: 'task' }});
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

function addOneMoreSeqtolSKMultiPremutated()
{
	new Effect.Appear("seqtol_SKMulti_pre_row_" + "" + numSeqTolSKMultiPremutations);
	numSeqTolSKMultiPremutations = numSeqTolSKMultiPremutations + 1;
	if (numSeqTolSKMultiPremutations >= SK_MaxPremutations)
	{
		new Effect.Fade("seqtol_SKMulti_pre_addrow", { duration: 0.0 } );
	}
	return true;
}

function changeApplicationToSeqtolSK1(app, task, extra)
{
	new Effect.Fade( "recNumStructures" + app + "_" + task );
	setSubmissionButtonsVisibility(false);
	
	new Effect.Appear( "parameterSeqtolSK_step1", { duration: 0.0, queue: { scope: 'task' }} );		
	new Effect.Fade(   "parameterSeqtolSK_step2", { duration: 0.0, queue: { scope: 'task' }} );
}

function changeApplicationToSeqtolSK2(app, task, extra)
{
	_extra = extra[0]
	_override = extra[1]
	                          	 
	var i;
	new Effect.Appear( "parameterSeqtolSK_step2", { duration: 0.0, queue: { scope: 'task' }} );	
	if ((app == 2) && (task == 1))
	{
		new Effect.Appear( "seqtolSK_premutated", { duration: 0.0, queue: { scope: 'task' }} );
	}
	else if ((app == 3) && (task == 0))
	{
		new Effect.Appear( "seqtolSKMulti_premutated", { duration: 0.0, queue: { scope: 'task' }} );
	}		
	
	setSubmissionButtonsVisibility(true);
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
		new Effect.Fade("seqtol_SK_chainrow_" + "" + i, { duration: 0.0, queue: { scope: 'task' }} );
	}
	numSeqTolSKChains = _extra
	
	if (!_override)
	{
		chainsChanged();
		reset_seqtolSKData();
	}
	new Effect.Appear( "recNumStructures" + app + "_" + task );
	
	if (localquery == "sampleData")
	{
		// @js7
		var mutationsUpTo = 0;
		if (isProtocol(2, 1))
		{
			numSeqTolSKPremutations = 0;
			for (i = 0; i < SK_MaxPremutations; i++)
			{
				new Effect.Fade("seqtol_SK_pre_row_" + "" + i, { duration: 0.0, queue: { scope: 'task' }});
			}
			mutationsUpTo = 6;
		}
		if (isProtocol(3, 0))
		{
			new Effect.Appear("seqtol_SKMulti_pre_row_0", { duration: 0.0, queue: { scope: 'task' }});
			for (i = 1; i < SK_MaxPremutations; i++)
			{
				new Effect.Fade("seqtol_SKMulti_pre_row_" + "" + i, { duration: 0.0, queue: { scope: 'task' }});
			}
			mutationsUpTo = 5;
		}
				
		for (i = 0; i < mutationsUpTo; i++)
		{
			new Effect.Appear("seqtol_SK_row_" + "" + i, { duration: 0.0, queue: { scope: 'task' }});
		}
		for (i = mutationsUpTo; i < SK_MaxMutations; i++)
		{
			new Effect.Fade("seqtol_SK_row_" + "" + i, { duration: 0.0, queue: { scope: 'task' }});
		}
		new Effect.Appear("addmrow_2_1", { duration: 0.0, queue: { scope: 'task' }});
	}	
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
	
	// Premutations for design (Multi)
	for (i = 0; i < minSeqTolSKMultiPremutations; i++)
	{
		oSubmitForm.elements["seqtol_SKMulti_pre_mut_c_" + i].value = "";
		new Effect.Appear( "seqtol_SKMulti_pre_row_" + i, { duration: 0.0 } );
	}
	for (i = minSeqTolSKMultiPremutations; i < SK_MaxPremutations; i++)
	{
		oSubmitForm.elements["seqtol_SKMulti_pre_mut_c_" + i].value = "";
		new Effect.Fade( "seqtol_SKMulti_pre_row_" + i, { duration: 0.0 } );
	}
	new Effect.Appear("seqtol_SKMulti_pre_addrow");
	numSeqTolSKMultiPremutations = minSeqTolSKMultiPremutations;
	
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
	new Effect.Appear("addmrow_2_1");
	numSeqTolSK = minSeqTolSKMutations;
	
	// Chains
	for (i = initNumSeqTolSKChains; i < SK_max_seqtol_chains; i++)
	{
		oSubmitForm.elements["seqtol_SK_chain" + i].value = "";
		// new Effect.Fade( "seqtol_SK_chainrow_" + i, { duration: 0.0 } );
	}
	// numSeqTolSKChains = initNumSeqTolSKChains;
}

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
			alert("Javascript functionality missing. Please try another browser.")
			return
			var integralExpression = /^[0-9]+$/;
						
			var tds = document.getElementsByTagName("td");
			for (j = 0; j < tds.length; j++)
			{
				var cn = tds[j].className;
				if (cn && cn.indexOf("seqtol_SK_kP") == 0)
				{
					var idx = cn.substring(11);
					if (checkValue(idx, integralExpression))
					{
						idx = parseInt(idx);
						if (idx < SK_max_seqtol_chains - 1)
						{
							// add columnElements[idx].className to list idx
						}
					}
				}
			}
		}
		else
		{
			for (i = 0; i < SK_max_seqtol_chains - 1 ; i = i + 1)
			{
				// @js8
				columnElements[i] = document.getElementsByClassName("seqtol_SK_kP" + i)
			}
		}
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
		var invalid = !checkValue(c.value, chainExpression);
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

function updateBoltzmann()
{
	if (document.submitform.elements["customBoltzmann"].checked)
	{
		var validPremuations = getValidResidues()["premutated"]
       	document.submitform.seqtol_SK_Boltzmann.value = SK_InitialBoltzmann + validPremuations[-1] * SK_BoltzmannIncrease;
	}
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

/* Sequence Tolerance SK Multi */

function selectAminoAcids(elem, selection)
{
	var n = elem.value;
	for (i = 0; i < document.getElementsByName("premutatedAAMulti" + n).length; i++)
	{
		document.getElementsByName("premutatedAAMulti" + n)[i].checked = selection;
	}
	
}

/*******************************************************************************
 * Validity subfunctions
 ******************************************************************************/

// Generic checkers and validators

// Be careful using this as a boolean value as it uses match.
// Apply negation or double negation to get a boolean value back.
function checkValue(v, expression)
{
	return v.match(expression)
}

function validateElem(elem, expression)
{
	var val = elem.value
	if(val.length > 0 && val.match(expression))
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

function validateEmptyElem(elem)
{
	var val = elem.value
	if(val.match(emptyExpression))
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

function validateNotEmpty(elem)
{
	if(elem.value.match(emptyExpression))
	{
		elem.focus();
		elem.style.background="red";
		return false;
	}
	elem.style.background="white";
	return true;
}

// Specific validators

function validChain(c)
{
	// @js9
	if (checkValue(c, chainExpression))
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

// @js10
function validChainHK(c)
{
	// @js11
	if (checkValue(c, chainExpression))
	{
		var elems = document.submitform.elements;
		if (elems["seqtol_chain1"].value == c)
		{
			return true;
		}
		else if (elems["seqtol_chain2"].value == c)
		{
			return true;
		}
	}
	return false;
}

// @js12

// *** Sequence Tolerance ***
// Returns an array of two arrays.
// The first array maps the displayed (numSeqTolSKPremutations) premutation
// indices to one of the values (true, false, "").
// true means that the premutation is valid
// false means that the premutation is invalid
// -1 means that the premutation fields are empty
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
		
	if (isProtocol(2, 1))
	{
		for (i = 0; i < numSeqTolSKPremutations ; i = i + 1) 
		{
			premutated[i] = false; 
			var chain = "" + elems["seqtol_SK_pre_mut_c_" + i].value;
			var resid = elems["seqtol_SK_pre_mut_r_" + i]
			resid.value = resid.value.replace(/^\s+|\s+$/g, '')
			var rval = resid.value 
			var AA = "" + elems["premutatedAA" + i].value;
	        
			if (chain == "invalid" && rval == "" && AA.length != 3)
			{
				premutated[i] = -1;
			}
			else if (validChain(chain) && validateElem(resid, integralExpression) && AA.length == 3)
			{
				if (!existingPremutations[chain+rval])
				{
					numValidPremutations = numValidPremutations + 1;
					premutated[i] = true; 
				}
				existingPremutations[chain+rval] = true;
			}
		}
	}
	if (isProtocol(3, 0))
	{
		for (i = 0; i < numSeqTolSKMultiPremutations ; i = i + 1) 
		{
			premutated[i] = false; 
			var chain = "" + elems["seqtol_SKMulti_pre_mut_c_" + i].value;
			var resid = elems["seqtol_SKMulti_pre_mut_r_" + i]
			resid.value = resid.value.replace(/^\s+|\s+$/g, '')
			var rval = resid.value 
						
			var checkboxgroup = "premutatedAAMulti" + i;
			var anychecked = false;
			for (j = 0; j < document.getElementsByName(checkboxgroup).length; j++)
			{
				anychecked = anychecked || document.getElementsByName(checkboxgroup)[j].checked;
			}
			if (chain == "invalid" && rval == "") // @js14:
																	// count AA
																	// filled in
			{
				premutated[i] = -1;
			}
			else if (validChain(chain) && validateElem(resid, integralExpression)) // @js14:
																					// count
																					// AA
																					// filled
																					// in
			{
				if (!existingPremutations[chain+rval])
				{
					numValidPremutations = numValidPremutations + 1;
					premutated[i] = true; 
				}
				existingPremutations[chain+rval] = true;
			}
		}
	}
	if ((isProtocol(2, 1)) || (isProtocol(3, 0)))
	{
		for (i = 0; i < numSeqTolSK ; i = i + 1) 
		{
			designed[i] = false; 
			var chain = "" + elems["seqtol_SK_mut_c_" + i].value;
			var resid = elems["seqtol_SK_mut_r_" + i]
			resid.value = resid.value.replace(/^\s+|\s+$/g, '')
			var rval = resid.value 
						  			
			if (chain == "invalid" && rval == "")
			{
				designed[i] = -1;
			}
			else if (validChain(chain) && validateElem(resid, integralExpression))
			{
				if (!existingDesignedResidues[chain+rval])
				{
					numValidDesignedResidues = numValidDesignedResidues + 1;
					designed[i] = true; 
				}
				existingDesignedResidues[chain+rval] = true;
			}
		}
	}
	// @js13
	else if (isProtocol(2, 0))
	{
		for (i = 0; i < numSeqTol ; i = i + 1) 
		{
			designed[i] = false; 
			var chain = elems["seqtol_mut_c_" + i].value;
			var resid = elems["seqtol_mut_r_" + i]
			resid.value = resid.value.replace(/^\s+|\s+$/g, '');
			var rval = resid.value 
			
			if (chain == "" && rval == "")
			{
				designed[i] = -1;
			}
			else if (validChainHK(chain) && validateElem(resid, integralExpression))
			{
				if (!existingDesignedResidues[chain+rval])
				{
					numValidDesignedResidues = numValidDesignedResidues + 1;
					designed[i] = true; 
				}
				existingDesignedResidues[chain+rval] = true;
			}
		}
	}
	premutated[-1] = numValidPremutations
	designed[-1] = numValidDesignedResidues
	validResidues["premutated"] = premutated
	validResidues["designed"] = designed
	return validResidues;
}


/*******************************************************************************
 * GUI functions
 ******************************************************************************/

// This function clears all form fields except for those specifically listed in
// the persistent array
function clearFormFields()
{
	var elems = document.submitform.elements;
	
	// Remember any persistent fields here
	persistent = new Array("JobName", "nos", "numPartners");
	previousValues = new Array();
	for (var i = 0; i < persistent.length; i++ ) 
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
			elems[k].value = previousValues[k];
		}
	}
}

function showCommonElements(subtask)
{
	// Show or hide the PDB uploading section
	if (subtask == 0)
	{
		new Effect.Appear('PrePDBParameters', { duration: 0.0 } );
		new Effect.Fade('PostPDBParameters', { duration: 0.0 } );
	}
	else
	{
		new Effect.Fade('PrePDBParameters', { duration: 0.0 } );
		new Effect.Appear('PostPDBParameters', { duration: 0.0 } );
	}
	new Effect.Appear( 'parameter_submit', { duration: 0.5, queue: { scope: 'task' } } ) ;
}

function hideInactiveProtocols(app, task)
{
	// Change the color of the box depending on the series and add the
	// appropriate logo
	for ( i = 0; i < protocolTasks.length; i++ ) 
	{
		new Effect.Fade( "text" + i , { duration: 0.0 } );
		if (i == app)
		{
			new Effect.Appear("pic" + i);
		}
		else
		{
			new Effect.Fade( "pic" + i, { duration: 0.0, queue: { position: '0', scope: 'img' } } );
		}
	}	
	document.getElementById("box").style.background = colors[app];	
	  	
	// Hide all other specialized parameters
	var thistask = undefined
	
	// special-cased to allow both protocols to share the same form
	runningSeqtolSK = isProtocol(2, 1) || isProtocol(3, 0);
	if (!runningSeqtolSK)
	{
		new Effect.Fade('parameterSeqtolSK', { duration: 0.0, queue: { scope: 'task' }} )
	}
	else
	{
		new Effect.Appear('parameterSeqtolSK', { duration: 0.0, queue: { scope: 'task' }} )
	}
	
	for ( i = 0; i < protocolTasks.length; i++ ) 
	{
		for ( j = 0; j < protocolTasks[i]; j++ )
		{
			ptask = 'parameter' + i + '_' + j;
			arrowstyle = document.getElementById("protocolarrow" + i + "_" + j).style
			
			if ( !isProtocol(i, j)) 
			{
				new Effect.Fade(ptask , { duration: 0.0, queue: { scope: 'task' }} );
				new Effect.Fade( "ref" + i + "_" + j, { duration: 0.0, queue: { scope: 'task' }} );
				new Effect.Fade( "recNumStructures" + i + "_" + j, { duration: 0.0 } );
				arrowstyle.color = "black"
				arrowstyle.fontWeight = "normal"
			}
			else
			{
				thistask = ptask
				new Effect.Appear(ptask, { duration: 0.0, queue: { scope: 'task' }} )
				new Effect.Appear( "ref" + i + "_" + j, { duration: 0.0, queue: { scope: 'task' }} )
				new Effect.Appear( "recNumStructures" + i + "_" + j, { duration: 0.0 } );
				arrowstyle.color = "#d55414"
				arrowstyle.fontWeight = "bold"
			}
		}
	}
	return thistask
}

function allWhite()
{
	for(i = 0; i < document.submitform.elements.length; i++)
	{
		var elem = document.submitform.elements[i];
		if ((elem.disabled == false) || (elem.name == "UserName") || (elem.name == "MiniTextbox") || (elem.name == "UploadedPDB"))
		{
			elem.style.background = "white";
		}
		else
		{
			if (elem.style.background != null && elem.style.background != "")
			{
				elem.style.backgroundColor = "silver";
			}
		}
	}
}

function reset_form ()
{
	// Remember the binary selection
	// This avoids problems when a user loads sample data then resets the form
	// then loads sample data again
	selectedMini = -1
	Mini = document.submitform.Mini;
	for (var i = 0 ; i < Mini.length ; i++)
	{
		if (Mini[i].checked)
		{
			selectedMini = i
		}
	}

	document.submitform.reset();
	allWhite();
	chainsChanged();
	reset_seqtolSKData();
	
	// Re-enter binary selection
	if (selectedMini >= 0)
	{
		Mini[selectedMini].checked = true
	}
}



/*******************************************************************************
 * Getters / Setters
 ******************************************************************************/

function setProtocol(group, task)
{
	document.submitform.protocolgroup.value = group
	document.submitform.protocoltask.value = task
}

function getProtocol()
{
	return [document.submitform.protocolgroup.value, document.submitform.protocoltask.value]
}

function isProtocol(group, task)
{
	return (document.submitform.protocolgroup.value == group && document.submitform.protocoltask.value == task); 
}

function isProtocolGroup(group)
{
	return (document.submitform.protocolgroup.value == group); 
}

/*******************************************************************************
 * helper functions
 ******************************************************************************/

function markError(elem)
{
	elem.focus();
	elem.style.background="red";
}

function usingMini()
{
	Mini = document.submitform.Mini;
	for (var i = 0 ; i < Mini.length ; i++)
	{
		if (Mini[i].checked)
		{
			return bversion[Mini[i].value];
		}
	}
	alert("Rosetta version unidentified.")
	return false;
}

