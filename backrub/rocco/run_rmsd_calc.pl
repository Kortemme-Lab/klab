#!/usr/bin/perl

if(($#ARGV+1) != 2)
{
  print "\n\nThis script creates the chimera script needed for calculating the RMSD of all the backrub structures\n"; 
  print "\nUsage: perl run_rmsd_calc.pl pdbid maxFilesOpenAtOnce"; 
  print "\nExample: perl run_rmsd_calc.pl 1IZH 20\n\n"; 
  exit;
}

# Note: The conformations are organized like so:
#       0) for each temperature (i.e. 0.6 or 1.2) there exist 2000 backrub conformations
#       1) there are 10 "initial" structures and are labeled 00 through 09
#       2) for each one of these initial structures 100 last and 100 low structures were created (total 200)
#        
# Example file name: 081IZHlast_0075.pdb

$scriptname = "calc_rmsd_with_orig.com";
$scriptname_init = "calc_rmsd_with_init.com";
open CHIMERA_SCRIPT, ">$scriptname" or die "\n\nUnable to open $scriptname\n\n";
#open CHIMERA_SCRIPT_INIT, ">$scriptname_init" or die "\n\nUnable to open $scriptname_init\n\n";
my $initnum = 0; # this will iterate from 0-9
my $pdb = $ARGV[0]; # this will be the pdb id
my $confnum = 0; # this will iterate from 1-100, must take special care because the naming format has 4 digits (e.g. 0001-0100)
my $filesinlist = 0;
my $maxfilesopen = $ARGV[1];

# We will calculate the RMSD two ways:
# 1) We will calculate the RMSD between the original minized structure (e.g. 1IZH.pdb) and all the conformations.
print CHIMERA_SCRIPT "open $pdb.pdb\n\n"; # this will be model #0 onto which all other structures will be matched to, see matchmaker docs on chimera user's guide for details

# LAST structures
# iterate through groups of N (to minimize opening and closing files and memory usage)
# Example file name: 081IZHlast_0075.pdb
for ($initnum = 0; $initnum < 10; $initnum++) # iterate through group number
{
  for($confnum = 1; $confnum <= 100; $confnum++)
  {
    if($confnum < 10) # if confnum has a single digit, pad with 3 zeros
    {
      $filename = "0$initnum"."$pdb"."last_000"."$confnum".".pdb";

    }
    elsif($confnum == 100) # if confnum is 3 digits long, pad with 1 zero
    {
      $filename = "0$initnum"."$pdb"."last_0"."$confnum".".pdb";

    }
    else # else if confnum is 2 digits long, pad with 2 zeros
    {
      $filename = "0$initnum"."$pdb"."last_00"."$confnum".".pdb";

    }

    if($filesinlist == 0) # this is the first file name added to the list
    {
      $filelist = $filename;
      $filesinlist++;

    }
    elsif($filesinlist < $maxfilesopen-1) # append this file name to the list
    {
      $filelist = "$filelist $filename";
      $filesinlist++;

    }
    else # we have 20 files in our list, so open them, match them, then close them 
    {
      $filelist = "$filelist $filename";
      print CHIMERA_SCRIPT "open $filelist\n";
      for(my $modelnum = 1; $modelnum <= $maxfilesopen; $modelnum++) # modelnum is the chimera model number
      {
        print CHIMERA_SCRIPT "mm #0 #".$modelnum."\n";
      
      }
      for(my $modelnum = 1; $modelnum <= $maxfilesopen; $modelnum++) # modelnum is the chimera model number
      {
        print CHIMERA_SCRIPT "close #".$modelnum.";";
      }
      print CHIMERA_SCRIPT "\n\n";
      
      $filesinlist = 0; # reset
      $filelist = "";
    } # end else statement to print structural comparisons

  } # end for loop $confnum

} # end for loop iterating through all the initial group numbers

# LOW structures
# iterate through groups of N (to minimize opening and closing files and memory usage)
# Example file name: 081IZHlast_0075.pdb
for ($initnum = 0; $initnum < 10; $initnum++) # iterate through group number
{
  for($confnum = 1; $confnum <= 100; $confnum++)
  {
    if($confnum < 10) # if confnum has a single digit, pad with 3 zeros
    {
      $filename = "0$initnum"."$pdb"."low_000"."$confnum".".pdb";

    }
    elsif($confnum == 100) # if confnum is 3 digits long, pad with 1 zero
    {
      $filename = "0$initnum"."$pdb"."low_0"."$confnum".".pdb";

    }
    else # else if confnum is 2 digits long, pad with 2 zeros
    {
      $filename = "0$initnum"."$pdb"."low_00"."$confnum".".pdb";

    }

    if($filesinlist == 0) # this is the first file name added to the list
    {
      $filelist = $filename;
      $filesinlist++;

    }
    elsif($filesinlist < $maxfilesopen-1) # append this file name to the list
    {
      $filelist = "$filelist $filename";
      $filesinlist++;

    }
    else # we have 20 files in our list, so open them, match them, then close them 
    {
      $filelist = "$filelist $filename";
      print CHIMERA_SCRIPT "open $filelist\n";
      for(my $modelnum = 1; $modelnum <= $maxfilesopen; $modelnum++) # modelnum is the chimera model number
      {
        print CHIMERA_SCRIPT "mm #0 #".$modelnum."\n";
      
      }
      for(my $modelnum = 1; $modelnum <= $maxfilesopen; $modelnum++) # modelnum is the chimera model number
      {
        print CHIMERA_SCRIPT "close #".$modelnum.";";
      }
      print CHIMERA_SCRIPT "\n\n";
      
      $filesinlist = 0; # reset
      $filelist = "";
    } # end else statement to print structural comparisons

  } # end for loop $confnum

} # end for loop iterating through all the initial group numbers
# 2) We will calculate the RMSD between the structures labeled "initial" (e.g. 001IZH_initial.pdb) and their corresponding conformations (e.g.001IZHlast_0011.pdb).
#    Still not clear to me what these "initial" structures are or why they exist or why sometimes they're a little different 
#    from one another.
# 08/15/10: We'll hold off on this for now.

close(CHIMERA_SCRIPT);
#close(CHIMERA_SCRIPT_INIT);

#system("/kortemmelab/home/rocco/apps/chimera/bin/chimera --nogui $scriptname > $pdb_rmsd_calcs.out"); 

