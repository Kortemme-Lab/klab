var subpages;
if (document.gen9form.Username.value == 'oconchus')
{
	subpages = ["browse", "rankmapping", "manualdesigns"]
}
else
{
	subpages = ["browse", "rankmapping", "manualdesigns"]
}

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
if (document.gen9form.gen9mode.value != null && document.gen9form.gen9mode.value == 'top10')
{
	document.getElementsByName("Show_Top_10_Options")[0].checked = true;
	/*if (document.gen9form.top10scheme.value != null)
	{
		
	}*/	
	toggleTop10Options();
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

function reopen_page_with_top10()
{
	if (document.getElementsByName("Show_Top_10_Options")[0].checked)
	{
		var o1 = document.getElementById("ordering1");
		
		var ordering1 = o1.options[o1.selectedIndex].value;
		var o2 = document.getElementById("ordering2");
		var ordering2 = o2.options[o2.selectedIndex].value;
		
		var t1 = document.getElementById("Top10SmallMolecules");
		var molecule= t1.options[t1.selectedIndex].value;
		if (molecule != '')
		{
			molecule = '&top10mol=' + molecule
		}
		
		var t2 = document.getElementById("Top10RankingScheme");
		var scheme= t2.options[t2.selectedIndex].value;
		if (scheme != '')
		{
			scheme = '&top10scheme=' + scheme
		}
		
		var t3 = document.getElementById("Top10DesignType");
		var tttype= t3.options[t3.selectedIndex].value;
		if (tttype != '')
		{
			tttype = '&top10type=' + tttype
		}
		window.open("?query=Gen9&gen9mode=top10" + molecule + scheme + tttype + "&gen9sort1=" + ordering1 + "&gen9sort2=" + ordering2, "_self");
	}
	else
	{
		reopen_page_with_sorting();
	}
}



if (document.gen9form.DesignID.value != "")
{
	window.location.hash="d" + document.gen9form.DesignID.value;
}
if (document.gen9form.Gen9Error.value != "")
{
	alert(document.gen9form.Gen9Error.value);
}

function goToSmallMolecule(SmallMoleculeID)
{
	window.location.hash="#";
	window.location.hash="aSmallMolecule" + SmallMoleculeID;
	return false;
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

function copyGenericPageFormValues(elem)
{
	design_form = elem.form;
	design_form.Gen9Page.value = document.gen9form.Gen9Page.value;
	design_form.gen9sort1.value = document.gen9form.gen9sort1.value;
	design_form.gen9sort2.value = document.gen9form.gen9sort2.value;
	design_form.gen9mode.value = document.gen9form.gen9mode.value;
	design_form.top10mol.value = document.gen9form.top10mol.value;
	design_form.top10scheme.value = document.gen9form.top10scheme.value;
	design_form.top10type.value = document.gen9form.top10type.value;
}

function copyPageFormValues(elem)
{
	design_form = elem.form;
	design_form.query.value = "Gen9Comment";
	copyGenericPageFormValues(elem);
}

function copyPageFormValuesForMeeting(elem)
{
	design_form = elem.form;
	design_form.query.value = "Gen9Comment";
	copyGenericPageFormValues(elem);
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

function showScaffoldDetails(designID, show)
{
	var plus_span = document.getElementById('scaffold-details-' + designID + '-show');
	var minus_span = document.getElementById('scaffold-details-' + designID + '-hide');
	var details_div = document.getElementById('scaffold-details-' + designID + '-div');
	if (show)
	{
		new Effect.Fade(plus_span, { duration: 0.0 } );
		new Effect.Appear(minus_span, { duration: 0.0 } );
		new Effect.Appear(details_div, { duration: 0.0 } );
	}
	else
	{
		new Effect.Fade(minus_span, { duration: 0.0 } );
		new Effect.Fade(details_div, { duration: 0.0 } );
		new Effect.Appear(plus_span, { duration: 0.0 } );
	}
}

function showUserComments(designID, show)
{
	var plus_span = document.getElementById('user-comments-' + designID + '-show');
	var minus_span = document.getElementById('user-comments-' + designID + '-hide');
	var details_div = document.getElementById('user-comments-' + designID + '-div');
	if (show)
	{
		new Effect.Fade(plus_span, { duration: 0.0 } );
		new Effect.Appear(minus_span, { duration: 0.0 } );
		new Effect.Appear(details_div, { duration: 0.0 } );
	}
	else
	{
		new Effect.Fade(minus_span, { duration: 0.0 } );
		new Effect.Fade(details_div, { duration: 0.0 } );
		new Effect.Appear(plus_span, { duration: 0.0 } );
	}
}

function toggleTop10Options()
{
	var b = document.getElementsByName("Show_Top_10_Options")[0].checked;
	var options_span = document.getElementById('Top10Options');
	
	if (b == true)
	{
		new Effect.Appear(options_span, { duration: 0.0 } );
	}
	else
	{
		new Effect.Fade(options_span, { duration: 0.0 } );
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


