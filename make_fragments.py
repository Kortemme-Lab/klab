#!/usr/bin/python
# -*- coding: utf-8 -*-
# Created 2011-10-13 by Shane O'Connor, Kortemme Lab

import sys
import os
import re
from string import join, strip
import shutil
import subprocess
import traceback
import time
from datetime import datetime
from optparse import OptionParser

ERRCODE_ARGUMENTS = 1
ERRCODE_CLUSTER = 2
ERRCODE_OLDRESULTS = 3
ERRCODE_CONFIG = 4

logfile = "make_fragments_destinations.txt"
	
cmd = '/netapp/home/klabqb3backrub/r3.3/rosetta_tools/make_fragments_netapp.pl -verbose -noporter -id %(pdbid)s%(chain)s %(fasta)s'

# A successful job contains the following in the stdout file.
# Also, any files of the form aa<pdbid><chain>_picker_cmd_size<numder>.log should have size zero 
Notes = '''
sam file ok
...
Checking frag file format: aa1cyoA.3mers
Format okay!
Checking frag file format: aa1cyoA.9mers
Format okay!
aa1cyoA03_05.200_v1_3
aa1cyoA09_05.200_v1_3
Done!'''

template ='''
#!/bin/csh	    
#$ -N fragment_generation	    
#$ -o %(outpath)s	    
#$ -e %(outpath)s	    
#$ -cwd	    
#$ -r y	    
#$ -l mem_free=1G	    
#$ -l arch=lx24-amd64	    
#$ -l h_rt=24:00:00	    

#setenv LD_LIBRARY_PATH /netapp/home/shaneoconner/fragtest
#env

echo "<make_fragments>"
echo "<startdate>"
date
echo "</startdate>"
echo "<host>"
hostname
echo "</host>"
echo "<cwd>"
pwd
echo "</cwd>"
echo "<arch>"
uname -i
echo "</arch>"

#ls -latr /lib/

cd %(outpath)s

#ldd  /netapp/home/klabqb3backrub/make_fragments/porter/Distill_JC/Porter/Porter'''

template += '''
echo "<cmd>%(cmd)s</cmd>"
%(cmd)s
'''  % vars()

template += '''
echo "<startdate>"
date
echo "</startdate>"

echo "</make_fragments>"
'''

def getUsername():
	return subprocess.Popen("whoami", stdout=subprocess.PIPE).communicate()[0].strip()

def printError(s):
	print('\033[91m%s\033[0m' %s) #\x1b\x5b1;31;40m%s\x1b\x5b0;40;40m' % s)

def printPrompt(s = None):
	if s:
		print('\033[93m%s\033[0m' %s) #\x1b\x5b1;31;40m%s\x1b\x5b0;40;40m' % s)
	else:
		sys.stdout.write("\033[93m $ \033[0m")								

def printMessage(s):
	print('\033[92m%s\033[0m' %s) #\x1b\x5b1;31;40m%s\x1b\x5b0;40;40m' % s)

