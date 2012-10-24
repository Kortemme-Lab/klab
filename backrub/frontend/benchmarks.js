subpages = ["submission", "binaries", "report"]

function showPage(page)
{
	foundDiv = false;
	for (j = 0 ; j < 2; j++)
	{
		for (i = 0; i < subpages.length; i++)
		{
			if (page == subpages[i])
			{
				foundDiv = true;
			}
		}
		if (foundDiv)
		{
			if (document.getElementById)
			{
				for (i = 0; i < subpages.length; i++)
				{
					tpage = subpages[i]
					if (page == subpages[i])
					{
						document.getElementById(tpage).style.display = 'block';
						document.benchmarksform.BenchmarksPage.value = page
					}
					else
					{
						document.getElementById(tpage).style.display = 'none'; 
					}
				}
			}
			else
			{
				print("missing document.getElementById")
			}
			return;
		}
		else
		{
			page = subpages[0]
		}
	}
	alert("Cannot find div " + page)
}

function clearSelect(selectBoxElement)
{
	numExistingOptions = selectBoxElement.options.length
	for (i = 0; i < numExistingOptions ; i++){
		selectBoxElement.remove(0);
	}
	
}
function validate()
{
	var subform = document.benchmarkoptionsform;
	var benchmarkName = subform.elements['BenchmarkType'].value;
	success = true;
	benchmarkoptions = benchmarks[benchmarkName]['options'];
	if (!validateEmailAddress(subform.elements['BenchmarkNotificationEmailAddresses'], true, true))
	{
		success = false;
	}
	for (i = 0; i < benchmarkoptions.length; i++)
	{
		benchmarkoption = benchmarkoptions[i];
		if (benchmarkoption['Type'] == 'int')
		{
			formelement = subform.elements['Benchmark' + benchmarkName + 'Option' + benchmarkoption['OptionName']];
			if (!validateElem(formelement, integralExpression)) 
			{
				success = false;
			}
		}
		else if (benchmarkoption['Type'] == 'string' && benchmarkoption['OptionName'] == 'PDBsToBenchmark')
		{
			allowedPDBIDs = {};
			if (benchmarkName == "KIC" || benchmarkName == "NGK")
			{
				allowedPDBIDs = {
					'1a8d' : true, '1cnv' : true, '1ede' : true, '1ms9' : true, '1pbe' : true, '1thg' : true, '2ebn' : true, '3cla' : true, '1arb' : true,
					'1cs6' : true, '1exm' : true, '1msc' : true, '1qlw' : true, '1thw' : true, '2exo' : true, '3hsc' : true, '1bhe' : true, '1cyo' : true,
					'1ezm' : true, '1my7' : true, '1rro' : true, '1tib' : true, '2pia' : true, '4i1b' : true, '1bn8' : true, '1dqz' : true, '1f46' : true,
					'1onc' : true, '1srp' : true, '1tml' : true, '2rn2' : true, '1c5e' : true, '1dts' : true, '1i7p' : true, '1oth' : true, '1t1d' : true,
					'1xif' : true, '2sil' : true, '1cb0' : true, '1eco' : true, '1m3s' : true, '1oyc' : true, '1tca' : true, '2cpl' : true, '2tgi' : true
				};
			}
			formelement = subform.elements['Benchmark' + benchmarkName + 'Option' + benchmarkoption['OptionName']];
			
			failedPDBIDs = new Array();
			passedPDBIDs = formelement.value.split(',');
			for (j = 0; j < passedPDBIDs.length; j++)
			{
				formPDBID = passedPDBIDs[j].toLowerCase().replace(/^\s+|\s+$/g, '');
				if (formPDBID != "")
				{
					if (!allowedPDBIDs[passedPDBIDs[j].toLowerCase().replace(/^\s+|\s+$/g, '')])
					{
						failedPDBIDs.push(passedPDBIDs[j]);
					}
				}
			}
			if (failedPDBIDs.length > 0)
			{
				alert('The following PDB IDs are not valid for the ' + benchmarkName + ' benchmark: "' + failedPDBIDs.join('", "') + '".')
				markError(formelement);
				success = false;
			}
		}
		else
		{
			alert("The type '" + benchmarkoption['Type'] + "' of " + benchmarkoption['OptionName'] + " is not handled yet. Get the admin to write a JavaScript validator.")
		}
	}
	if (!validateElem(subform.elements['BenchmarkMemoryRequirement'], numericExpression)) 
	{
		success = false;
	}
	if (!validateElem(subform.elements['BenchmarkWalltimeLimitDays'], integralExpression, 0, 14)) 
	{
		success = false;
	}
	if (!validateElem(subform.elements['BenchmarkWalltimeLimitHours'], integralExpression, 0, 23)) 
	{
		success = false;
	}
	if (!validateElem(subform.elements['BenchmarkWalltimeLimitMinutes'], integralExpression, 0, 59)) 
	{
		success = false;
	}
	if (subform.elements['BenchmarkWalltimeLimitDays'].value == 14)
	{
		if (subform.elements['BenchmarkWalltimeLimitHours'].value > 0)
		{
			markError(subform.elements['BenchmarkWalltimeLimitHours']);
			success = false;
		}
		if (subform.elements['BenchmarkWalltimeLimitMinutes'].value > 0)
		{
			markError(subform.elements['BenchmarkWalltimeLimitMinutes']);
			success = false;
		}
	}
	
	minmaxErrors = []
	for (i = 0; i < benchmarkoptions.length; i++)
	{
		benchmarkoption = benchmarkoptions[i];
		formElement = subform.elements[benchmarkoption['FormElement']];
		optionValue = formElement.value
		if (benchmarkoption['Type'] == 'int')
		{
			if (benchmarkoption['MinimumValue'] != 'null')
			{
				minValue = parseInt(benchmarkoption['MinimumValue']);
				if (optionValue < minValue)
				{
					minmaxErrors.push("Benchmark option '" + benchmarkoption['Description'] + "' has a minimum value of " + minValue + ".");
					markError(formElement);
				}
			}
			if (benchmarkoption['MaximumValue'] != 'null')
			{
				maxValue = parseInt(benchmarkoption['MaximumValue']);
				if (optionValue > maxValue)
				{
					minmaxErrors.push("Benchmark option '" + benchmarkoption['Description'] + "' has a maximum value of " + maxValue + ".");
					markError(formElement);
				}
			}
		}
	}
	if (minmaxErrors.length > 0)
	{
		alert(minmaxErrors.join("\n"));
		return false;
	}
	
	// We need to enable all form elements or else their values will not be posted (or else use hidden variables)
	for (i = 0; i < benchmarkoptions.length; i++)
	{
		formElement = subform.elements[benchmarkoptions[i]['FormElement']];
		formElement.disabled = false;
	}

	
	return success;
}

