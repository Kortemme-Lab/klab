<?php # (jEdit options) :folding=explicit:collapseFolds=1:
/*****************************************************************************
    This page displays statistics about the just-uploaded PDB model.
*****************************************************************************/
// We use a uniquely named wrapper class to avoid re-defining display(), etc.
class upload_other_done_delegate extends BasicDelegate {
    
#{{{ display - creates the UI for this page
############################################################################
/**
* Context is an array containing:
*   type            the type of file uploaded. One of 'map', ...
*   errorMsg        an error diagnosis from failed PDB upload
*   mapName         the name of the just-added map file (map upload only)
*/
function display($context)
{
    if(isset($context['errorMsg']))
    {
        echo $this->pageHeader("File upload failed");
        echo "For some reason, your file could not be uploaded.\n<ul>\n";
        echo "<li>$context[errorMsg]</li>\n";
        echo "</ul>\n";
        echo "<p>" . makeEventForm("onTryAgain");
        echo "<table border='0' width='100%'><tr>\n";
        echo "<td align='left'><input type='submit' name='cmd' value='&lt; Try again'></td>\n";
        echo "<td align='right'><input type='submit' name='cmd' value='Cancel'></td>\n";
        echo "</tr></table>\n</form></p>\n";
        echo $this->pageFooter();
    }
    else // upload was OK
    {
        $type = $context['type'];
        if($type == 'kin')          $this->displayKin($context);
        elseif($type == 'map')      $this->displayMap($context);
        elseif($type == 'hetdict')  $this->displayHetDict($context);
    }
}
#}}}########################################################################

#{{{ displayKin
############################################################################
function displayKin($context)
{
    echo $this->pageHeader("Kinemage $context[kinName] added");
    echo "Your kinemage has been uploaded. You may now view it in KiNG:\n";
    echo "<ul><li>".linkKinemage($context['kinName'])."</li></ul>\n";
    echo "<p>" . makeEventForm("onReturn");
    echo "<input type='submit' name='cmd' value='Continue &gt;'>\n</form></p>\n";
    echo $this->pageFooter();
}
#}}}########################################################################

#{{{ displayMap
############################################################################
function displayMap($context)
{
    echo $this->pageHeader("Map $context[mapName] added");
    echo "<p>The following electron density maps are now available:\n";
    echo "<ul>\n";
    foreach($_SESSION['edmaps'] as $map)
    {
        $mapPath = "$_SESSION[dataDir]/".MP_DIR_EDMAPS."/$map";
        echo "<li><b>$map</b> (".formatFilesize(filesize($mapPath)).")</li>\n";
    }
    echo "</ul>\n</p>\n";
    echo "<p>" . makeEventForm("onReturn");
    echo "<input type='submit' name='cmd' value='Continue &gt;'>\n</form></p>\n";
    echo $this->pageFooter();
}
#}}}########################################################################

#{{{ displayHetDict
############################################################################
function displayHetDict($context)
{
    echo $this->pageHeader("Custom het dictionary added");
    echo "<p>Your custom heterogen dictionary will be used for all future work in this session.</p>\n";
    echo "<p>" . makeEventForm("onReturn");
    echo "<input type='submit' name='cmd' value='Continue &gt;'>\n</form></p>\n";
    echo $this->pageFooter();
}
#}}}########################################################################

#{{{ onTryAgain
############################################################################
/**
* Documentation for this function.
*/
function onTryAgain()
{
    if($_REQUEST['cmd'] == '< Try again')
        pageGoto("upload_setup.php");
    else
        pageReturn();
}
#}}}########################################################################

#{{{ a_function_definition - sumary_statement_goes_here
############################################################################
/**
* Documentation for this function.
*/
//function someFunctionName() {}
#}}}########################################################################

}//end of class definition
?>
