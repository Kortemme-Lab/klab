#!/usr/bin/perl
##
## Copyright 2002, University of Washington, the Baker Lab, and Dylan Chivian.
##   This document contains private and confidential information and its 
##   disclosure does not constitute publication.  All rights are reserved by 
##   University of Washington, the Baker Lab, and Dylan Chivian, except those 
##   specifically granted by license.
##
##  Initial Author: Dylan Chivian (dylan@lazy8.com)
##  $Revision: 15214 $
##  $Date: 2007-05-29 12:57:20 -0700 (Tue, 29 May 2007) $
##  $Author: yiliu $
##
###############################################################################
# Vanita Sood, November 15, 2004
# Pass in the pdbfile
# Optional: Pass in comma separated lists of residues to be designed, repacked
# or to be designed only as hydrophobic,charged, aromatic or polar.
# Specify rosetta or interface type resfile to be made
# Optionally give a name for the output resfile or will write to STDOUT
# Outputs a resfile in the appropriate format
###############################################################################
# conf
###############################################################################
$| = 1;                                              # disable stdout buffering
###############################################################################
# init
###############################################################################
# argv
my %opts = &getCommandLineOptions ();
my $pdbfile   = $opts{pdb};
my $desres    = $opts{desres};     # ALLAA
my $hphobic   = $opts{hphobic};    # PIKAA  ACFILMPVWY (no cys for pDes)
my $charged   = $opts{charged};    # PIKAA  DEKR
my $polar     = $opts{polar};      # PIKAA  HNQSTWY
my $aromatic  = $opts{aromatic};   # PIKAA  HWY
my $allpolar = $opts{allpolar};    # POLAR
my $pikaa     = $opts{pikaa};	   # PIKAA  (specify the aa in the list file) 
my $repack    = $opts{repack};     # NATAA  (no cys for pDes)
my $repackall = $opts{repackall};  # repack residues not being designed (no cys for pDes)
my $outfile   = $opts{outfile};

@pdb_buf = &fileBufArray ($pdbfile);
###############################################################################
# main
###############################################################################

# Make undef arrays for optional design/repack choices
my @repack;
my @hphobic;
my @charged;
my @polar;
my @allpolar;
my @aromatic;
my @pikaa;

# Get aa identities and chain ID for each residue
my @res_num = ();
my @res_id = ();
my @chain = ();
my @sequential_residue_number = ();
my $sqrn = 0;
foreach $line (@pdb_buf) {
    if (substr($line,13,2) =~ /CA/ || substr($line,13,4) =~ /C1\* / ) {
	my $res_num = substr($line,23,3);
	$res_num =~ s/^\s+|\s+$//g;
	my $res_id = substr($line,17,3);
	$res_id =~ s/^\s+|\s+$//g;
	my $ch = substr($line,21,1);
	$ch =~ s/^\s+|\s+$//g;
	if($res_num != $res_num[$line-1]){
	    push (@res_num, $res_num);
	    push (@res_id, $res_id);
	    push (@chain, $ch);
	    $sqrn++ ;
	    push (@sequential_residue_number, $sqrn);
	}
    }
}

my %pdbaa = ();
for (my $i=0; $i<=$#sequential_residue_number; $i++){
    $pdbaa{$sequential_residue_number[$i]} = $res_id[$i];
} 

my %chain_id = ();
for (my $i=0; $i<=$#sequential_residue_number; $i++){
    $chain_id{$sequential_residue_number[$i]} = $chain[$i];
}

#add the residue_number()
my %residue_number = ();
for (my $i=0; $i<=$#sequential_residue_number; $i++){
    $residue_number{$sequential_residue_number[$i]} = $res_num[$i];
}


my @resfile_buf = ();
# Make a template rosetta resfile
# top of resfile
    my $resfile_top = 
