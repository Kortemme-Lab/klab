subpages = ["jobadmin", "diskstats"]

function showPage(page)
{
	foundDiv = false;
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
	}
	else
	{
		alert("Cannot find div " + page)
	}
}