def parseArgs():
	errors = []
	pdbpattern = re.compile("^\w{4}$")
	description = ["e.g. make_fragments.py -p 1KI1 -c B -f /path/to/1KI1.fasta.txt."]
	description.append("The output of the computation will be saved in the output directory, along with the input FASTA files which is generated from the supplied FASTA file.")
	description.append("A log of the output directories for cluster jobs is saved in %s in the current directory, to help locate run data." % logfile)
	description.append("Warning: Do not reuse the same output directory for multiple runs. Results from a previous run may confuse the executable chain and lead to erroneous results.")
	description.append("To prevent this occurring e.g. in batch submissions, use the -S option to create the results in a subdirectory of the output directory.")
	description = join(description, "\n")
	parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0", description = description)
	parser.add_option("-f", "--fasta", dest="fasta", help="The input FASTA file. This defaults to OUTPUT_DIRECTORY/PDBID.fasta.txt if the PDB ID is supplied.", metavar="FASTA")
	parser.add_option("-c", "--chain", dest="chain", help="Chain used for the fragment. This is optional so long as the FASTA file only contains one chain.", metavar="CHAIN")
	parser.add_option("-p", "--pdbid", dest="pdbid", help="The input PDB identifier. This is optional if the FASTA file is specified and only contains one PDB identifier.", metavar="PDBID")
	parser.add_option("-d", "--outdir", dest="outdir", help="Optional. Output directory relative to user space on netapp. Defaults to the current directory so long as that is within the user's netapp space.", metavar="OUTPUT_DIRECTORY")
	parser.add_option("-Q", "--qstat", dest="qstat", action="store_true", help="Optional. Query qstat results against %s and then quit." % logfile)
	parser.add_option("-S", "--subdirs", dest="subdirs", action="store_true", help="Optional. Create a subdirectory in the output directory named <PDBID><CHAIN>. See the notes above.")
	parser.add_option("-N", "--noprompt", dest="noprompt", action="store_true", help="Optional. Create the output directory without prompting.")
	parser.set_defaults(outdir = os.getcwd())
	parser.set_defaults(noprompt = False)
	parser.set_defaults(subdirs = False)
	parser.set_defaults(qstat = False)
	(options, args) = parser.parse_args()
	
	username = getUsername()
	if len(args) >= 1:
		errors.append("Unexpected arguments: %s." % join(args, ", "))
	
	# qstat
	if options.qstat:
		qstat()
		
	# PDB ID
	if options.pdbid and not pdbpattern.match(options.pdbid): 
		errors.append("Please enter a valid PDB identifier.")
	
	# CHAIN
	if options.chain and not (len(options.chain) == 1):
		errors.append("Chain must only be one character.")
	
	# OUTDIR
	outpath = options.outdir
	if outpath[0] != "/":
		outpath = os.path.join(os.getcwd(), outpath)
	userdir = os.path.join("/netapp/home", username)
	outpath = os.path.normpath(outpath)
	if os.path.commonprefix([userdir, outpath]) != userdir:
		errors.append("Please enter an output directory inside your netapp space.")
	else:
		if not os.path.exists(outpath):
			if not options.noprompt:
				answer = ""
				printPrompt("Output path '%(outpath)s' does not exist. Create it now with 755 permissions (y/n)?" % vars())
				while answer not in ['Y', 'N']:
					printPrompt()
					answer = sys.stdin.readline().upper().strip()
				if answer == 'Y':
					try:
						pass
						#os.makedirs(outpath, 0755)
					except Exception, e:
						errors.append(str(e))
						errors.append(traceback.format_exc())
				else:
					errors.append("Output directory '%s' does not exist." % outpath)
			else:
				try:
					pass
					#os.makedirs(outpath, 0755)
				except Exception, e:
					errors.append(str(e))
					errors.append(traceback.format_exc())

	# FASTA
	if options.fasta:
		if not os.path.isabs(options.fasta):
			options.fasta= os.path.realpath(options.fasta)
	if options.pdbid and not options.fasta:
		options.fasta = os.path.join(outpath, "%s.fasta.txt" % options.pdbid)
	if not options.fasta:
		if options.qstat:
			sys.exit(0)
		else:
			parser.print_help()
			sys.exit(ERRCODE_ARGUMENTS)
	if not os.path.exists(options.fasta):
		errors.append("FASTA file %s does not exists." % options.fasta)
	elif not errors:
		fastadata = None
		try:
			fastadata = parseFASTA(options.fasta)
			if not fastadata:
				errors.append("No data found in the FASTA file %s." % options.fasta)
				
		except Exception, e:
			errors.append("Error parsing FASTA file %s:\n%s" % (options.fasta, str(e)))
		
		if fastadata:
			sequencecount = len(fastadata)
			recordfrequency = {}
			for record in fastadata.keys():
				k = (record[1], record[2])
				recordfrequency[k] = recordfrequency.get(k, 0) + 1 
			multipledefinitions = ["\tPDB ID: %s, Chain %s" % (record[0], record[1]) for record, count in sorted(recordfrequency.iteritems()) if count > 1]
			chainspresent = sorted([record[2] for record in fastadata.keys()])
			pdbidspresent = sorted(list(set([record[1] for record in fastadata.keys()])))
			if len(multipledefinitions) > 0:
				errors.append("The FASTA file %s contains multiple sequences for the following chains:\n%s.\nPlease edit the file and remove the unnecessary chains." % (options.fasta, join(multipledefinitions, "\n")))				 
			elif sequencecount == 0:
				errors.append("No sequences found in the FASTA file %s." % options.fasta)
			else:
				if not options.chain and sequencecount > 1: 
					errors.append("Please enter a chain. Valid chains are: %s." % join(chainspresent, ", "))
				elif not options.pdbid and len(pdbidspresent) > 1:
					errors.append("Please enter a PDB identifier. Valid IDs are: %s." % join(pdbidspresent, ", "))	
				else:
					foundsequence = None
					
					if sequencecount == 1:
						key = fastadata.keys()[0]
						(temp, options.pdbid, options.chain) = key
						foundsequence = fastadata[key]
						printMessage("One chain and PDB ID pair (%s, %s) found in %s. Using that pair as input." % (options.chain, options.pdbid, options.fasta))
					elif not options.pdbid:
						assert(len(pdbidspresent) == 1)
						options.pdbid = pdbidspresent[0]
						printMessage("No PDB ID specified. Using the only one present in the fasta file, %s." % options.pdbid)
						if sequencecount > 1:
							for (recordnumber, pdbid, chain), sequence in sorted(fastadata.iteritems()):
								if pdbid.upper() == options.pdbid.upper() and chain == options.chain:
									foundsequence = sequence						
					
					# This line determines in which case the filenames will be generated for the command chain
					options.pdbid = options.pdbid.lower()
					
					# Create subdirectories if specified
					assert(options.pdbid and options.chain)
					if options.subdirs:
						newoutpath = os.path.join(outpath, "%s%s" % (options.pdbid, options.chain))
						if os.path.exists(newoutpath):
							count = 1
							while count < 1000:
								newoutpath = os.path.join(outpath, "%s%s_%.3i" % (options.pdbid, options.chain, count))
								if not os.path.exists(newoutpath):
									break						
								count += 1
							if count == 1000:
								printError("The directory %s contains too many previous results. Please clean up the old results or choose a new output directory." % outpath)
								sys.exit(ERRCODE_OLDRESULTS)
						outpath = newoutpath
						os.makedirs(outpath, 0755)

					# Create a pruned FASTA file in the output directory
					if foundsequence:
						fpath, ffile = os.path.split(options.fasta)
						newfile = os.path.join(outpath, "%s%s.fasta" % (options.pdbid, options.chain))
						printMessage("Creating a new FASTA file %s." % newfile) 
						
						writefile = True
						if os.path.exists(newfile):
							printPrompt("The file %(newfile)s exists. Do you want to overwrite it?" % vars())
							answer = None
							while answer not in ['Y', 'N']:
								printPrompt()
								answer = sys.stdin.readline().upper().strip()
							if answer == 'N':
								writefile = False
								errors.append("Please remove the existing file %(newfile)s to continue." % vars())
						if writefile:
							F = open(newfile, "w")
							for line in foundsequence:
								F.write("%s" % line)
							F.close()
							options.fasta = newfile
					else:
						errors.append("Could not find the sequence for chain %s in structure %s in FASTA file %s." % (options.chain, options.pdbid, options.fasta))
	if errors:
		print("")
		for e in errors:
			printError(e)
		print("")
		parser.print_help()
		sys.exit(ERRCODE_ARGUMENTS)
	
	return {
		"user"  : username,
		"outpath": outpath,
		"pdbid" : options.pdbid,
		"chain" : options.chain,
		"fasta" : options.fasta,
		}