" This file specifies which residues will be varied
                                                  
 Column   2:  Chain                               
 Column   4-7:  sequential residue number         
 Column   9-12:  pdb residue number                
 Column  14-18: id  (described below)             
 Column  20-40: amino acids to be used            
                                                  
 NATAA  => use native amino acid                  
 ALLAA  => all amino acids                        
 NATRO  => native amino acid and rotamer          
 PIKAA  => select inividual amino acids           
 POLAR  => polar amino acids                      
 APOLA  => apolar amino acids                     
                                                  
 The following demo lines are in the proper format
                                                  
 A    1    3 NATAA                                
 A    2    4 ALLAA                                
 A    3    6 NATRO                                
 A    4    7 NATAA                                
 B    5    1 PIKAA  DFLM                          
 B    6    2 PIKAA  HIL                           
 B    7    3 POLAR                                
 -------------------------------------------------
 start";
chomp $resfile_top;
push (@resfile_buf,$resfile_top);
# resfile
#    $sequential_residue_number=1;

foreach (@sequential_residue_number) {
  my $a = sprintf("%2s", $chain_id{$_});
  my $b = sprintf("%5s", $_);
  
  my $c = sprintf("%5s", $residue_number{$_});
  push (@resfile_buf,"$a$b$c NATRO ");
}
# Make design substitutions
if (defined $desres) {
  open (FILE, $desres);
  chomp (my $des = <FILE>);
  close FILE;
  $des =~ s/^\s+|\s+$//g;
  my @design = split (/,/, $des);
  foreach my $design_part(@design) {
    $design_part =~ s/^\s+|\s+$//;
    my @chain_residue = split(" ",$design_part);
    if (@chain_residue == 2){
      my $design_chain = $chain_residue[0];
      my $design_residue = $chain_residue[1];
      foreach my $line (@resfile_buf) {
	if ($design_residue == substr($line,7,5) && $design_chain eq substr($line,1,1)){
	  $line =~ s/NATRO/ALLAA/;
	  last;
	}
      }
    }
    elsif(@chain_residue==1){
      foreach my $line (@resfile_buf) {
	if ($design_part == substr($line,7,5)){
	  #if ($tmp_array[1] == substr($line,7,5) && $tmp_array[0] eq substr($line,1,1)){
	  $line =~ s/NATRO/ALLAA/;
	  last;
	}
      }
    }
  }
}

# Hydrophobic residues
if (defined $hphobic) {
  open (FILE, $hphobic);
  chomp (my $buf = <FILE>);
  close FILE;
  $buf =~ s/^\s+|\s+$//g;
  @hphobic = split (/,/, $buf);
  foreach my $hphobic_part(@hphobic){
    $hphobic_part =~ s/^\s+|\s+$//;
    my @chain_residue = split(" ",$hphobic_part);
    if(@chain_residue == 2){
      my $hphobic_chain = $chain_residue[0];
      my $hphobic_residue = $chain_residue[1];
      foreach my $line (@resfile_buf) {
	if ($hphobic_residue == substr($line,7,5) && $hphobic_chain eq substr($line,1,1)){
	  $line =~ s/NATRO/PIKAA  ACFILMPVWY/;
	  last;
	}
      }
    }
    elsif(@chain_residue==1){
      foreach my $line (@resfile_buf) {
	if ($hphobic_part == substr($line,7,5) ){
	  #if ($tmp_array[1] == substr($line,7,5) && $tmp_array[0] eq substr($line,1,1)){
	  $line =~ s/NATRO/PIKAA  ACFILMPVWY/;
	  last;
	}
      }
    }
  }
}
    
# Charged residues
if (defined $charged) {
  open (FILE, $charged);
  chomp (my $buf = <FILE>);
  close FILE;
  $buf =~ s/^\s+|\s+$//g;
  @charged = split (/,/, $buf);
  foreach my $charged_part(@charged){
    $charged_part =~ s/^\s+|\s+$//;
    my @chain_residue = split(" ",$charged_part);
    if(@chain_residue == 2){
      my $charged_chain = $chain_residue[0];
      my $charged_residue = $chain_residue[1];
      foreach my $line (@resfile_buf) {
	if ($charged_residue == substr($line,7,5) && $charged_chain eq substr($line,1,1)){
	  $line =~ s/NATRO/PIKAA  DEKR/;
	  last;
	}
      }
    }
    elsif(@chain_residue==1){
      foreach my $line (@resfile_buf) {
	if ($charged_part == substr($line,7,5) ){
	  #if ($tmp_array[1] == substr($line,7,5) && $tmp_array[0] eq substr($line,1,1)){
	  $line =~ s/NATRO/PIKAA  DEKR/;
	  last;
	}
      }
    }
  }
}

