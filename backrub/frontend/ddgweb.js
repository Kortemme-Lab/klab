subpages = ["status", "protherm", "jmol"]

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
						document.ddgform.DDGPage.value = page
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

if (document.ddgform.DDGPage.value != null)
{
	showPage(document.ddgform.DDGPage.value)
}

/************************************
 * Jmol functions 
 ************************************/

function _updateResidues(strarray, n, residues)
{
	if (residues.length > 0)
	{
		var numres = residues.length;
		residueString = []
		for (j = 0; j < residues.length; j++)
		{
			residueString.push(residues[j] + "/" + n + " ") // Eclipse 3.5.2 throws an "AST creation" error/wobbly with this line and some from updateJmol which necessitates moving these scripts into a separate file. 
		}
		strarray.push(residueString.join())
	}
}

function updateJmol()
{
	//for all structure checkboxes
	
	displayString = ""
	var displayString = [];
	var hideString = [];
	var residueString = [];
		                                      	
	// Display / hide structures
	for (i = 0; i < document.getElementsByName("JmolStructures").length; i++)
	{
		var showStructure = document.getElementsByName("JmolStructures")[i].checked;
		
		index = document.getElementsByName("JmolStructures")[i].value
		if (showStructure)
		{
			displayString.push(index)
		}
		else
		{
			hideString.push(index)
		}		
	}
	if (displayString.length == 0)
	{
		document.getElementsByName("JmolStructures")[0].checked = true
		jmolScript("frame all; display 1.0")		
	}
	else
	{
		jmolScript("frame all; display " + displayString.join() + "; hide " + hideString.join())
	}
}