class FastaException(Exception): pass
def parseFASTA(fastafile): 
	F = open(fastafile, "r")
	fasta = F.readlines()
	F.close()
	
	chainLine = re.compile("^>(\w{4}):(\w)|PDBID|CHAIN|SEQUENCE\n?$")
	sequenceLine = re.compile("^[ACDEFGHIKLMNPQRSTVWY]+\n?$")
	
	records = {}
	pdbid = None
	chain = None
	count = 1
	recordcount = 0
	for line in fasta:
		if line.strip():
			if chain == None and pdbid == None:
				mtchs = chainLine.match(line)
				if not mtchs:
					raise FastaException("Expected a record header at line %d." % count)
			
			mtchs = chainLine.match(line)
			if mtchs:
				recordcount += 1
				pdbid = (mtchs.group(1))
				chain = (mtchs.group(2))
				records[(recordcount, pdbid, chain)] = [line]
			else:
				mtchs = sequenceLine.match(line)
				if not mtchs:
					raise FastaException("Expected a record header or sequence line at line %d." % count)
				records[(recordcount, pdbid, chain)].append(line)
				
		count += 1
	return records

def qstat():
	""" Returns a table of jobs run by the user."""
	
	#2011-10-17T11:50:43.799896: Job ID 6777279 results will be saved in /netapp/home/shaneoconner/fragtestMonday3.
	
	F = open(logfile, "r")
	joblist = F.read().strip().split("\n")
	F.close()
	
	reg = re.compile("^(.*): Job ID (\d+) results will be saved in (.+)\.$")
	jobDirs = {}
	jobTimes = {}
	for job in joblist:
		mtchs = reg.match(job)
		if mtchs:
			jobID = int(mtchs.group(2))
			jobDirs[jobID] = mtchs.group(3)
			nt = mtchs.group(1)
			nt = nt.replace("-", "")
			nt = nt[:nt.find(".")]
			timetaken = datetime.now() - datetime(*time.strptime(nt, "%Y%m%dT%H:%M:%S")[0:6])
			jobTimes[jobID] = timetaken.seconds
		else:
			printError("Error parsing logfile: '%s' does not match regex." % job)
	
	command = ['qstat']
	output = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0]
	# Form command
	output = output.strip().split("\n")
	jobs = {}
	if len(output) > 2:
		for line in output[2:]:
			# We assume that our script names contain no spaces for the parsing below to work (this should be ensured by ClusterTask) 
			tokens = line.split()
			jid = int(tokens[0])
			jobstate = tokens[4]
						
			details = {  "jobid" : jid,
						 "prior" : tokens[1],
						 "name" : tokens[2],
						 "user" : tokens[3],
						 "state" : jobstate,
						 "submit/start at" : "%s %s" % (tokens[5], tokens[6])
						 }			
			jataskID = 0
			if jobstate == "r":
				details["queue"] = tokens[7]
				details["slots"] = tokens[8]
			elif jobstate == "qw":
				details["slots"] = tokens[7]
				if len(tokens) >= 9:
					jataskID = tokens[8]
					details["ja-task-ID"] = jataskID
					
			if len(tokens) > 9:
				jataskID = tokens[9]
				details["ja-task-ID"] = jataskID
				
			jobs[jid] = jobs.get(jid) or {}
			jobs[jid][jataskID] = details
			if jobDirs.get(jid):
				print("Job %d submitted %d minutes ago. Status: '%s'. Destination directory: %s." % (jid, jobTimes[jid] / 60, jobstate, jobDirs[jid]))
			else:
				print("Job %d submitted at %s %s. Status: '%s'. Destination directory unknown." % (jid, tokens[5], tokens[6], jobstate))

	
