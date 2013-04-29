var subpages;
if (document.gen9form.Username.value == 'oconchus')
{
	subpages = ["ChildPlates", "DNATranslation"]
}
else
{
	subpages = ["ChildPlates", "DNATranslation"]
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
						document.gen9form.Gen9DNAPage.value = page
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
			move_plate_info();	
			return;
		}
		else
		{
			page = subpages[0]
		}
	}
	alert("Cannot find div " + page)
}
showPage(subpages[0])

function set_fade()
{
	plate_ids = ['Child1', 'Child2']
	for (var j = 0; j < plate_ids.length; j++)
	{
		plate_id = plate_ids[j];
		rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
		for (i = 0 ; i < 2; i++)
		{
			for (y = 0; y < rows.length; y++)
			{
				for (x = 1; x <= 12; x++)
				{
					var span_id;
					if (x < 10)
					{
						span_id = '#' + plate_id + '_' + rows[y] + '_0' + x;
					}
					else
					{
						span_id = '#' + plate_id + '_' + rows[y] + '_' + x;
					}
					$(span_id + '_info').fadeTo(0, 0.75);
				}
			}
		}
	}
}

function show_gen9well_legend(visib)
{
	if (visib)
	{
		$('#gen9well_legend-show').hide();
		$('#gen9well_legend-hide').show();
		$('#gen9well_legend_contents').show();
	}
	else{
		$('#gen9well_legend-show').show();
		$('#gen9well_legend-hide').hide();
		$('#gen9well_legend_contents').hide();		
	}
	move_plate_info();
}

function move_plate_info()
{
	plate_ids = ['Child1', 'Child2']
	for (var j = 0; j < plate_ids.length; j++)
	{
		plate_id = plate_ids[j];
		rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
		for (i = 0 ; i < 2; i++)
		{
			for (y = 0; y < rows.length; y++)
			{
				for (x = 1; x <= 12; x++)
				{
					var span_id;
					if (x < 10)
					{
						span_id = '#' + plate_id + '_' + rows[y] + '_0' + x;
					}
					else
					{
						span_id = '#' + plate_id + '_' + rows[y] + '_' + x;
					}
					var well_position = $(span_id + '_well').offset();
					$(span_id + '_info').css({position: 'absolute'}).css({top: well_position['top']}).css({left: well_position['left']}).css('z-index', 1).show();
					$(span_id + '_well').css('z-index', 3);
					
				}
			}
		}
	}
}

function getDesignPyMOLFile(DesignID)
{
	var iframe = document.createElement("iframe"); 
	iframe.src = 'http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py?query=Gen9File&amp;DesignID=' + DesignID + '&amp;download=PSE'; 
	iframe.style.display = "none"; 
	document.body.appendChild(iframe);
}

function getManualDesignsPyMOLFile(DesignID)
{
	var iframe = document.createElement("iframe"); 
	iframe.src = 'http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py?query=Gen9File&amp;DesignID=' + DesignID + '&amp;download=ManualDesignsPSE'; 
	iframe.style.display = "none"; 
	document.body.appendChild(iframe);
}

var details_dialog;

