
var numMPM = 0; // Multiple Point Mutations
var numSeqTol = 0; // Mutation SeqTol


function startup(query) {
      if (query == "submit") {
          Nifty("ul#about li","big fixed-height");
          Nifty("div#box","big transparent fixed-height");
      }
      if (query == "index" || query == "login") {
          Nifty("div#login_box","big transparent fixed-height");
      }
      //updateCellSize2();
}


function ValidateFormRegister() {
        if ( document.myForm.username.value == "" ||
            document.myForm.firstname.value == "" ||
            document.myForm.lastname.value == "" ||
            document.myForm.password.value == "" ||
            document.myForm.confirmpassword.value == "") {
                      alert("Please complete all required fields.");
                      return false;
        }
        if ( document.myForm.email.value.indexOf("@") == -1 ||
            document.myForm.email.value.indexOf(".") == -1 ||
            document.myForm.email.value.indexOf(" ") != -1 ||
            document.myForm.email.value.length < 6 ) {
                        alert("Your email address is not valid.");
                        return false;
        }
        if ( document.myForm.password.value != document.myForm.confirmpassword.value  ) {
                alert("Your password does not match your password confirmation.");
                return false;
        }
        return true;
    }


function ValidateForm() {
    if ( document.submitform.JobName.value == "" ||
        ( document.submitform.PDBComplex.value == "" && document.submitform.PDBComplexURL.value == "" ) ||
        document.submitform.Mini.value == "" ||
        document.submitform.task.value == "" ||
        document.submitform.nos.value == "" ) {
                    alert("Please complete all required fields.");
                    return false;
    }
    if ( document.submitform.task.value == "point_mutation" &&
        ( document.submitform.PM_chain.value == "" ||
            document.submitform.PM_resid.value == "" ||
            document.submitform.PM_newres.value == "" ||
            document.submitform.PM_radius.value == "" ) ) {
                    alert("Please complete all required fields.");
                    return false;
    }
    if ( document.submitform.task.value == "ensemble" &&
        ( document.submitform.ENS_temperature.value == "" ||
          document.submitform.ENS_num_designs_per_struct.value == "" ||
          document.submitform.ENS_segment_length.value == "" ) ) {
                    alert("Please complete all required fields.");
                    return false;
    }
    if ( document.submitform.task.value == "upload_mutation" &&
            document.submitform.Mutations.value == "" ) {
                    alert("Please complete all required fields.");
                    return false;
    }
    if ( document.submitform.task.value == "sequence_tolerance" &&
          (  document.submitform.seqtol_chain1.value == "" ||
             document.submitform.seqtol_chain2.value == "" ||
             document.submitform.seqtol_weight_chain1.value == "" ||
             document.submitform.seqtol_weight_chain2.value == "" ||
             document.submitform.seqtol_weight_interface.value == "" ||
             ( document.submitform.seqtol_seqtol_mut_c_0.value == "" && document.submitform.seqtol_seqtol_mut_r_0.value == "" ) ) ) {
                    alert("Please complete all required fields.");
                    return false;
    }
    return true;
}


function ValidateFormEmail() {
    if ( document.myForm.Email.value.indexOf("@") == -1 ||
        document.myForm.Email.value.indexOf(".") == -1 ||
        document.myForm.Email.value.indexOf(" ") != -1 ||
        document.myForm.Email.value.length < 6 ) {
            alert("Your email address is not valid.");
            return false;
        }
    return true;
}