def qsub(command_filename, workingdir, hold_jobid = None, showstdout = False):
	'''Submit the given command filename to the queue. Adapted from the qb3 example.'''

	# Open streams
	command_filename = command_filename
	outfile = command_filename + ".out"
	file_stdout = open(outfile, 'w')
	
	# Form command
	command = ['qsub']
	if hold_jobid:
		command.append('-hold_jid')
		command.append('%d' % hold_jobid)
	command.append(command_filename)
	
	# Submit the job and capture output.
	try:
		subp = subprocess.Popen(command, stdout=file_stdout, stderr=file_stdout, cwd=workingdir)
	except Exception, e:
		printError('Failed running qsub command: %s in cwd %s.' % (command, workingdir))
		raise

	waitfor = 0
	errorcode = subp.wait()
	file_stdout.close()

	file_stdout = open(outfile, 'r')
	output = strip(file_stdout.read())
	file_stdout.close()

	if errorcode != 0:
		printError('Failed running qsub command: %s in cwd %s.' % (command, workingdir))
		if output.find("unable to contact qmaster") != -1:
			raise Exception("qsub failed: unable to contact qmaster")
		else:
			raise Exception(output)

	# Match job id
	# This part of the script may be error-prone as it depends on the server message.
	matches = re.match('Your job-array (\d+).(\d+)-(\d+):(\d+)', output)
	if not matches:
		matches = re.match('Your job (\d+) \(".*"\) has been submitted.*', output)

	if matches:
		jobid = int(matches.group(1))
	else:
		jobid = -1

	output = output.replace('"', "'")
	if output.startswith("qsub: ERROR"):
		raise Exception(output)
	print(output)

	os.remove(outfile)
	os.remove(command_filename)

	return jobid, output

