var subpages;
var DocumentIsReady = false;
if (document.gen9form.Username.value == 'oconchus')
{
	subpages = ["browse", "rankmapping"]
}
else
{
	subpages = ["browse", "rankmapping"]
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



function show_file_links_new(DesignID)
{
	var elemname = 'file-links-div-' + DesignID;
	$('.' + elemname).each(function(index){
		$(this).toggle()
	});
	/*
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
	}*/
}



function enableMeetingComments(DesignID)
{
	$('#' + "meeting-comments-" + DesignID).show();
	$('#' + "meeting-comments-" + DesignID + "-header").hide();
	
	//new Effect.Appear("meeting-comments-" + DesignID, { duration: 0.0 } );
	//new Effect.Fade("meeting-comments-" + DesignID + "-header", { duration: 0.0, queue: { position: '0', scope: 'task' } } );	
}


function toggleManualDesigns(elem)
{
	var b;
	if (elem.innerHTML == 'Only manually designed')
	{
		b = false;
		elem.innerHTML = 'All designs';
	}
	else
	{
		b = true;
		elem.innerHTML = 'Only manually designed';
	}
	$('.no-manual-designs').each(function(index){
		if(b == true) {	$(this).show()}
		else{$(this).hide()}
	});
	updateDesignCounter();
	/*var all_divs = document.getElementsByClassName('no-manual-designs');
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
	}*/
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
			$('#d' + i).hide();
			//new Effect.Fade(old_div, { duration: 0.0 } );
		}
		else
		{
			$('#d' + i).show();
			//new Effect.Appear(old_div, { duration: 0.0 } );
		}
	}
	updateDesignCounter();
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
	$('#filter_table').toggle();
	/*var tbl = document.getElementById('filter_table');
	if(tbl.getStyle('display') == 'none')
	{
		new Effect.Appear("filter_table", { duration: 0.0 } );
	}
	else
	{
		new Effect.Fade( "filter_table", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
	}*/
}
function showHelp()
{
	$('#help_text').toggle();
	/*var tbl = document.getElementById('help_text');
	if(tbl.getStyle('display') == 'none')
	{
		new Effect.Appear("help_text", { duration: 0.0 } );
	}
	else
	{
		new Effect.Fade( "help_text", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
	}*/
}
function show_file_links(DesignID)
{
	$('#' + 'file-links-row-' + DesignID).toggle();
	/*var elemname = 'file-links-row-' + DesignID;
	var row = document.getElementById(elemname );
	if(row.getStyle('display') == 'none')
	{
		new Effect.Appear(elemname , { duration: 0.0 } );
	}
	else
	{
		new Effect.Fade( elemname , { duration: 0.0, queue: { position: '0', scope: 'task' } } );
	}*/	
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

function showScaffoldDetails(DesignID, show)
{
	var plus_span = 'scaffold-details-' + DesignID + '-show';
	var minus_span = 'scaffold-details-' + DesignID + '-hide';
	var details_div = 'scaffold-details-' + DesignID + '-div';
	if (show)
	{
		if ($('#' + details_div).children().length == 0)
		{
			$.post("/backrub/frontend/ajax/gen9ajax.py", {request: 'DesignResidueDetails', DesignID: DesignID}, function(html_content) {
				$('#' + details_div).html(html_content);
				$('#' + plus_span).hide();
				$('#' + minus_span).show();
				$('#' + details_div).show();
			});
		}
		else{
			$('#' + plus_span).hide();
			$('#' + minus_span).show();
			$('#' + details_div).show();
		}
	}
	else
	{
		$('#' + plus_span).show();
		$('#' + minus_span).hide();
		$('#' + details_div).hide();
	}
}

function updateDesignCounter()
{
	l = getNumberOfVisibleDesigns();
	$('#DesignCounter').html('Designs (' + l[0] + ' total, ' + l[1] + ' shown)');
}

function getNumberOfVisibleDesigns()
{
	total = 0;
	visible_count = 0;
	$('.generic_design_class').each(function(index){
		if ($(this).is(":visible"))
		{
			visible_count += 1;
		}
		total += 1;
	});
	return [total, visible_count];
}

function addCommentToDatabase(CommentType, CommentMaker, DesignID)
{
	var rating;
	var comments;
	if (CommentMaker == "User")
	{
		if (CommentType == "Design")
		{
			rating = $('select[name=ajax-user-design-rating-' + DesignID + ']').val();
			comments = $('textarea[name=ajax-user-design-comments-' + DesignID + ']').val();
		}
		else if (CommentType == "Scaffold")
		{
			rating = $('select[name=ajax-user-scaffold-rating-' + DesignID + ']').val();
			comments = $('textarea[name=ajax-user-scaffold-comments-' + DesignID + ']').val();
		}
	}
	else if (CommentMaker == "Meeting")
	{
		if (CommentType == "Design")
		{
			rating = $('select[name=ajax-meeting-design-rating-' + DesignID + ']').val();
			comments = $('textarea[name=ajax-meeting-design-comments-' + DesignID + ']').val();
		}
		else if (CommentType == "Scaffold")
		{
			rating = $('select[name=ajax-meeting-scaffold-rating-' + DesignID + ']').val();
			comments = $('textarea[name=ajax-meeting-scaffold-comments-' + DesignID + ']').val();
		}
	}
	
	if (rating == 'None' || rating.replace(/^\s+|\s+$/g, '') == '')
	{
		rating = null;
	}
	if (comments.replace(/^\s+|\s+$/g, '') == '')
	{
		comments = null;
	}
	
	data = {
		request			: 'AddComment',
		CommentType		: CommentType,
		CommentMaker	: CommentMaker,
		DesignID		: DesignID,
		Username		: document.gen9form.Username.value,
		Rating			: rating,
		Comments		: comments,
	}
	
	$.post("/backrub/frontend/ajax/gen9ajax.py", data, function(html_content) {
		$('#comments-for-design-' + DesignID).html(html_content);
		$.post("/backrub/frontend/ajax/gen9ajax.py", {request: 'GetHeaderCSSClasses', DesignID : DesignID}, function(css_data) {
			
			if ('design_tr_class' in css_data)
			{
				$('#design-header-' + DesignID).removeClass().addClass(css_data['design_tr_class']);
			}
			else
			{
				alert("Failed to update the design header color.")
			}
			if ('scaffold_tr_class' in css_data)
			{
				$('#scaffold-header-' + DesignID).removeClass().addClass(css_data['scaffold_tr_class']);
			}
			else
			{
				alert("Failed to update the scaffold header color.")
			}
		});
	});
}

function showUserComments(designID, show)
{
	var plus_span = 'user-comments-' + designID + '-show';
	var minus_span = 'user-comments-' + designID + '-hide';
	var details_div = 'user-comments-' + designID + '-div';
	if (show)
	{
		$('#' + plus_span).hide();
		$('#' + minus_span).show();
		$('#' + details_div).show();
	}
	else
	{
		$('#' + plus_span).show();
		$('#' + minus_span).hide();
		$('#' + details_div).hide();
	}
	/*
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
	}*/
}

function toggleTop10Options()
{
	var b = document.getElementsByName("Show_Top_10_Options")[0].checked;
	var options_span = document.getElementById('Top10Options');
	
	if (b == true)
	{
		$('#Top10Options').show();
		//new Effect.Appear(options_span, { duration: 0.0 } );
	}
	else
	{
		$('#Top10Options').hide();
		//new Effect.Fade(options_span, { duration: 0.0 } );
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
	
	if(b == true)
	{
		$('.' + t + '_' + group_type + '-cl').show();
	}
	else
	{
		$('.' + t + '_' + group_type + '-cl').hide();		
	}
	updateDesignCounter();
	/*
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
	*/
}

var big_applet = false;
function LoadDesignModel(DesignID)
{
	if (DocumentIsReady)
	{
		Jmol.script(jmolApplet0, 'console off')
		if (false)
		{
			$.post("/backrub/frontend/ajax/gen9ajax.py", {request: 'DesignPDBContents', DesignID: DesignID}, function(PDBContents) {
			
				//$("#motif_interaction_diagram").attr('src', "data:image/png;base64,"+image_data);
				{
					Jmol.script(jmolApplet1, 'load DATA "mydata"\n ' + PDBContents + '\nEND "mydata"');
					Jmol.script(jmolApplet1, 'color group; color monomer; cartoon; wireframe off; cpk off; backbone 0.2; backbone on;')
					$("#design_jsmol_structure_big_div").html(jmolApplet1._code)
					Jmol.script(jmolApplet1, 'select 1:X; color cpk; wireframe only; wireframe 0.15; spacefill 23%');
				}
				{
					Jmol.script(jmolApplet0, 'load DATA "mydata"\n ' + PDBContents + '\nEND "mydata"');
					Jmol.script(jmolApplet0, 'color group; color monomer; cartoon; wireframe off; cpk off; backbone 0.2; backbone on;')
					$("#design_jsmol_structure_div").html(jmolApplet0._code)
					Jmol.script(jmolApplet0, 'select 1:X; color cpk; wireframe only; wireframe 0.15; spacefill 23%');
				}
				//Jmol.script(jmolApplet0, 'load ' + design_data['FilePath'] + ';')
				//Jmol.script(jmolApplet0, 'color group; color monomer; cartoon; wireframe off; cpk off; backbone 0.2; backbone on;')
				$("#design_jsmol_structure_panel").show()
			});
		}
		else
		{
			var bigmodeldata;
			//$.post("/backrub/frontend/ajax/gen9ajax.py", {request: 'DesignPDBContents', DesignID: DesignID}, function(PDBContents) {
			//	bigmodeldata = PDBContents;
				$.post("/backrub/frontend/ajax/gen9ajax.py", {request: 'newDesignPDBContents', DesignID: DesignID}, function(result) {
					//alert(bigmodeldata)
					//alert(result)
					//$("#motif_interaction_diagram").attr('src', "data:image/png;base64,"+image_data);
					{
						/*Jmol.script(jmolApplet1, 'load DATA "mydata"\n ' + bigmodeldata + '\nEND "mydata"');
						Jmol.script(jmolApplet1, 'color group; color monomer; cartoon; wireframe off; cpk off; backbone 0.2; backbone on;')
						$("#design_jsmol_structure_big_div").html(jmolApplet1._code)
						Jmol.script(jmolApplet1, 'select 1:X; color cpk; wireframe only; wireframe 0.15; spacefill 23%');*/
						
						/*Jmol.script(jmolApplet1, 'load DATA "mydata1"\n ' + '' + '\nEND "mydata1"');
						Jmol.script(jmolApplet1, 'load DATA "append mydata2"\n ' + result['model2'] + '\nEND "append mydata2"');
						Jmol.script(jmolApplet1, 'color group; color monomer; cartoon; wireframe off; cpk off; backbone 0.2; backbone on;')
						$("#design_jsmol_structure_big_div").html(jmolApplet1._code)
						Jmol.script(jmolApplet1, 'select 1:X; color cpk; wireframe only; wireframe 0.15; spacefill 23%');*/
					}
					{
						var JSmolInfo = {
								width: 256,
								height: 256,
								debug: false,
								color: "white",
								coverTitle: "Not loaded",
								serverURL: "../../rosettaweb/jsmol/jsmol.php",
								use: "HTML5",
								j2sPath: "../../rosettaweb/jsmol/j2s",
								readyFunction: null,
								defaultModel: null,
								console: "none",
								script: "set antialiasDisplay; background black;"
						}
						Jmol.getApplet("jmolApplet0", JSmolInfo);
						var JSmolInfo = {
								width: 712,
								height: 712,
								debug: false,
								color: "white",
								coverTitle: "Not loaded",
								serverURL: "../../rosettaweb/jsmol/jsmol.php",
								use: "HTML5",
								j2sPath: "../../rosettaweb/jsmol/j2s",
								readyFunction: null,
								defaultModel: null,
								console: "none",
								script: "set antialiasDisplay; background black;"
						}
						Jmol.getApplet("jmolApplet1", JSmolInfo);
						
						//alert(result['script'].length)
						
						full_script = result['script'].join(" ")
						Jmol.script(jmolApplet0, full_script);
						Jmol.script(jmolApplet1, full_script);
						
						/*for (var i = 0; i < result['script'].length; i++) {
							//if (i==1){break;}
							tscript = result['script'][i];
							tscript_len = tscript.length;
							if (tscript_len > 200)
							{
								//alert(tscript.substring(0, 100) + '\n...\n' + tscript.substring(tscript_len-100, tscript_len));
							}
							else
							{
								//alert(tscript);
							}
							Jmol.script(jmolApplet0, result['script'][i]);
						} */
						//alert(bigmodeldata)
						
						//Jmol.script(jmolApplet0, 'load data "mydata"\n ' + result['model1'] + '\nend "mydata"');
						//Jmol.script(jmolApplet0, 'load data "append mydata"\n ' + result['model2'] + '\nend "append mydata"');
						//Jmol.script(jmolApplet0, 'load data "append mydata"\n' + bigmodeldata + '\nend "append mydata"');
						
						//Jmol.script(jmolApplet0, 'frame all')
						$("#design_jsmol_structure_div").html(jmolApplet0._code)
						$("#design_jsmol_structure_big_div").html(jmolApplet1._code)
						//Jmol.showInfo(jmolApplet0, true);
						//Jmol.script(jmolApplet0, 'frame all; color group; color monomer; cartoon; wireframe off; cpk off; backbone 0.2; backbone on;')
						//$("#design_jsmol_structure_div").html(jmolApplet0._code)
						//Jmol.script(jmolApplet0, 'select 1:X; color cpk; wireframe only; wireframe 0.15; spacefill 23%');
					}
					//Jmol.script(jmolApplet0, 'load ' + design_data['FilePath'] + ';')
					//Jmol.script(jmolApplet0, 'color group; color monomer; cartoon; wireframe off; cpk off; backbone 0.2; backbone on;')
					$("#design_jsmol_structure_panel").show()
				});
			//});
		}
	}
}
$(document).ready(function() {
	// Set up PyMOL session download links
	// We use iframes as opening a new window (even though it closes automatically) breaks the JSmol applet
	$('[id^="PSELink-"]').click(function() {
		this_id = $(this).attr('id');
		DesignID = parseInt(this_id.split('-')[1]);
		var iframe = document.createElement("iframe"); 
		iframe.src = 'http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py?query=Gen9File&amp;DesignID=' + DesignID + '&amp;download=PSE'; 
		iframe.style.display = "none"; 
		document.body.appendChild(iframe);
		return false;
	});
	
	Jmol.setDocument(0);
	updateDesignCounter();
	DocumentIsReady = true;
	var JSmolInfo = {
			width: 256,
			height: 256,
			debug: false,
			color: "white",
			coverTitle: "Not loaded",
			serverURL: "../../rosettaweb/jsmol/jsmol.php",
			use: "HTML5",
			j2sPath: "../../rosettaweb/jsmol/j2s",
			readyFunction: null,
			defaultModel: null,
			console: "none",
			script: "set antialiasDisplay; background black;"
	}
	Jmol.getApplet("jmolApplet0", JSmolInfo);
	var JSmolInfo = {
			width: 712,
			height: 712,
			debug: false,
			color: "white",
			coverTitle: "Not loaded",
			serverURL: "../../rosettaweb/jsmol/jsmol.php",
			use: "HTML5",
			j2sPath: "../../rosettaweb/jsmol/j2s",
			readyFunction: null,
			defaultModel: null,
			console: "none",
			script: "set antialiasDisplay; background black;"
	}
	Jmol.getApplet("jmolApplet1", JSmolInfo);
	
	
	$(".close_jsmol").click(function(e) {
		if ($("#design_jsmol_structure_panel").is(":visible"))
		{
			$("#design_jsmol_structure_panel").hide()		
		}
		if ($("#design_jsmol_structure_big_panel").is(":visible"))
		{
			$("#design_jsmol_structure_big_panel").hide()		
		}			
	});
	$(".minimize_jsmol").click(function(e) {
		if ($("#design_jsmol_structure_big_panel").is(":visible"))
		{
			$("#design_jsmol_structure_big_panel").hide()		
			big_applet = false;
			$("#design_jsmol_structure_panel").show();
		}
	});
	$(".maximize_jsmol").click(function(e) {
		if ($("#design_jsmol_structure_panel").is(":visible"))
		{
			$("#design_jsmol_structure_panel").hide();
			big_applet = true;
			$("#design_jsmol_structure_big_panel").show()		
		}
		/*new_width = 44 + (($("#design_jsmol_structure_panel").width()-44)*2);
		new_height = 44 + (($("#design_jsmol_structure_panel").height()-44)*2); 
		
		Jmol.resizeApplet(jmolApplet0, "150%");
		
		$("#design_jsmol_structure_panel")
			.css('width', new_width + 'px')
			.css('height', new_height + 'px')
			.css("position","fixed")
			.css("left", ( $(window).width() - new_width - 10) + "px");

		$("#design_jsmol_structure_div")
			.css('width', $('#design_jsmol_structure_div').width()*2 + 'px')
			.css('height', $('#design_jsmol_structure_div').height()*2 + 'px')
			
		
		$("#design_jsmol_structure_panel_controls")
			.css("position","absolute")
			.css("left", ( $(design_jsmol_structure_panel).right() - 30) + "px")
			.css("z-index", 100);*/
		/*$("#design_jsmol_structure_div").css('width', new_width);
		$("#design_jsmol_structure_div").css('height', new_height);
		$("#design_jsmol_structure_div").css('left', '10px');
		
		$("#design_jsmol_structure_div").css("position","absolute");
		$("#design_jsmol_structure_div").css("top", ( $(window).height() - this.height() ) / 2+$(window).scrollTop() + "px");
		$("#design_jsmol_structure_div").css("left", ( $(window).width() - this.width() ) / 2+$(window).scrollLeft() + "px");
        */
		
		//$("#design_jsmol_structure_panel").hide()
	});
	
		
		
	//Jmol.script(jmolApplet0, 'load DATA "mydata"\n ' +  '\nEND "mydata"');
	//Jmol.script(jmolApplet0, 'load /rosettaweb/test.pse;')
	//Jmol.script(jmolApplet0, 'load /rosettaweb/pse320.png;')
	
	//Jmol.script(jmolApplet0, 'load /rosettaweb/1hxw.png;')
	//Jmol.script(jmolApplet0, 'load /rosettaweb/100_variants.pse;')
	
	//Jmol.script(jmolApplet0, 'load /rosettaweb/2I0L_A_C_V2006.pdb;')
	//Jmol.script(jmolApplet0, 'color group; color monomer; cartoon; wireframe off; cpk off; backbone 0.2; backbone on;')
	//Jmol.script(jmolApplet0, 'load /rosettaweb/2I0L_A_C_V20062.pdb.gz;')
	//Jmol.script(jmolApplet0, 'console')
	// select 319:a; cpk on; color green
	// select 5; color cpk; wireframe only; wireframe 0.15; spacefill 23%;
	


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

	if (document.gen9form.top10mol.value != null && document.gen9form.top10mol.value != "")
	{
		$('#Top10SmallMolecules').val(document.gen9form.top10mol.value);
	}
	if (document.gen9form.top10scheme.value != null && document.gen9form.top10scheme.value != "")
	{
		$('#Top10RankingScheme').val(document.gen9form.top10scheme.value);
	}
	if (document.gen9form.top10type.value != null && document.gen9form.top10type.value != "")
	{
		$('#Top10DesignType').val(document.gen9form.top10type.value);
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
	
	if (document.gen9form.Gen9Error.value != "")
	{
		alert(document.gen9form.Gen9Error.value);
	}
	
	// Navigate back to the correct div, ignoring user scrolling. If we wish to respect user scrolling, move this code to the document ready function.
	var design_hash_position = null;
	if (document.gen9form.DesignID.value != "")
	{
		design_hash_position = "d" + document.gen9form.DesignID.value;
	}
	else if (window.location.hash != "" && window.location.hash.indexOf('#d') == 0)
	{
		// Alternative method
		//var offset = $(window.location.hash).offset(); // window.location.hash works as an identifier for the div
		//window.scrollTo(offset.left, offset.top);
		design_hash_position = window.location.hash.substring(1) 
	}
	if (design_hash_position != null)
	{
		// override the default scroll function
		$(document).scroll( function() {
			if ($('#' + design_hash_position) != undefined)
			{
				window.scrollTo(0, $('#' + design_hash_position).position().top);
			}
			// restore the default scroll function
			$(document).unbind("scroll");
		 });
	}
});