function UpdateOptionsAndCommandLineForRevision()
{
	var subform = document.benchmarkoptionsform;
	var benchmarkName = subform.elements['BenchmarkType'].value;
	revisionSelector = subform.elements['BenchmarkRosettaRevision'];
	
	// We could just update here when the revision selection moves between revision groups e.g. from a KIC revision < 49521 to a revision >= 49521  
	
	// Add the alternate flags
	currentRevision = revisionSelector.value
	currentRevisionGroup = benchmarks[benchmarkName]['BinaryRevisionsToBenchmarkRevisionsMap'][currentRevision]
	alternate_flags = benchmarks[benchmarkName]['Revisions'][currentRevisionGroup]['alternate_flags']
	alternateFlagsSelector = subform.elements['BenchmarkAlternateFlags']
	clearSelect(alternateFlagsSelector);
	for (i = 0; i < alternate_flags.length; i++)
	{
		alternate_flag = alternate_flags[i];
		alternateFlagsSelector.options[alternateFlagsSelector.options.length] = new Option(alternate_flag, alternate_flag);
	}
	alternateFlagsSelector.options[0].selected = true;
	
	// Set up the custom flag text areas
	subform.elements['BenchmarkCommandLine_1'].rows  = benchmarks[benchmarkName]['Revisions'][currentRevisionGroup]['CustomFlagsDimensions'][0]; 
	subform.elements['BenchmarkCommandLine_1'].cols  = benchmarks[benchmarkName]['Revisions'][currentRevisionGroup]['CustomFlagsDimensions'][2];
	subform.elements['BenchmarkCommandLine_1'].value = benchmarks[benchmarkName]['Revisions'][currentRevisionGroup]['ParameterizedFlags']; 
	subform.elements['BenchmarkCommandLine_2'].rows  = benchmarks[benchmarkName]['Revisions'][currentRevisionGroup]['CustomFlagsDimensions'][1]; 
	subform.elements['BenchmarkCommandLine_2'].cols  = benchmarks[benchmarkName]['Revisions'][currentRevisionGroup]['CustomFlagsDimensions'][2];
	subform.elements['BenchmarkCommandLine_2'].value = benchmarks[benchmarkName]['Revisions'][currentRevisionGroup]['SimpleFlags']; 
}