# Polar residues
if (defined $polar) {
  open (FILE, $polar);
  chomp (my $buf = <FILE>);
  close FILE;
  $buf =~ s/^\s+|\s+$//g;
  @polar = split (/,/, $buf);
  foreach my $polar_part(@polar){
    $polar_part =~ s/^\s+|\s+$//;
    my @chain_residue = split(" ",$polar_part);
    if(@chain_residue == 2){
      my $polar_chain = $chain_residue[0];
      my $polar_residue = $chain_residue[1];
      foreach my $line (@resfile_buf) {
	if ($polar_residue == substr($line,7,5) && $polar_chain eq substr($line,1,1)){
	  $line =~ s/NATRO/PIKAA  HNQSTWY/;
	  last;
	}
      }
    } elsif (@chain_residue==1){
      foreach my $line (@resfile_buf) {
	if ($polar_part == substr($line,7,5) ){
	  #if ($tmp_array[1] == substr($line,7,5) && $tmp_array[0] eq substr($line,1,1)){
	  $line =~ s/NATRO/PIKAA  HNQSTWY/;
	  last;
	}
      }
    }
  }
}
# All Polar residues
if (defined $allpolar) {
  open (FILE, $allpolar);
  chomp (my $buf = <FILE>);
  close FILE;
  $buf =~ s/^\s+|\s+$//g;
  @allpolar = split (/,/, $buf);
  foreach my $allpolar_part(@allpolar){
    $allpolar_part =~ s/^\s+|\s+$//;
    my @chain_residue = split(" ",$allpolar_part);
    if(@chain_residue == 2){
      my $allpolar_chain = $chain_residue[0];
      my $allpolar_residue = $chain_residue[1];
      foreach my $line (@resfile_buf) {
	if ($allpolar_residue == substr($line,7,5) && $allpolar_chain eq substr($line,1,1)){
	  $line =~ s/NATRO/POLAR/;
	  last;
	}
      }
    }
    elsif(@chain_residue==1){
      foreach my $line (@resfile_buf) {
	if ($allpolar_part == substr($line,7,5) ){
	  $line =~ s/NATRO/POLAR/;
	  last;
	}
      }
    }
  }
}

# Aromatic residues
if (defined $aromatic) {
  open (FILE, $aromatic);
  chomp (my $buf = <FILE>);
  close FILE;
  $buf =~ s/^\s+|\s+$//g;
  @aromatic = split (/,/, $buf);
  foreach my $aromatic_part(@aromatic){
    $aromatic_part =~ s/^\s+|\s+$//;
    my @chain_residue = split(" ",$aromatic_part);
    if(@chain_residue == 2){
      my $aromatic_chain = $chain_residue[0];
      my $aromatic_residue = $chain_residue[1];
      foreach my $line (@resfile_buf) {
	if ($aromatic_residue == substr($line,7,5) && $aromatic_chain eq substr($line,1,1)){
	  $line =~ s/NATRO/PIKAA  HWY/;
	  last;
	}
      }
    }
    elsif(@chain_residue==1){
      foreach my $line (@resfile_buf) {
	if ($aromatic_part == substr($line,7,5) ){
	  $line =~ s/NATRO/PIKAA  HWY/;
	  last;
	}
      }
    }
  }
}

# Pikaa residues
if (defined $pikaa) {
  open (FILE, $pikaa);
  chomp (my $buf = <FILE>);
  close FILE;
  $buf =~ s/^\s+|\s+$//g;
  @pikaa = split (/,/, $buf);
  foreach my $pikaa_part(@pikaa){
    $pikaa_part =~ s/^\s+|\s+$//;
    my @chain_residue = split(" ",$pikaa_part);
    if(@chain_residue == 3){
      my $pikaa_chain = $chain_residue[0];
      my $pikaa_residue = $chain_residue[1];
      my $pikaa_theaa = $chain_residue[2];
      foreach my $line (@resfile_buf) {
	if ($pikaa_residue == substr($line,7,5) && $pikaa_chain eq substr($line,1,1)){
	  $line =~ s/NATRO/PIKAA  $pikaa_theaa/;
	  last;
	}
      }
    }
    elsif(@chain_residue==2){
      my $pikaa_residue = $chain_residue[0];
      my $pikaa_theaa = $chain_residue[1];
      foreach my $line (@resfile_buf) {
	if ($pikaa_part == substr($line,7,5) ){
	  $line =~ s/NATRO/PIKAA  $pikaa_theaa/;
	  last;
	}
      }
    }
  }
}

