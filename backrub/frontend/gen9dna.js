var subpages;
if (document.gen9form.Username.value == 'oconchus')
{
	subpages = ["test"]
}
else
{
	subpages = ["test"]
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


$(document).ready(function() {
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
	});
});
//make ajax call
//$.post("/backrub/frontend/ajax/gen9dna_ajax.py", {rating: "teststring"}, function(json_text) {
//	alert(json_text["average"]);
//	$("#motif_interaction_diagram").html(json_text["average"])
//});