def searchConfigurationFiles(findstr, replacestr = None):
	'''This function could be used to find and replace paths in the configuration files.
		At present, it only finds phrases.'''
		
	F = open("make_fragments_confs.txt", "r")
	allerrors = {}
	alloutput = {}
	
	for line in F.readlines():
		line = line.strip()
		if line:
			if line.endswith("make_fragments.py"):
				# Do not parse the Python script but check that it exists
				if not(os.path.exists(line)):
					allerrors[line] = "File/directory %s does not exist." % line
			else:
				cmd = ["grep", "-n", "-i",  findstr, line]
				output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
				errors = output[1]
				output = output[0]
				if errors:
					errors = errors.strip()
					allerrors[line] = errors
				if output:
					output = output.strip()
					alloutput[line] = output.split("\n")
	return alloutput, allerrors

def checkConfigurationPaths():
	pathregex1 = re.compile('.*"(/netapp.*?)".*')
	pathregex2 = re.compile('.*".*(/netapp.*?)\\\\".*')
	alloutput, allerrors = searchConfigurationFiles("netapp")
	errors = []
	if allerrors:
		for flname, errs in sorted(allerrors.iteritems()):
			errors.append((flname, [errs]))
	for flname, output in sorted(alloutput.iteritems()):
		m_errors = []
		for line in output:
			mtchs = pathregex1.match(line) or pathregex2.match(line)
			if not mtchs:
				m_errors.append("Regex could not match line: %s." % line)
			else:
				dir = mtchs.group(1).split()[0]
				if not os.path.exists(dir):
					m_errors.append("File/directory %s does not exist." % dir)
		if m_errors:
			errors.append((flname, m_errors))
		
	return errors

if __name__ == "__main__":
	errors = checkConfigurationPaths()
	if errors:
		printError("There is an error in the configuration files:")
		for e in errors:
			print("")
			flname = e[0]
			es = e[1]
			printPrompt(flname)
			for e in es:
				printError(e)
		sys.exit(ERRCODE_CONFIG)
			
	options = parseArgs()
	template = template % options
	qcmdfile = os.path.join(options["outpath"], "make_fragments_temp.cmd")
	F = open(qcmdfile, "w")
	F.write(template)
	F.close()
	
	try:
		(jobid, output) = qsub(qcmdfile, options["outpath"] )
	except Exception, e:
		printError("An exception occurred during submission to the cluster.")
		printError(str(e))
		printError(traceback.format_exc())
		sys.exit(ERRCODE_CLUSTER)
	
	printMessage("\nmake_fragments jobs started with job ID %d. Results will be saved in %s." % (jobid, options["outpath"]))
	F = open(logfile, "a")
	F.write("%s: Job ID %d results will be saved in %s.\n" % (datetime.now().isoformat(), jobid, options["outpath"]))
	F.close()
	