function changeApplication( app, _task ) {
	// change these two arrays if you change the table in rosettahtml.py
	myParameter = new Array("parameter1_1","parameter1_2","parameter1_3",
	                        "parameter2_1","parameter2_2",
	                        "parameter3_1");
  
  myFields = new Array( "logo1","logo2","logo3",
                        "text1","text2","text3",
                        "ref1","ref2","ref3" );

  // hide text 
  new Effect.Fade( "text" + app , { duration: 0.0 } );
  //new Effect.Fade( "ref" + app, { duration: 0.0 } );

  task = "parameter" + app + "_" + _task;
	setTask(task);
	
  new Effect.Appear( 'parameter_common', { duration: 0.5, queue: { scope: 'task' } } ) ;
	new Effect.Appear( task, { duration: 0.5 } )
  new Effect.Appear( 'parameter_submit', { duration: 0.5, queue: { scope: 'task' } } ) ;
  
	for ( i = 0; i < myParameter.length; i++ ) {
		if ( myParameter[i] != task ) {
			new Effect.Fade( myParameter[i], { duration: 0.0 } );
		}
	}
	if ( task == 'parameter1_1' || task == 'parameter1_2' || task == 'parameter2_1' ) { 
	  new Effect.Appear( "ref1" );
	  document.submitform.Mini[0].checked=true;
	  document.submitform.Mini[0].disabled=false;
    document.submitform.Mini[1].disabled=false;
    document.getElementById('rv0').style.color='#000000';
    document.getElementById('rv1').style.color='#000000';
  } else { 
    new Effect.Fade( "ref1", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
  }
	
	if ( task == 'parameter2_2' ) { 
	  new Effect.Appear( "ref2" ); 
	  new Effect.Appear( "rosetta_remark" );
	  document.submitform.Mini[0].checked=true;
    document.submitform.Mini[1].disabled=true;
    document.getElementById('rv0').style.color='#000000';
    document.getElementById('rv1').style.color='#D8D8D8';
	
	} else { 
	  new Effect.Fade( "ref2", { duration: 0.0, queue: { position: '0', scope: 'task' } } ); 
    new Effect.Fade( "rosetta_remark", { duration: 0.0, queue: { position: '20', scope: 'task' } } );
  
  }
	
	if ( task == 'parameter3_1' ) { 
	  new Effect.Appear( "ref3" ); 
	  document.submitform.Mini[0].disabled=true;
    document.submitform.Mini[1].checked=true;
    document.submitform.Mini[1].disabled=false;
    document.getElementById('rv0').style.color='#D8D8D8';
    document.getElementById('rv1').style.color='#000000';
	  
	} else { 
	  new Effect.Fade( "ref3", { duration: 0.0, queue: { position: '0', scope: 'task' } } ); 

	}

  
  mycolor = "";     
  if (task == 'parameter1_1' || task == 'parameter1_2') {
    mycolor = "#DCE9F4" ;
  } else if (task == 'parameter2_1' || task == 'parameter2_2') {
    mycolor = "#B7FFE0" ;
  } else if (task == 'parameter3_1'){
    mycolor = "#FFE2E2" ;
  }
  
  document.getElementById("box").style.background = mycolor;

}


function showMenu( menu_id ) {
    /* This function extends or hides the menu on the left */
    
    myTasks = new Array("pic1","pic2","pic3",
                        "text1","text2","text3"); // ,
                        //"ref1","ref2","ref3" );
    myParameter = new Array("parameter_common", "parameter_submit",
                            "parameter1_1","parameter1_2","parameter1_3",
  	                        "parameter2_1","parameter2_2",
  	                        "parameter3_1");
    
    // this builds an dictionary that supports the in operator
    myFields = oc(['pic', 'text','ref'], menu_id);

    mycolor = "";     
    if (menu_id == "1") {
      mycolor = "#DCE9F4" ;
      // new Effect.Appear( "menu_1", { queue: { position: '0', scope: 'menu' } } );
      // new Effect.Fade( "menu_2", { duration: 0.0 } );
      // new Effect.Fade( "menu_3", { duration: 0.0 } );
    } else if (menu_id == "2") {
      mycolor = "#B7FFE0" ;
      // new Effect.Fade( "menu_1", { duration: 0.0 } );
      // new Effect.Appear( "menu_2", { queue: { position: '0', scope: 'menu' } } );
      // new Effect.Fade( "menu_3", { duration: 0.0 } );
    } else if (menu_id = "3"){
      mycolor = "#FFE2E2" ;
      // new Effect.Fade( "menu_1", { duration: 0.0 } );
      // new Effect.Fade( "menu_2", { duration: 0.0 } );
      // new Effect.Appear( "menu_3", { queue: { position: '0', scope: 'menu' } } );
    }
    
    document.getElementById("box").style.background = mycolor;
    document.getElementById("box").style.minHeight = document.getElementById("columnLeft").style.offsetHeight;
    Nifty("div#box","big transparent fixed-height");
            
    new Effect.Fade( "text0", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
    
    // new Effect.Appear( "parameter_common", { queue: { position: '0', scope: 'task' } } );
    // new Effect.Appear( "parameter_submit", { queue: { position: '0', scope: 'task' } } );
    
    for ( i=0; i < myTasks.length; i++ ) {
      if ( myTasks[i] in myFields ) {
          new Effect.Appear( myTasks[i] );
        } else {
          new Effect.Fade( myTasks[i], { duration: 0.0, queue: { position: '0', scope: 'task' } } );
        }
    }
    // hide parameter fields
    for ( i = 0; i < myParameter.length; i++ ) {
      new Effect.Fade( myParameter[i], {duration: 0.0, queue: {position: '0', scope: 'parameter'} } );
    }
    
    new Effect.Fade( "ref1", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
  	new Effect.Fade( "ref2", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
  	new Effect.Fade( "ref3", { duration: 0.0, queue: { position: '0', scope: 'task' } } );
        
    return true;
}

/************************************
 * helper functions 
 ************************************/

function oc(a, n)
 {
   var o = {};
   for(var i=0;i<a.length;i++)
   {
     o[a[i]+n]='';
   }
   return o;
 }

function getTask() {
  return document.submitform.task.value
}

function setTask(mode){
    document.submitform.task.value = mode;
    //alert(mode);
    return true;
}

function setMini( disable ) {
    if ( disable == 1 ) {
    document.submitform.Mini[0].disabled=true;
    document.submitform.Mini[1].disabled=true;
    //document.submitform.keep_output.disabled=true;
    document.getElementById('rosetta1').style.color='#D8D8D8';
    //document.getElementById('rosetta2').style.color='#D8D8D8';
    } else {
    document.submitform.Mini[0].disabled=false;
    document.submitform.Mini[1].disabled=false;
    //document.submitform.keep_output.disabled=false;
    document.getElementById('rosetta1').style.color='#000000';
    //document.getElementById('rosetta2').style.color='#000000';
    }
    return true;
}

function updateCellSize1( task ) {
    var high = document.getElementById( 'pic' ).offsetHeight + document.getElementById( 'common_form' ).offsetHeight + document.getElementById( 'submit_button' ).offsetHeight + document.getElementById( task ).offsetHeight ;
    document.getElementById('empty_box').style.height = high ;
}

function updateCellSize2() {
    var high = document.getElementById( 'pic' ).offsetHeight + document.getElementById( 'task_init' ).offsetHeight;
    document.getElementById('empty_box').style.height = high ;
}

function addOneMore() {
    numMPM = numMPM + 1;
    //document.write("row_PM");
    //document.write(numMPM);
    new Effect.Appear("row_PM" + "" + numMPM);
    //return "row_PM" + "" + numMPM;
    
    return true;
}

function addOneMoreSeqtol() {
    numSeqTol = numSeqTol + 1;
    new Effect.Appear("seqtol_row_" + "" + numSeqTol);
    return true;
}

function writeRow( numbr ) {
    x = numbr + 1
    var s = '<td align="center">' + '' + x + '</td>';
    s = s + '<td align="center"><input type="text" name="PM_chain'  + '' + numbr + '" maxlength=1 SIZE=5 VALUE=""></td>';
    s = s + '<td align="center"><input type="text" name="PM_resid'  + '' + numbr + '" maxlength=4 SIZE=5 VALUE=""></td>';
    s = s + '<td align="center"><input type="text" name="PM_newres' + '' + numbr + '" maxlength=1 SIZE=2 VALUE=""></td>';
    s = s + '<td align="center"><input type="text" name="PM_radius' + '' + numbr + '" maxlength=4 SIZE=7 VALUE=""></td>';
    document.write(s);
    return true;
}

function writeRowDEMO( numbr, chain, resid, newres, radius ) {
    x = numbr + 1
    var s = '<td align="center">' + '' + x + '</td>';
    s = s + '<td align="center"><input type="text" name="PM_chain'  + '' + numbr + '" maxlength=1 SIZE=5 VALUE="' + '' + chain + '"></td>';
    s = s + '<td align="center"><input type="text" name="PM_resid'  + '' + numbr + '" maxlength=4 SIZE=5 VALUE="' + '' + resid + '"></td>';
    s = s + '<td align="center"><input type="text" name="PM_newres' + '' + numbr + '" maxlength=1 SIZE=2 VALUE="' + '' + newres + '"></td>';
    s = s + '<td align="center"><input type="text" name="PM_radius' + '' + numbr + '" maxlength=4 SIZE=7 VALUE="' + '' + radius + '"></td>';
    document.write(s);
    addOneMore();
    return true;
}

/************************************
 * helper functions  END
 ************************************/

function confirm_delete(jobID)
{
  var r=confirm("Delete Job " + jobID + "?");
  if (r==true) {
    //document.write("You pressed OK!");
    window.location.href = "rosettaweb.py?query=delete&jobID=" + jobID + "&button=Delete" ; }
//  else {
//    window.location.href = "rosettaweb.py?query=queue" ; }
}




function set_demo_values() {
  actual_task = getTask();

 if ( actual_task == 'parameter1_1') {
      document.submitform.PDBComplexURL.value = "https://kortemmelab.ucsf.edu/backrub/downloads/1KYO.pdb"
      document.submitform.nos.value = "10";
      document.submitform.PM_chain.value = "A";
      document.submitform.PM_resid.value = "153";
      document.submitform.PM_newres.value = "F";

  } else if ( actual_task == 'parameter1_2') {
      document.submitform.PDBComplexURL.value = "https://kortemmelab.ucsf.edu/backrub/downloads/2PDZ_M01.pdb"
      document.submitform.nos.value = "10";
      document.submitform.PM_chain0.value = "A";
      document.submitform.PM_resid0.value = "17";
      document.submitform.PM_newres0.value = "A";
      document.submitform.PM_radius0.value = "6.0";
      addOneMore();
      document.submitform.PM_chain1.value = "A";
      document.submitform.PM_resid1.value = "32";
      document.submitform.PM_newres1.value = "A";
      document.submitform.PM_radius1.value = "6.0";
      addOneMore();
      document.submitform.PM_chain2.value = "A";
      document.submitform.PM_resid2.value = "65";
      document.submitform.PM_newres2.value = "A";
      document.submitform.PM_radius2.value = "6.0";
      addOneMore();
      document.submitform.PM_chain3.value = "A";
      document.submitform.PM_resid3.value = "72";
      document.submitform.PM_newres3.value = "A";
      document.submitform.PM_radius3.value = "6.0";
      addOneMore();

  } else if ( actual_task == "parameter2_1") {
      document.submitform.PDBComplexURL.value = "https://kortemmelab.ucsf.edu/backrub/downloads/1UBQ.pdb"
      document.submitform.nos.value = "10";  

  } else if ( actual_task == 'parameter2_2') {
      document.submitform.PDBComplexURL.value = "https://kortemmelab.ucsf.edu/backrub/downloads/1UBQ.pdb"
      document.submitform.nos.value = "10";
      document.submitform.ENS_temperature.value = "1.2";
      document.submitform.ENS_num_designs_per_struct.value = "20";
      document.submitform.ENS_segment_length.value = "12";

  } else if ( actual_task == 'parameter3_1') {
      document.submitform.PDBComplexURL.value = "https://kortemmelab.ucsf.edu/backrub/downloads/2PDZ_M01.pdb"
      document.submitform.nos.value = "10";
      document.submitform.seqtol_chain1.value = "A";
      document.submitform.seqtol_chain2.value = "B";
      document.submitform.seqtol_radius.value = "4.0";
      document.submitform.seqtol_weight_chain1.value = "1";
      document.submitform.seqtol_weight_chain2.value = "1";      
      document.submitform.seqtol_weight_interface.value = "2";
      document.submitform.seqtol_mut_c_0.value = "B";
      document.submitform.seqtol_mut_r_0.value = "3";
      addOneMoreSeqtol();
      document.submitform.seqtol_mut_c_1.value = "B";
      document.submitform.seqtol_mut_r_1.value = "4";
      addOneMoreSeqtol();
      document.submitform.seqtol_mut_c_2.value = "B";
      document.submitform.seqtol_mut_r_2.value = "5";
      addOneMoreSeqtol();
      document.submitform.seqtol_mut_c_3.value = "B";
      document.submitform.seqtol_mut_r_3.value = "6";
      addOneMoreSeqtol();
  }
  return true;
}



/* disabled 
else if ( actual_task == 'upload_mutation') {
    document.submitform.nos.value = "10"
    
    document.submitform..value = "";
    document.submitform..value = "";
    document.submitform..value = "";

} */


// obsolete:

// function popUp( obj ) {
//     my_obj = document.getElementById(obj).style;
//     if ( my_obj.visibility == "visible" || my_obj.visibility == "show" ) {
//         my_obj.visibility = "hidden";
//     }
//     else { if ( my_obj.visibility == "hidden" ) {
//         my_obj.visibility = "visible";
//     }
//     }
// }

function popUp( obj ) {
    my_obj = document.getElementById(obj).style;
    offset=10
    if ( my_obj.visibility == "visible" || my_obj.visibility == "show" ) {
        my_obj.top  = e.clientY + offset;
        my_obj.left = e.clientX + offset*2;
        my_obj.visibility = "hidden";
    }
    else {
        my_obj.visibility = "visible";
    }
}





