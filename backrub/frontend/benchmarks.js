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
	
	return false;
	return success;
}


function ChangeBenchmark()
{
	//Select the database of the corresponding Rosetta revision if it exists
	var subform = document.benchmarkoptionsform;
	var benchmarkName = subform.elements['BenchmarkType'].value;
	
	// Add the binary revisions
	binary_revisions = benchmarks[benchmarkName]['revisions']
	revisionSelector = subform.elements['BenchmarkRosettaRevision']
	clearSelect(revisionSelector);
	for (i = 0; i < binary_revisions.length; i++)
	{
		binary_revision = binary_revisions[i];
		revisionSelector.options[revisionSelector.options.length] = new Option(binary_revision, binary_revision);
	}
	revisionSelector.options[0].selected = true;
	
	// Add the alternate flags
	alternate_flags = benchmarks[benchmarkName]['alternate_flags']
	alternateFlagsSelector = subform.elements['BenchmarkAlternateFlags']
	clearSelect(alternateFlagsSelector);
	for (i = 0; i < alternate_flags.length; i++)
	{
		alternate_flag = alternate_flags[i];
		alternateFlagsSelector.options[alternateFlagsSelector.options.length] = new Option(alternate_flag, alternate_flag);
	}
	alternateFlagsSelector.options[0].selected = true;
	
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
	// Set up the custom flag text areas
	subform.elements['BenchmarkCommandLine_1'].rows = benchmarks[benchmarkName]['CustomFlagsDimensions'][0]; 
	subform.elements['BenchmarkCommandLine_1'].cols = benchmarks[benchmarkName]['CustomFlagsDimensions'][2];
	subform.elements['BenchmarkCommandLine_1'].value = benchmarks[benchmarkName]['ParameterizedFlags']; 
	subform.elements['BenchmarkCommandLine_2'].rows = benchmarks[benchmarkName]['CustomFlagsDimensions'][1]; 
	subform.elements['BenchmarkCommandLine_2'].cols = benchmarks[benchmarkName]['CustomFlagsDimensions'][2];
	subform.elements['BenchmarkCommandLine_2'].value = benchmarks[benchmarkName]['SimpleFlags']; 
			
			
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
	ChangedRunLength();
}

defaultWalltimes = {
	'Test' : {'Days' : 0, 'Hours' : 6, 'Minutes' : 0},
	'Normal' : {'Days' : 7, 'Hours' : 0, 'Minutes' : 0},
	'Long' : {'Days' : 14, 'Hours' : 0, 'Minutes' : 0},
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
	var benchmark1 = prompt('[Optional] Enter a title for the left-selected benchmark.', null);
	var benchmark2 = prompt('[Optional] Enter a title for the right-selected benchmark.', null);
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