# Repack residues
if (defined $repack) {
  open (FILE, $repack);
  chomp (my $buf = <FILE>);
  close FILE;
  $buf =~ s/^\s+|\s+$//g;
  @repack = split (/,/, $buf);
  foreach my $repack_part(@repack){
    $repack_part =~ s/^\s+|\s+$//; 
    my @chain_residue = split(" ",$repack_part);
    if(@chain_residue ==2 ){
      my $repack_chain = $chain_residue[0];
      my $repack_residue = $chain_residue[1];
      foreach my $line (@resfile_buf) {
	if ($repack_residue == substr($line,7,5) && $repack_chain eq substr($line,1,1)
	    && $pdbaa{$residue} ne "GLY" 
	    && $pdbaa{$residue} ne "ALA"){
	  $line =~ s/NATRO/NATAA/;
	  last;
	}elsif ($pdbaa{$residue} eq "GLY"){
	  print "no point in repacking $residue, it's a GLY\n";
	  last;
	}elsif ($pdbaa{$residue} eq "ALA"){
	  print "no point in repacking $residue, it's a ALA\n";
	  last;
	}
      }
    }
    elsif(@chain_residue==1){
      foreach my $line (@resfile_buf) {
	if ($repack_part == substr($line,7,5) 
	    && $pdbaa{$residue} ne "GLY" 
	    && $pdbaa{$residue} ne "ALA"){
	  #if ($tmp_array[1] == substr($line,7,5) && $tmp_array[0] eq substr($line,1,1)){
	  $line =~ s/NATRO/NATAA/;
	  last;
	}
      }
    }
  }
}

# Repack all residues not being designed
if (defined $repackall) {
  foreach my $line (@resfile_buf) {
    my $residue = substr($line,4,3);
    if ($pdbaa{$residue} ne "GLY"
	&& $pdbaa{$residue} ne "ALA"){
      $line =~ s/NATRO/NATAA/;
    }
  }
}

######################################################################
# print resfile
if (defined $outfile) {
    open OUTFILE, ">$outfile";
    foreach (@resfile_buf){
	print OUTFILE $_."\n";
    }
    close OUTFILE;
}else {
    foreach (@resfile_buf){
	print $_."\n";
    }
}
exit 0;
###############################################################################
# subs
###############################################################################

# getCommandLineOptions()
#
#  rets: \%opts  pointer to hash of kv pairs of command line options
#
sub getCommandLineOptions {
    use Getopt::Long;
    my $usage = qq{usage: $0
\t-pdb <pdbfile>
\t[-desres <design_res_file>]
\t[-hphobic <hphobic_res_file>]
\t[-charged <charged_res_file>]
\t[-polar <polar_res_file>]
\t[-allpolar <allpolar_res_file>]
\t[-aromatic <aromatic_res_file>]
\t[-pikaa <pikaa_res_file>]
\t[-repack <repack_res_file>]
\t[-repackall]
\t[-outfile <resfile_name>]
remember all residue lists must contain comma separated values. 
The values should have chain id and the residue number, if there is no chain id specified, will only consider the first chain.
   For ex: 1,4,5,A15,B3    indicates residues 1,4,5 and 15 of chain A and residue 3 of chain B
For pikaa option, the list need contain the signle aa code, such as "A 23 ALM, A 24 WY"
};

    # Get args
    my %opts = ();
    &GetOptions (\%opts, "pdb=s", "desres=s", "repack=s", "hphobic=s", "charged=s", "polar=s", "allpolar=s", "aromatic=s", "pikaa=s", "repackall", "outfile=s");

    # Check for legal invocation
    if (! defined $opts{pdb} ) {
        print STDERR "$usage\n";
        exit -1;
    }
    &checkExist ('f', $opts{pdb});
    if (defined $opts{desres}) {
	&checkExist ('f', $opts{desres});
    }
    if (defined $opts{repack}) {
	&checkExist ('f', $opts{repack});
    }
    if (defined $opts{hphobic}) {
	&checkExist ('f', $opts{hphobic});
    }
    if (defined $opts{charged}) {
	&checkExist ('f', $opts{charged});
    }
    if (defined $opts{polar}) {
	&checkExist ('f', $opts{polar});
    }
    if (defined $opts{allpolar}) {
	&checkExist ('f', $opts{allpolar});
    }
    if (defined $opts{aromatic}) {
	&checkExist ('f', $opts{aromatic});
    }
    if (defined $opts{pikaa}) {
        &checkExist ('f', $opts{pikaa});
    }


    return %opts;
}