function ChangedRevision()
{
	var subform = document.benchmarkoptionsform;
	revisionSelector = subform.elements['BenchmarkRosettaRevision'];
	dbRevisionSelector = subform.elements['BenchmarkRosettaDBRevision'];
	for (i = 0; i < dbRevisionSelector.length; i++)
	{
		if (dbRevisionSelector.options[i].value <= revisionSelector.value) // select a database revision equal or lower to the binary's revision
		{
			dbRevisionSelector.options[i].selected = true;
			break;
		}
	}
	UpdateOptionsAndCommandLineForRevision();
}
function AddEmail(email_address)
{
	try
	{
		var subform = document.benchmarkoptionsform;
		emailAddressElement = subform.elements['BenchmarkNotificationEmailAddresses'];
		currentEmailAddresses = emailAddressElement.value;
		if (!validateEmailAddress(emailAddressElement, true, true))
		{
			alert("Existing email addresses are invalid. Cannot add a new one.")
			return;
		}
		if (currentEmailAddresses.indexOf(email_address) == -1)
		{
			if (currentEmailAddresses.replace(/^\s+|\s+$/g, '') == "")
			{
				emailAddressElement.value = email_address;
			}
			else
			{
				emailAddressElement.value += ", " + email_address;
			}
		}
		else
		{
			if (false && currentEmailAddresses.replace(/^\s+|\s+$/g, '') == email_address)
			{
				emailAddressElement.value = "";
			}
			else
			{
				new_addresses = []
				existingAddresses = emailAddressElement.value.split(",")
				for (i = 0; i < existingAddresses.length; i++)
				{
					existingAddress = existingAddresses[i].replace(/^\s+|\s+$/g, '');
					if (existingAddress != email_address)
					{
						new_addresses.push(existingAddress)
					}
				}
				emailAddressElement.value = new_addresses.join(", ")
			}
		}
	}
	catch(err)
	{
		alert(err)
	}
}
function ChangeBenchmark()
{
	//Select the database of the corresponding Rosetta revision if it exists
	var subform = document.benchmarkoptionsform;
	var benchmarkName = subform.elements['BenchmarkType'].value;
	
	// Add the binary revisions
	binary_revisions = benchmarks[benchmarkName]['availablerevisions']
	revisionSelector = subform.elements['BenchmarkRosettaRevision']
	clearSelect(revisionSelector);
	for (i = 0; i < binary_revisions.length; i++)
	{
		binary_revision = binary_revisions[i];
		revisionSelector.options[revisionSelector.options.length] = new Option(binary_revision, binary_revision);
	}
	if (revisionSelector.options.length > 0)
	{
		revisionSelector.options[0].selected = true;
		ChangedRevision();
	}
	
	fadefx = { duration: 0.0, queue: { position: '0', scope: 'task' } }
	if (document.getElementsByClassName == undefined)
	{
		alert("Javascript functionality missing: document.getElementsByClassName is not defined. Please try another browser.")
	}
	else
	{
		for (var k in benchmarks)
		{
			if (k != benchmarkName)
			{
				optionfields = document.getElementsByClassName("benchmark_" + k + "_options");
				for (i = 0; i < optionfields.length; i++)
				{
					new Effect.Fade(optionfields[i], fadefx);
				}
			}
		}
		optionfields = document.getElementsByClassName("benchmark_" + benchmarkName + "_options");
		for (i = 0; i < optionfields.length; i++)
		{
			new Effect.Appear(optionfields[i], fadefx);
		}
	}
	
	x = revisionSelector.value;
	dbrevisionoptions = subform.elements['BenchmarkRosettaDBRevision'].options
	for (i = 0; i < dbrevisionoptions.length; i++)
	{
		if (dbrevisionoptions[i].text == x)
		{
			subform.elements['BenchmarkRosettaDBRevision'].options[i].selected = true;
			break;
		}
	}
	
	document.getElementById('benchmarkseparator').style.color = benchmarks[benchmarkName]['color'];
	subform.elements['BenchmarkRunLength'].value = 'Normal';
	subform.elements['BenchmarkMemoryRequirement'].value = JSON.parse(benchmarks[benchmarkName]["MemoryRequirementsInGB"])["normal"];
	ChangedRunLength();
}

