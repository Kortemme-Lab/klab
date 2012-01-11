import os
import subprocess
import sys
import datetime
import shutil
sys.path.insert(0, "../common/")

import colortext
from klfilesystem import FileSysStats, FileStats, FolderStats, DiskStats, targzDirectory, safeMkdir, getSubdirectories, computeMD5

# Leave at least 30 GB free
MIN_DISK_SPACE_IN_GB = 30

# Only allow this script to be run when disk usage is above this percentage
MIN_DISK_USAGE = 94

def logmessage(str, suffix = "\n"):
	global Log
	str = colortext.make(str, color = 'green', suffix = suffix)
	sys.stdout.write(str)
	sys.stdout.flush()
	Log.write(str)
	Log.flush()
	
def main():	
	
	cwd = os.getcwd()
	assert(cwd == "/var/www/html/rosettaweb/backrub/archive")
	
	# Create the directories for compressed jobs and those ready for deletion.
	# For safety, we do not delete those ready for deletion automatically.
	zipdir = os.path.join(cwd, "forarchival")
	deldir = os.path.join(cwd, "fordeletion")
	safeMkdir(zipdir)
	safeMkdir(deldir)
	
	# Check to see if this run is necessary
	ds = DiskStats(cwd)
	if ds.getUsagePercentage() < MIN_DISK_USAGE:
		colortext.warning("You should only run this script when the disk is at %0.2f%% usage. If you want to force an archive, you need to edit the script." % MIN_DISK_USAGE)
		sys.exit(1)
	
	# Get a sorted list of the numbered directories
	jobIDs = sorted([int(d) for d in getSubdirectories(cwd) if d.isdigit()])
	
	md5file = open("md5sum_%d-%d.txt" % (jobIDs[0], jobIDs[-1]), "w")
	
	# Iterate through the archived job directories, zipping and moving
	b_folders = 0
	b_zips = 0
	count = 0
	for d in jobIDs:
		ds = DiskStats(cwd)
		
		# Leave at least 30 GB free
		colortext.error("Disk space free: %.2f GB." % ds.getFree(unit = ds.GB))
		if ds.getFree(unit = ds.GB) > MIN_DISK_SPACE_IN_GB:
			# Get the directory size
			subdir = os.path.join(cwd, str(d))
			logmessage("Processing %s: " % subdir, suffix = "")
			pStats = FolderStats(subdir)
			
			# Zip and get the resulting size
			zipfile = os.path.join(zipdir, "%d.tar.gz" % d)
			t, s = targzDirectory(str(d), zipfile, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
			colortext.warning(t.strip())			
			zStats = FileStats(zipfile)
			
			md5hash = computeMD5(zipfile)
			colortext.printf("MD5 checksum: %s\n" % md5hash, color = "lightblue")
			md5file.write("%s\n" % md5hash)
			m5F = open(os.path.join(zipdir, "%d.tar.gz.md5" % d), "w")
			m5F.write("%s\n" % md5hash)
			m5F.close()
			
			# Update counters
			b_folders += pStats.m_size
			b_zips += zStats.m_size
			
			# Print stats
			compression = pStats.m_size / zStats.m_size
			logmessage("Compression rate %.2fx (%s -> %s)." % (compression, pStats.getHumanReadableSize(), zStats.getHumanReadableSize()), suffix = "")
			
			# Move the folder
			shutil.move(subdir, os.path.join(deldir, str(d)))
			
			logmessage("Done.")
			count += 1
		else:
			break
	
	md5file.close()
	
	if b_zips and b_folders:
		compression = b_folders / b_zips
		b_folders = FileSysStats().getHumanReadable(b_folders)
		b_zips = FileSysStats().getHumanReadable(b_zips)

		logmessage("\nArchived %d folders. " % count, suffix = "")
		logmessage("Compression rate %.2fx (%s -> %s)." % (compression, b_folders, b_zips))

def splitmd5file():
	'''One-off functfile:///mnt/Tantalus/website/archive/770-1335/1245.tar.gzion for splitting a text file of md5 checksums.'''
	F = open("md5sum_770-1335.txt", "r")
	safeMkdir(os.path.join(os.getcwd(), "md5"))
	for line in F.readlines():
		filename = line.split()[1] + ".md5"
		mF = open(os.path.join(os.getcwd(), "md5", filename), "w")
		mF.write(line)
		mF.close()
	F.close()

t = datetime.datetime.today()
datestamp = "%s-%s-%s_%s.%s" % (t.year, t.month, t.day, t.hour, t.minute)
Log = open("log-%s.txt" % datestamp, "w")
main()
Log.close()
