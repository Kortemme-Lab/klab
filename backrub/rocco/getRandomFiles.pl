#!/usr/bin/perl

if(($#ARGV+1) != 3)
{
  print "\n\nThis script reads in the location where the backrub files are located and randomly selects a subset of them.\n"; 
  print "\nUsage:   perl getRandomFiles.pl directory keyword numRandSamples"; 
  print "\nExample: perl getRandomFiles.pl Backrub/1RTH_ensemble last 100\n\n"; 
  exit;
}

my $path = $ARGV[0]; 
my $keyword = $ARGV[1];
my $numsamples = $ARGV[2];
my @files = `ls $path \| grep $keyword `;
my %uniquefiles = ();
my $index = 0;
my $filename;
#print "Number of pdb files: ".scalar(@files)."\n";
#exit;

my $numUniquesSelected = 0;
while ($numUniquesSelected != $numsamples)
{
  $index = rand(@files);
  #print "index = $index\n";
  $filename = $files[$index];
  if (exists $uniquefiles{$filename})
  {
    # do nothing, keep looking
  }
  else # doesn't exist already so make note if it
  {
    $uniquefiles{$filename} = 1;
    $numUniquesSelected++;
  }
}


#print "\nThe randomly selected unique file acquired from $path are: ". keys(%uniquefiles) . "\n";
foreach my $key (keys %uniquefiles)
{
  my @patharray = split(m//, $path);
  if($patharray[-1] == '/')
  { 
    print "$path$key";
  }
  else
  {
    print "$path/$key";
  }
}