$(document).ready(function() {
	
	details_dialog = $("#dialog").dialog({
		autoOpen: false,
		width: 800,
	});
	 
	set_fade();
	$(window).resize(function() {
		move_plate_info();	
	});
	window.setTimeout(move_plate_info, 10);

	$('#gen9well_legend_contents').appendTo('#gen9well_legend')
	
	$('#dna_translator').keypress(function (event) {
		if (event.which == 13)
		{
			var allowed = {A: true, C: true, G: true, T: true}
			allowed[String.fromCharCode(10)] = true;
			allowed[String.fromCharCode(13)] = true;
			
			var dna_sequence = $('#dna_translator').val();
			dna_sequence = dna_sequence.replace(/\\n/g, '');
			dna_sequence = dna_sequence.replace(/\\r/g, '');
			
			dna_sequence = dna_sequence.replace(/ /g, '').toUpperCase();
			success = true
			
			for (x = 0; x < dna_sequence.length; x++){
				var c = dna_sequence[x];
				if (allowed[dna_sequence[x]] != true)
				{
					success = false;
					break;
				}
			}
			if (!success)
			{
				$("#dna_translator_results").val("Non-DNA characters found in the string.");
				return false;
			}
			$.post("/backrub/frontend/ajax/gen9dna_ajax.py", {request : 'DNATranslation', Sequence : dna_sequence}, function(result) {
				//alert(image_data.length);
				$("#dna_translator_results").val(result['Translation']);
	
			});
			return false;
		}
	});
	
	$('[class^="Gen9DNAWell"]').click(function() {
		var this_class = $(this).attr('class');
		var this_id = $(this).parent().attr('id');
		
		var id_tokens = this_id.split('_')
		var plate_name = id_tokens[0]
		var row_name = id_tokens[1]
		var column_name = id_tokens[2]
		
		plate_row = "row_" + plate_name + "_" + row_name;
		var PlateID = null;
		if (plate_name == "Child1")
		{
			PlateID = 1;
		}
		else if (plate_name == "Child2")
		{
			PlateID = 2;
		}
		DesignID = parseInt(this_class.split('_')[1]);
		
		$.post("/backrub/frontend/ajax/gen9dna_ajax.py", {request : 'DesignDetails', DesignID : DesignID, PlateID: PlateID}, function(html_contents) {
			details_dialog.dialog("option", 'title', 'Manual design ' + DesignID + ' (child plates ' + row_name + column_name + ')');
			details_dialog.dialog("option", 'width', 1100);
			details_dialog.html(html_contents)
			details_dialog.dialog({ position: { my: "left top", at: "left bottom+50",  of: "#" + plate_row} });
			details_dialog.dialog("open");
		});
		return false;
	});
	
	
	$('[class^="Gen9DNAPyMOL"]').click(function() {
		alert('here')
		this_id = $(this).attr('class');
		DesignID = parseInt(this_id.split('_')[1]);
		var iframe = document.createElement("iframe"); 
		iframe.src = 'http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py?query=Gen9File&amp;DesignID=' + DesignID + '&amp;download=PSE'; 
		iframe.style.display = "none"; 
		document.body.appendChild(iframe);
		return false;
	});

	
	if (false)
	{
		Jmol.setDocument(0);
		$("a").click(function(e) {
			// prevents click from reloading page
			e.preventDefault();
	
			$.post("/backrub/frontend/ajax/gen9dna_ajax.py", {small_molecule: 'TEP'}, function(image_data) {
				//alert(image_data.length);
				$("#motif_interaction_diagram").attr('src', "data:image/png;base64,"+image_data);
	
			});
	
			// make ajax call
			/*$.ajax({
				url: "/backrub/frontend/ajax/gen9dna_ajax.py",
				type: "post",
				//data: {},//'rating': 'teststring'},
				dataType: "image/png",
				//contentType: "image/png",
				success: function(image_data) {
				//success: function(response) {
					//alert(response["average"]);
					alert(image_data)
					alert(image_data.length)
					$("#motif_interaction_diagram").attr('src', image_data);
					//$("#motif_interaction_diagrams").html(response["average"])
	
				},
				error: function(xhr, ajaxOptions, thrownError) {
					alert('Error #' + xhr.status + ': ' + thrownError);
				}
			});*/
			
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
			//Jmol.script(jmolApplet0, 'load DATA "mydata"\n ' +  '\nEND "mydata"');
			//Jmol.script(jmolApplet0, 'load /rosettaweb/test.pse;')
			//Jmol.script(jmolApplet0, 'load /rosettaweb/pse320.png;')
			
			//Jmol.script(jmolApplet0, 'load /rosettaweb/1hxw.png;')
			//Jmol.script(jmolApplet0, 'load /rosettaweb/100_variants.pse;')
			
			Jmol.script(jmolApplet0, 'load /rosettaweb/2I0L_A_C_V2006.pdb;')
			//Jmol.script(jmolApplet0, 'load /rosettaweb/2I0L_A_C_V20062.pdb.gz;')
			Jmol.script(jmolApplet0, 'console')
			// select 319:a; color green
			//Jmol.script(jmolApplet0, 'color group; color monomer; cartoon; wireframe off; cpk off; backbone 0.2; backbone on;')
			$("#input_structure").html(jmolApplet0._code)
		});
	}
});
//make ajax call
//$.post("/backrub/frontend/ajax/gen9dna_ajax.py", {rating: "teststring"}, function(json_text) {
//	alert(json_text["average"]);
//	$("#motif_interaction_diagram").html(json_text["average"])
//});