defaultWalltimes = {
	'Test' : {'Days' : 0, 'Hours' : 6, 'Minutes' : 0},
	'Normal' : {'Days' : 7, 'Hours' : 0, 'Minutes' : 0},
	'Long' : {'Days' : 14, 'Hours' : 0, 'Minutes' : 0}
};

function ChangedRunLength()
{
	var subform = document.benchmarkoptionsform;
	var benchmarkName = subform.elements['BenchmarkType'].value;
	var BenchmarkRunLength = subform.elements['BenchmarkRunLength'].value;
	benchmarkoptions = benchmarks[benchmarkName]['options'];
	
	if (BenchmarkRunLength == "Custom")
	{
		for (i = 0; i < benchmarkoptions.length; i++)
		{
			formElement = subform.elements[benchmarkoptions[i]['FormElement']];
			formElement.disabled = false;
		}
	}
	else
	{
		subform.elements['BenchmarkWalltimeLimitDays'].value = defaultWalltimes[BenchmarkRunLength]['Days'];
		subform.elements['BenchmarkWalltimeLimitHours'].value = defaultWalltimes[BenchmarkRunLength]['Hours'];
		subform.elements['BenchmarkWalltimeLimitMinutes'].value = defaultWalltimes[BenchmarkRunLength]['Minutes'];
		for (i = 0; i < benchmarkoptions.length; i++)
		{
			benchmarkoption = benchmarkoptions[i];
			formElement = subform.elements[benchmarkoption['FormElement']];
			formElement.value = benchmarkoption[BenchmarkRunLength + "RunValue"];
			formElement.disabled = true;
		}
	}
}

function editCommandLine()
{
	var subform = document.benchmarkoptionsform
	BenchmarkCommandLineType = subform.BenchmarkCommandLineType;
	benchmarkname = subform.BenchmarkType.value;
	
	alternateflags_dropbox = subform.elements['BenchmarkAlternateFlags']
	fadefx = { duration: 0.0, queue: { position: '0', scope: 'task' } }
	for(var i = 0; i < BenchmarkCommandLineType.length; i++) 
	{
		if(BenchmarkCommandLineType[i].checked) 
		{
			
			if (BenchmarkCommandLineType[i].value == "Standard")
			{
				new Effect.Fade(alternateflags_dropbox, fadefx);
				new Effect.Fade(document.getElementById("BenchmarkCustomSettingsMessage"), fadefx);
				new Effect.Fade(subform.BenchmarkCommandLine_1, fadefx);
				new Effect.Fade(subform.BenchmarkCommandLine_2, fadefx);
			}
			else if (BenchmarkCommandLineType[i].value == "ExtraFlags")
			{
				new Effect.Appear(alternateflags_dropbox, fadefx);
				new Effect.Fade(document.getElementById("BenchmarkCustomSettingsMessage"), fadefx);
				new Effect.Fade(subform.BenchmarkCommandLine_1, fadefx);
				new Effect.Fade(subform.BenchmarkCommandLine_2, fadefx);
			}
			else if (BenchmarkCommandLineType[i].value == "Custom")
			{
				new Effect.Fade(alternateflags_dropbox, fadefx);
				new Effect.Appear(document.getElementById("BenchmarkCustomSettingsMessage"), fadefx);
				new Effect.Appear(subform.BenchmarkCommandLine_1, fadefx);
				new Effect.Appear(subform.BenchmarkCommandLine_2, fadefx);
			}
		}
	}
}

