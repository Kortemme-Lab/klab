<?php # (jEdit options) :folding=explicit:collapseFolds=1:
/*****************************************************************************
    This page is the command center for MolProbity.
    It is the only page to appear in the browser URL bar, with few exceptions.
    
    This page provides a clean model-view-controller architecture
    in cooperation with lib/event-page.php.
    
    The pages that do the actual work reside in pages/ and are referred to
    as "delegates", because the work and UI is delegated to them from here.
    (They are also called "pages", obviously.)
*****************************************************************************/
// EVERY *top-level* page must start this way:
// 1. Define it's relationship to the root of the MolProbity installation.
// Pages in subdirectories of lib/ or public_html/ will need more "/.." 's.
    if(!defined('MP_BASE_DIR')) define('MP_BASE_DIR', realpath(dirname(__FILE__).'/..'));
// 2. Include core functionality - defines constants, etc.
    require_once(MP_BASE_DIR.'/lib/core.php');
// 3. Restore session data. If you don't want to access the session
// data for some reason, you must call mpInitEnvirons() instead.
    $isNewSess = mpStartSession(true);
// New sessions must define where they start!
// Default is welcome page unless URL is like index.php?start=____
    if($isNewSess)
    {
        if(date('F j') == 'April 1') pageGoto("april_fools.php");
        else switch($_REQUEST['start'])
        {
            case "sitemap":     pageGoto("sitemap.php"); break;
            case "xray":        pageGoto("helper_xray.php"); break;
            default:            pageGoto("welcome.php"); break;
            //default:            pageGoto("april_fools.php"); break;
        }
    }
    


// Process submitted event /////////////////////////////////////////////////////
$page = end($_SESSION['pages']); // not a ref; read only
$delegate = makeDelegateObject();
if($isNewSess)
{
  // new code for directly telling molprobity to fetch a pdb file with a get in the html call
  if (isset($_GET["pdbCode"])) {
    $pdbCode = $_GET["pdbCode"];
    mpLog("new-session:New session started by calling MolProbity directly with ".$pdbCode);
    mpLog("browser-detect:".$_SERVER['HTTP_USER_AGENT']);
    mpLog("refered-by:".$_SERVER['HTTP_REFERER']);
    if (strlen($pdbCode) > 10) {
      mpLog("bad-pdb:Invalid PDB code detected.");
      $pdbCode = "";
    }
    $_SESSION['bgjob']['pdbCode']       = $pdbCode;
    $_SESSION['bgjob']['isCnsFormat']   = false;
    $_SESSION['bgjob']['ignoreSegID']   = false;
    $_SESSION['bgjob']['biolunit']      = false;
    $_SESSION['bgjob']['eds_2fofc']     = false;
    $_SESSION['bgjob']['eds_fofc']      = false;
    // launch background job
    pageCall("job_progress.php");
    launchBackground(MP_BASE_DIR."/jobs/addmodel.php", "upload_pdb_done.php", 3);
  } else {
    mpLog("new-session:New interactive user session started on the web");
    mpLog("browser-detect:".$_SERVER['HTTP_USER_AGENT']);
    mpLog("refered-by:".$_SERVER['HTTP_REFERER']);
  }
}
elseif(isset($_REQUEST['eventID']))
{
    $eid = $_REQUEST['eventID'] + 0;
    if(isset($page['handlers'][$eid]))
    {
        $funcName   = $page['handlers'][$eid]['funcName'];
        $funcArgs   = $page['handlers'][$eid]['funcArgs'];
        // We use a variable function name here to call the handler.
        //$delegate->$funcName($funcArg, $_REQUEST);
        // Now this is *real* voodoo:
        call_user_func_array(array(&$delegate, $funcName), $funcArgs);
        
        // In case we changed $_SESSION but display() calls mpSessReadOnly()
        // This save won't stop the session from being automatically saved again
        // after display() and the end of the page.
        // (Though display() shouldn't write to $_SESSION anyway, except events!)
        // However: this can truncate the session file just as a background job
        // is starting, so launchBackground() makes the session read-only,
        // so this call does nothing in that case.
        mpSaveSession();
    }
    else
    {
        $GLOBALS['badEventOccurred'] = true;
        mpLog("bad-event:Event ID '$eid' is unknown for page $page[delegate]. No action taken.");
    }
}

// Clean up from event processing //////////////////////////////////////////////
clearEventHandlers();   // events defined by previous display() are not valid

// Handle a return from a called page //////////////////////////////////////////
// This should now be possible but has not been implemented yet.
// pageReturn() should set global variables ($page_return_callback and _argument)
// and there should be a while() loop here to process multi-level returns.

// Display user interface //////////////////////////////////////////////////////
$page = end($_SESSION['pages']); // not a ref; read only
$delegate = makeDelegateObject();
// Can't call mpSessReadOnly() or we won't be able to create events.
// Other than events, display() shouldn't write to the session though.
// Not a variable function name; UI function is always 'display()'
$delegate->display($page['context']); // creates a HTML UI

mpLogPath($page['delegate']); // for tracking the user's path thru the system later
?>
