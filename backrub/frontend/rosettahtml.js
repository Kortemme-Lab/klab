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
			// the forward slash references the model number
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
	designedCheckboxes = document.getElementsByName("JmolDesigned")
	premutatedCheckboxes = document.getElementsByName("JmolPremutated")	
		                                      	
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
		
		if (i > 0 && premutatedCheckboxes.length > 0)
		{
			if (premutatedCheckboxes[i - 1].checked && showStructure)
			{
				_updateResidues(displayString, index, jmolMutatedResidues);
			}
			else
			{
				_updateResidues(hideString, index, jmolMutatedResidues);
			}
		}
		if (i > 0 && designedCheckboxes.length > 0)
		{
			if (designedCheckboxes[i - 1].checked && showStructure)
			{
				_updateResidues(displayString, index, jmolDesignedResidues);
			}
			else
			{
				_updateResidues(hideString, index, jmolDesignedResidues);
			}
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