function getBenchmarkNames()
{
	var subform = document.reportpageform;
	var benchmark1;
	var benchmark2;
	generateFreshComparison = subform.GenerateFreshComparison.checked
	if (generateFreshComparison)
	{
		benchmark1 = prompt('[Optional] Enter a title for the left-selected benchmark.', null);
		benchmark2 = prompt('[Optional] Enter a title for the right-selected benchmark.', null);
	}
	else
	{
		benchmark1 = null;
		benchmark2 = null;
	}
	var query = [];
	query[query.length] = 'query=benchmarkreport';
	if (benchmark1 != null)
	{
		benchmark1 = benchmark1.replace(/^\s+|\s+$/g, '');
		if (benchmark1 != '')
		{
			subform.Benchmark1Name.value = benchmark1;
			query[query.length] = 'Benchmark1Name=' + benchmark1;
		}
	}
	if (benchmark2 != null)
	{
		benchmark2 = benchmark2.replace(/^\s+|\s+$/g, '');
		if (benchmark2 != '')
		{
			subform.Benchmark2Name.value = benchmark2;
			query[query.length] = 'Benchmark2Name=' + benchmark2;
		}
	}
	vals = benchmarkWasSelected();
	subform.Benchmark1ID.value = vals[0]; 
	subform.Benchmark2ID.value = vals[1];
	subform.BenchmarksType.value = "KIC" // todo: generalize

	query[query.length] = 'Benchmark1ID=' + vals[0];
	query[query.length] = 'Benchmark2ID=' + vals[1];
	query[query.length] = 'BenchmarksType=' + "KIC"; // todo: generalize
	if (generateFreshComparison)
	{
		query[query.length] = 'generatefresh=True';
	}
	return query.join('&amp;');
}

function generateSingleRunReport(runID)
{
	var subform = document.reportpageform;
	var numbins = prompt('Enter the number of bins.', 100);
	if (numbins == null || !numbins.match(integralExpression))
	{
		alert("Bad value for the number of bins. Using the default value of 100.")
		numbins = 100;
	}
	var topX = prompt('Enter the number of lowest energy models to consider for the best model.', 5);
	if (topX == null || !topX.match(integralExpression))
	{
		alert("Bad value for the number of lowest energy models. Using the default value of 5.")
		topX = 5;
	}
	var query = ['query=benchmarkreport', 'id=' + runID, 'numbins=' + numbins, 'topx=' + topX, 'action=regenerate']; 
	return query.join('&amp;');
}

function benchmarkWasSelected()
{
	count = 0;
	leftvalue = null;
	rightvalue = null;
	radioset = document.reportpageform.benchmarkresults1;
	document.reportpageform.CompareButton.disabled = true;
	for(var i = 0; i < radioset.length; i++) {
		if(radioset[i].checked) {
			leftvalue = radioset[i].value;
			count = count + 1;
		}
	}
	radioset = document.reportpageform.benchmarkresults2;
	for(var i = 0; i < radioset.length; i++) {
		if(radioset[i].checked) {
			rightvalue = radioset[i].value; 
			if (leftvalue != rightvalue )
			{
				count = count + 1;
			}
		}
	}
	if (count == 2)
	{
		document.reportpageform.CompareButton.disabled = false;
	}
	return [leftvalue, rightvalue];
}

ChangeBenchmark();
if (document.benchmarksform.BenchmarksPage.value != null)
{
	showPage(document.benchmarksform.BenchmarksPage.value);
	benchmarkWasSelected();
}