###############################################################################
# util
###############################################################################
# readFiles
#
sub readFiles {
    my ($dir, $fullpath_flag) = @_;
    my $inode;
    my @inodes = ();
    my @files = ();
    
    opendir (DIR, $dir);
    @inodes = sort readdir (DIR);
    closedir (DIR);
    foreach $inode (@inodes) {
	next if (! -f "$dir/$inode");
	next if ($inode =~ /^\./);
	push (@files, ($fullpath_flag) ? "$dir/$inode" : "$inode");
    }
    return @files;
}

# createDir
#
sub createDir {
    my $dir = shift;
    if (! -d $dir && (system (qq{mkdir -p $dir}) != 0)) {
	print STDERR "$0: unable to mkdir -p $dir\n";
	exit -2;
    }
    return $dir;
}

# copyFile
#
sub copyFile {
    my ($src, $dst) = @_;
    if (system (qq{cp $src $dst}) != 0) {
	print STDERR "$0: unable to cp $src $dst\n";
	exit -2;
    }
    return $dst;
}

# zip
#
sub zip {
    my $file = shift;
    if ($file =~ /^\.Z$/ || $file =~ /\.gz$/) {
	print STDERR "$0: ABORT: already a zipped file $file\n";
	exit -2;
    }
    if (system (qq{gzip -9 $file}) != 0) {
	print STDERR "$0: unable to gzip -9 $file\n";
	exit -2;
    }
    $file .= ".gz";
    return $file;
}

# unzip
#
sub unzip {
    my $file = shift;
    if ($file !~ /^\.Z$/ && $file !~ /\.gz$/) {
	print STDERR "$0: ABORT: not a zipped file $file\n";
	exit -2;
    }
    if (system (qq{gzip -d $file}) != 0) {
	print STDERR "$0: unable to gzip -d $file\n";
	exit -2;
    }
    $file =~ s/\.Z$|\.gz$//;
    return $file;
}

# remove
#
sub remove {
    my $inode = shift;
    if (system (qq{rm -rf $inode}) != 0) {
	print STDERR "$0: unable to rm -rf $inode\n";
	exit -2;
    }
    return $inode;
}
     
# runCmd
#
sub runCmd {
    my ($cmd, $nodie) = @_;
    my $ret;
    my $date = `date +'%Y-%m-%d_%T'`;  chomp $date;
    print "[$date]:$0:RUNNING: $cmd\n" if ($debug);
    $ret = system ($cmd);
    #$ret = ($?>>8)-256;
    if ($ret != 0) {
	$date = `date +'%Y-%m-%d_%T'`;  chomp $date;
	print STDERR ("[$date]:$0: FAILURE (exit: $ret): $cmd\n");
	if ($nodie) {
	    return $ret;
	} else {
	    exit $ret;
	}
    }
    return 0;
}

# logMsg()
#
sub logMsg {
    my ($msg, $logfile) = @_;
    my $date = `date +'%Y-%m-%d_%T'`;  chomp $date;

    if ($logfile) {
        open (LOGFILE, ">".$logfile);
        select (LOGFILE);
    }
    else {
	select (STDERR);
    }
    print "[$date]:$0: $msg\n";
    if ($logfile) {
        close (LOGFILE);
    }
    select (STDOUT);

    return 'true';
}

