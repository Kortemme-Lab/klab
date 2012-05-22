subpages = ["submission", "report"]

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

if (document.benchmarksform.BenchmarksPage.value != null)
{
	showPage(document.benchmarksform.BenchmarksPage.value)
}

function editCommandLine()
{
	subform = document.benchmarkoptionsform
	BenchmarkCommandLineType = subform.BenchmarkCommandLineType;
	benchmarkname = subform.BenchmarkType.value;
	
	alternateflags_dropbox = subform.elements['BenchmarkAlternateFlags' + benchmarkname ]
	fadefx = { duration: 0.0, queue: { position: '0', scope: 'task' } }
	for(var i = 0; i < BenchmarkCommandLineType.length; i++) 
	{
		if(BenchmarkCommandLineType[i].checked) 
		{
			if (BenchmarkCommandLineType[i].value == "Standard")
			{
				new Effect.Fade(alternateflags_dropbox, fadefx);
				new Effect.Fade(subform.BenchmarkCommandLine_1, fadefx);
				new Effect.Fade(subform.BenchmarkCommandLine_2, fadefx);
			}
			else if (BenchmarkCommandLineType[i].value == "ExtraFlags")
			{
				alternateflags_dropbox.options.length = 0
				for (x = 0; x < benchmarks[benchmarkname]['alternate_flags'].length; x++)
				{
					alternateflags_dropbox.options[alternateflags_dropbox.length] = new Option(benchmarks[benchmarkname]['alternate_flags'][x], benchmarks[benchmarkname]['alternate_flags'][x]);
				}
				new Effect.Appear(alternateflags_dropbox, fadefx);
				new Effect.Fade(subform.BenchmarkCommandLine_1, fadefx);
				new Effect.Fade(subform.BenchmarkCommandLine_2, fadefx);
			}
			else if (BenchmarkCommandLineType[i].value == "Custom")
			{
				new Effect.Fade(alternateflags_dropbox, fadefx);
				new Effect.Appear(subform.BenchmarkCommandLine_1, fadefx);
				new Effect.Appear(subform.BenchmarkCommandLine_2, fadefx);
			}
		}
	}
}

