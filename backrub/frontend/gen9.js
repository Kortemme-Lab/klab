subpages = ["browse", "rankmapping"]

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

function show_file_links_new(DesignID)
{
	var elemname = 'file-links-div-' + DesignID;
	var rows = document.getElementsByClassName(elemname);
	for (i = 0; i < rows.length; i++)
	{
		var row = rows[i];
		if(row.getStyle('display') == 'none')
		{
			new Effect.Appear(row , { duration: 0.0 } );
		}
		else
		{
			new Effect.Fade( row, { duration: 0.0, queue: { position: '0', scope: 'task' } } );
		}
	}
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
	else if (document.gen9form.gen9sort1.value == 'MutantComplex')
	{
		var order_selection = document.getElementById("ordering1");
		order_selection.options[2].selected = true;
	}
	else if (document.gen9form.gen9sort1.value == 'Target')
	{
		var order_selection = document.getElementById("ordering1");
		order_selection.options[3].selected = true;
	}
	else if (document.gen9form.gen9sort1.value == 'Scaffold')
	{
		var order_selection = document.getElementById("ordering1");
		order_selection.options[4].selected = true;
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
	else if (document.gen9form.gen9sort2.value == 'MutantComplex')
	{
		var order_selection = document.getElementById("ordering2");
		order_selection.options[2].selected = true;
	}
	else if (document.gen9form.gen9sort2.value == 'Target')
	{
		var order_selection = document.getElementById("ordering2");
		order_selection.options[3].selected = true;
	}
	else if (document.gen9form.gen9sort2.value == 'Scaffold')
	{
		var order_selection = document.getElementById("ordering2");
		order_selection.options[4].selected = true;
	}
}

function enableMeetingComments(DesignID)
{
	new Effect.Appear("meeting-comments-" + DesignID, { duration: 0.0 } );
	new Effect.Fade("meeting-comments-" + DesignID + "-header", { duration: 0.0, queue: { position: '0', scope: 'task' } } );	
}

function toggleNewDesigns(elem)
{
	var b;
	if (elem.innerHTML == 'Only recent designs')
	{
		b = false;
		elem.innerHTML = 'All designs';
	}
	else
	{
		b = true;
		elem.innerHTML = 'Only recent designs';
	}
	
	for (i = 1; i <= 169; i++)
	{
		var old_div = document.getElementById("d" + i);
		if (b == false)
		{
			new Effect.Fade(old_div, { duration: 0.0 } );
		}
		else
		{
			new Effect.Appear(old_div, { duration: 0.0 } );
				
		}
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
	window.location.hash="d" + document.gen9form.DesignID.value;
}
if (document.gen9form.Gen9Error.value != "")
{
	alert(document.gen9form.Gen9Error.value);
}

function goToDesign(txtbox, e)
{
	var keycode;
	if (window.event)
	{
		keycode = window.event.keyCode;
	}
	else if (e)
	{
		keycode = e.which;
	}
	else return true;
	
	if (keycode == 13)
	{
		if(/^\d+$/.test(txtbox.value)) {
			window.location.hash="#";
			window.location.hash="d" + txtbox.value;
		}
		return false;
	}
	else
		return true;
}

function jumpToDesign(designID)
{
	showPage("browse");
	window.location.hash="#";
	window.location.hash="d" + designID;
}

function showFilters()
{
	var tbl = document.getElementById('filter_table');
	if(tbl.getStyle('display') == 'none')
	{
		new Effect.Appear("filter_table", { duration: 0.0 } );
	}
	else
	{
		new Effect.Fade( "filter_table", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
	}
}
function show_file_links(DesignID)
{
	var elemname = 'file-links-row-' + DesignID;
	var row = document.getElementById(elemname );
	if(row.getStyle('display') == 'none')
	{
		new Effect.Appear(elemname , { duration: 0.0 } );
	}
	else
	{
		new Effect.Fade( elemname , { duration: 0.0, queue: { position: '0', scope: 'task' } } );
	}	
}
function copyPageFormValues(elem)
{
	design_form = elem.form;
	design_form.Gen9Page.value = document.gen9form.Gen9Page.value;
	design_form.query.value = "Gen9Comment";
	design_form.gen9sort1.value = document.gen9form.gen9sort1.value;
	design_form.gen9sort2.value = document.gen9form.gen9sort2.value;
}

function copyPageFormValuesForMeeting(elem)
{
	design_form = elem.form;
	design_form.Gen9Page.value = document.gen9form.Gen9Page.value;
	design_form.query.value = "Gen9Comment";
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

function showDesigns()
{
	
	var all_divs = document.getElementsByClassName('general-design-cl');
	for (i = 0; i < all_divs.length; i++)
	{
		var particular_div = all_divs[i];
		if(particular_div.getStyle('display') == 'none')
		{
			new Effect.Appear(particular_div, { duration: 0.0 } );
		}
	}
}

function toggleDesigns(t, elem, group_type)
{
	var b;
	if (elem.innerHTML.substring(0, 4) == 'Hide')
	{
		b = false;
		elem.innerHTML = 'Show' + elem.innerHTML.substring(4);
	}
	else
	{
		b = true;
		elem.innerHTML = 'Hide' + elem.innerHTML.substring(4);
	}
	
	var all_divs = document.getElementsByClassName(t + '_' + group_type + '-cl');
	for (i = 0; i < all_divs.length; i++)
	{
		var particular_div = all_divs[i];
		if(b == true)
		{
			new Effect.Appear(particular_div, { duration: 0.0 } );
		}
		else
		{
			new Effect.Fade(particular_div, { duration: 0.0 } );
		}
	}
}


