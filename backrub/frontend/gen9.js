subpages = ["browse"]

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
						document.gen9form.Gen9Page.value = page
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

if (document.gen9form.Gen9Page.value != null)
{
	showPage(document.gen9form.Gen9Page.value)
}

if (document.gen9form.gen9sort1.value == null || document.gen9form.gen9sort1.value == "")
{
	document.gen9form.gen9sort1.value = 'Complex';
}
if (document.gen9form.gen9sort2.value == null || document.gen9form.gen9sort2.value == "")
{
	document.gen9form.gen9sort2.value = 'ID';
}

if (document.gen9form.gen9sort1.value != null && document.gen9form.gen9sort1.value != "" )
{
	if (document.gen9form.gen9sort1.value == 'Complex')
	{
		var order_selection = document.getElementById("ordering1");
		order_selection.options[0].selected = true;
	}
	else if (document.gen9form.gen9sort1.value == 'ID')
	{
		var order_selection = document.getElementById("ordering1");
		order_selection.options[1].selected = true;
	}
	else if (document.gen9form.gen9sort1.value == 'Target')
	{
		var order_selection = document.getElementById("ordering1");
		order_selection.options[2].selected = true;
	}
	else if (document.gen9form.gen9sort1.value == 'Scaffold')
	{
		var order_selection = document.getElementById("ordering1");
		order_selection.options[3].selected = true;
	}
}
if (document.gen9form.gen9sort2.value != null && document.gen9form.gen9sort2.value != "" )
{
	if (document.gen9form.gen9sort2.value == 'Complex')
	{
		var order_selection = document.getElementById("ordering2");
		order_selection.options[0].selected = true;
	}
	else if (document.gen9form.gen9sort2.value == 'ID')
	{
		var order_selection = document.getElementById("ordering2");
		order_selection.options[1].selected = true;
	}
	else if (document.gen9form.gen9sort2.value == 'Target')
	{
		var order_selection = document.getElementById("ordering2");
		order_selection.options[2].selected = true;
	}
	else if (document.gen9form.gen9sort2.value == 'Scaffold')
	{
		var order_selection = document.getElementById("ordering2");
		order_selection.options[3].selected = true;
	}
}
function reopen_page_with_sorting()
{
	var o1 = document.getElementById("ordering1");
	var ordering1 = o1.options[o1.selectedIndex].value;
	var o2 = document.getElementById("ordering2");
	var ordering2 = o2.options[o2.selectedIndex].value;
	window.open("?query=Gen9&gen9sort1=" + ordering1 + "&gen9sort2=" + ordering2, "_self");
}

if (document.gen9form.DesignID.value != "")
{
	window.location.hash="" + document.gen9form.DesignID.value;
}
if (document.gen9form.Gen9Error.value != "")
{
	alert(document.gen9form.Gen9Error.value);
}

function copyPageFormValues(elem)
{
	design_form = elem.form;
	design_form.Gen9Page.value = document.gen9form.Gen9Page.value;
	design_form.query.value = "Gen9Comment"
	design_form.gen9sort1.value = document.gen9form.gen9sort1.value;
	design_form.gen9sort2.value = document.gen9form.gen9sort2.value;
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