# checkExist()
#
sub checkExist {
    my ($type, $path) = @_;
    if ($type eq 'd') {
	if (! -d $path) { 
            print STDERR "$0: dirnotfound: $path\n";
            exit -3;
	}
    }
    elsif ($type eq 'f') {
	if (! -f $path) {
            print STDERR "$0: filenotfound: $path\n";
            exit -3;
	}
	elsif (! -s $path) {
            print STDERR "$0: emptyfile: $path\n";
            exit -3;
	}
    }
}

# abort()
#
sub abort {
    my $msg = shift;
    my $date = `date +'%Y-%m-%d_%T'`;  chomp $date;
    print STDERR "[$date]:$0:ABORT: $msg\n";
    exit -2;
}

# writeBufToFile()
#
sub writeBufToFile {
    my ($file, $bufptr) = @_;
    if (! open (FILE, '>'.$file)) {
	&abort ("$0: unable to open file $file for writing");
    }
    print FILE join ("\n", @{$bufptr}), "\n";
    close (FILE);
    return;
}

# fileBufString()
#
sub fileBufString {
    my $file = shift;
    my $oldsep = $/;
    undef $/;
    if ($file =~ /\.gz$|\.Z$/) {
	if (! open (FILE, "gzip -dc $file |")) {
	    &abort ("$0: unable to open file $file for gzip -dc");
	}
    }
    elsif (! open (FILE, $file)) {
	&abort ("$0: unable to open file $file for reading");
    }
    my $buf = <FILE>;
    close (FILE);
    $/ = $oldsep;
    return $buf;
}

