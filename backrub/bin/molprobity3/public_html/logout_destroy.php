<?php # (jEdit options) :folding=explicit:collapseFolds=1:
/*****************************************************************************
    This page destroys all user data for the current session.
    
INPUTS (via Post ONLY):
    confirm       must be TRUE in order for the operation to proceed

*****************************************************************************/
// EVERY *top-level* page must start this way:
// 1. Define it's relationship to the root of the MolProbity installation.
// Pages in subdirectories of lib/ or public_html/ will need more "/.." 's.
    if(!defined('MP_BASE_DIR')) define('MP_BASE_DIR', realpath(dirname(__FILE__).'/..'));
// 2. Include core functionality - defines constants, etc.
    require_once(MP_BASE_DIR.'/lib/core.php');
// 3. Restore session data. If you don't want to access the session
// data for some reason, you must call mpInitEnvirons() instead.
    mpStartSession();
// 4. For pages that want to see the session but not change it, such as
// pages that are refreshing periodically to monitor a background job.
    #mpSessReadOnly();

# MAIN - the beginning of execution for this page
############################################################################
if($_POST['confirm'])
{
    // Must log first or we lose our session ID for the log!
    mpLog("logout-session:User cleaned up all session files and left the site");
    mpDestroySession();
}

// Start the page: produces <HTML>, <HEAD>, <BODY> tags
echo mpPageHeader("Thanks!");

############################################################################
?>
<center>
Thanks for using MolProbity!
All your data files have been erased.
<br>
<br>
<br>
<br>
<a href="index.php"><img src="img/mplogo_clear.png"><br>Start another MolProbity session</a>
<br>
<br>
<br>
<br>
<a href="http://kinemage.biochem.duke.edu/"><img src="img/kinhome.gif"><br>Return to the Richardson lab (Kinemage) home page</a>
</center>
<?php echo mpPageFooter(); ?>