# fileBufArray()
#
sub fileBufArray {
    my $file = shift;
    my $oldsep = $/;
    undef $/;
    if ($file =~ /\.gz$|\.Z$/) {
	if (! open (FILE, "gzip -dc $file |")) {
	    &abort ("$0: unable to open file $file for gzip -dc");
	}
    }
    elsif (! open (FILE, $file)) {
	&abort ("$0: unable to open file $file for reading");
    }
    my $buf = <FILE>;
    close (FILE);
    $/ = $oldsep;
    @buf = split (/$oldsep/, $buf);
    pop (@buf)  if ($buf[$#buf] eq '');
    return @buf;
}

# bigFileBufArray()
#
sub bigFileBufArray {
    my $file = shift;
    my $buf = +[];
    if ($file =~ /\.gz$|\.Z$/) {
        if (! open (FILE, "gzip -dc $file |")) {
            &abort ("$0: unable to open file $file for gzip -dc");
        }
    }
    elsif (! open (FILE, $file)) {
        &abort ("$0: unable to open file $file for reading");
    }
    while (<FILE>) {
        chomp;
        push (@$buf, $_);
    }
    close (FILE);
    return $buf;
}     

###############################################################################
# end
1;                                                     # in case it's a package
###############################################################################
# Interface mode
# elsif ($format eq "interface"){
# # Make a template resfile
#     foreach (@res_num) {
# 	my $num = sprintf ("%3d", $_);
# 	my $id =  sprintf ("%3d", "1");
# 	my $line = $num.$id." 1 0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 ";
# 	push (@resfile_buf, $line);
#     }
# # Make design substitutions
#     if (defined $desres) {
# 	open (FILE, $desres);
# 	chomp (my $des = <FILE>);
# 	close FILE;
# 	$des =~ s/^\s+|\s+$//g;
# 	my @design = split (/,/, $des);
# 	foreach my $residue(@design) {
# 	    $residue =~ s/^\s+|\s+$//;
# 	    foreach my $line (@resfile_buf) {
# 		if ($residue == substr($line,0,3)){
# 		    substr($line,5,1) = 0;
# 		    if ($pdbaa{$residue} eq "CYS"){
# 			print "you are designing a cysteine ($residue) 
# - do you really want to do that?\n";
# 		    }
# 		    last;
# 		}
# 	    }
# 	}
#     }
# # Repack residues
#     if (defined $repack) {
# 	open (FILE, $repack);
# 	chomp (my $buf = <FILE>);
# 	close FILE;
# 	$buf =~ s/^\s+|\s+$//g;
# 	@repack = split (/,/, $buf);
# 	foreach my $residue(@repack) {
# 	    $residue =~ s/^\s+|\s+$//;
# 	    foreach my $line (@resfile_buf) {
# 		if ($residue == substr($line,0,3) 
# 		    && $pdbaa{$residue} ne "CYS"
# 		    && $pdbaa{$residue} ne "ALA"
# 		    && $pdbaa{$residue} ne "GLY"){
# 		    substr($line,5,1) = 2;
# 		    last;;
# 		}elsif ($pdbaa{$residue} eq "CYS"){
# 		    print "$residue is not being repacked, repacking of CYS is not supported\n";
# 		    last;
# 		}elsif ($pdbaa{$residue} eq "GLY"){
# 		    print "no point in repacking $residue, it's a GLY\n";
# 		    last;
# 		}elsif ($pdbaa{$residue} eq "ALA"){
# 		    print "no point in repacking $residue, it's an ALA\n";
# 		    last;
# 		}
# 	    }
# 	}
#     }
# # Hydrophobic residues
#     if (defined $hphobic) {
# 	open (FILE, $hphobic);
# 	chomp (my $buf = <FILE>);
# 	close FILE;
# 	$buf =~ s/^\s+|\s+$//g;
# 	@hphobic = split (/,/, $buf);
# 	foreach my $residue(@hphobic){
# 	    $residue =~ s/^\s+|\s+$//;
# 	    foreach my $line (@resfile_buf) {
# 		if ($residue == substr($line,0,3)) {
# 		    substr($line,5) = "3 1 0 0 0 1 0 0 1 0 1 1 0 1 0 0 0 0 1 1 1";
# 		    last;
# 		}
# 	    }
# 	}
#     }
# # Charged residues
#     if (defined $charged) {
# 	open (FILE, $charged);
# 	chomp (my $buf = <FILE>);
# 	close FILE;
# 	$buf =~ s/^\s+|\s+$//g;
# 	@charged = split (/,/, $buf);
# 	foreach my $residue(@charged){
# 	    $residue =~ s/^\s+|\s+$//;
# 	    foreach my $line (@resfile_buf) {
# 		if ($residue == substr($line,0,3)) {
# 		    substr($line,5) = "3 0 0 1 1 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0";
# 		    last;
# 		}
# 	    }
# 	}
#     }
# # Polar residues
#     if (defined $polar) {
# 	open (FILE, $polar);
# 	chomp (my $buf = <FILE>);
# 	close FILE;
# 	$buf =~ s/^\s+|\s+$//g;
# 	@polar = split (/,/, $buf);
# 	foreach my $residue(@polar){
# 	    $residue =~ s/^\s+|\s+$//;
# 	    foreach my $line (@resfile_buf) {
# 		if ($residue == substr($line,0,3)) {
# 		    substr($line,5) = "3 0 0 0 0 0 0 1 0 0 0 0 1 0 1 0 1 1 0 1 1";
# 		    last;
# 		}
# 	    }
# 	}
#     }
# # Aromatic residues
#     if (defined $aromatic) {
# 	open (FILE, $aromatic);
# 	chomp (my $buf = <FILE>);
# 	close FILE;
# 	$buf =~ s/^\s+|\s+$//g;
# 	@aromatic = split (/,/, $buf);
# 	foreach my $residue(@aromatic){
# 	    $residue =~ s/^\s+|\s+$//;
# 	    foreach my $line (@resfile_buf) {
# 		if ($residue == substr($line,0,3)) {
# 		    substr($line,5) = "3 0 0 0 0 1 0 1 0 0 0 0 0 0 0 0 0 0 0 1 1";
# 		    last;
# 		}
# 	    }
# 	}
#     }

# # Repack all residues not being designed
#     if (defined $repackall) {
# 	foreach my $line (@resfile_buf) {
# 	    my $residue = substr($line,0,3);
# 	    if (substr($line,5,1) == 1 
# 		&& $pdbaa{$residue} ne "GLY"
# 		&& $pdbaa{$residue} ne "ALA"
# 		&& $pdbaa{$residue} ne "CYS"
# 		){
# 		substr($line,5,1) = 2;	
# 	    }
# 	}
#     }

#     unshift (@resfile_buf, "    id A C D E F G H I K L M N P Q R S T V W Y ");
#     unshift (@resfile_buf, sprintf ("%3d", ($#res_num+1)));
# }
