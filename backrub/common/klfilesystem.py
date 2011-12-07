import os
import stat
import shutil
import subprocess
import colortext

# todo: Remove these from rosettahelper
permissions755SGID = stat.S_ISGID | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
permissions755     =                stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
permissions775     =                stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH

class FileSysStats(object):
	B = 1
	KB = 1024.0
	MB = 1024.0 * KB
	GB = 1024.0 * MB
	TB = 1024.0 * GB

	def __init__(self, unit = None):
		self.m_unit = unit or self.B

	def setDefaultUnit(self, unit):
		self.m_unit = unit

	def getHumanReadable(self, v):
		if v < self.KB:
			return "%b B" % v
		elif v < self.MB:
			return "%.2f KB" % (v / self.KB)
		elif v < self.GB:
			return "%.2f MB" % (v / self.MB)
		elif v < self.TB:
			return "%.2f GB" % (v / self.GB)
		else:
			return "%.2f TB" % (v / self.TB)

class FileStats(FileSysStats):
	
	def __init__(self, filelocation, unit = None):
		unit = None or self.MB
		super(FileStats, self).__init__(unit)
		s = os.stat(filelocation)
		self.stats = s
		self.m_size = float(s.st_size)
	
	def getSize(self, unit = None):
		return self.m_size / (unit or self.m_unit)

	def getHumanReadableSize(self):
		return self.getHumanReadable(self.m_size)

class FolderStats(FileSysStats):
	
	def __init__(self, folderpath, unit = None):
		unit = None or self.MB
		super(FolderStats, self).__init__(unit)
		
		p = subprocess.Popen(["du", "-b", folderpath], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		stdoutdata, stderrdata = p.communicate()
		stdoutdata = stdoutdata.split("\n")[-1]
		
		if stderrdata:
			raise(colortext.Exception(stderrdata))
		
		self.m_size = float(stdoutdata.split()[0])
		
	def getSize(self, unit = None):
		return self.m_size / (unit or self.m_unit)

	def getHumanReadableSize(self):
		return self.getHumanReadable(self.m_size)

class DiskStats(FileSysStats):
	
	def __init__(self, filelocation, unit = None):
		unit = None or self.MB
		super(DiskStats, self).__init__(unit)
		s = os.statvfs(filelocation)
		self.stats = s
		self.m_size = float(s.f_blocks * s.f_frsize)
		self.m_free = float(s.f_bsize * s.f_bavail)
		self.m_unit = unit or self.m_unit
			
	def getSize(self, unit = None):
		return self.m_size / (unit or self.m_unit)

	def getFree(self, unit = None):
		return self.m_free / (unit or self.m_unit)
	
	def getUsagePercentage(self):
		return 100 - 100 * (float(self.getFree()) / float(self.getSize()))

def targzDirectory(inpath, outfile, stdout = None, stderr = None):
	if os.path.exists(outfile):
		raise colortext.Exception("The output file '%s' already exists." % outfile)
	if not os.path.exists(inpath):
		raise colortext.Exception("The input directory '%s' does not exist." % inpath)
	if not os.path.exists(os.path.dirname(outfile)):
		raise colortext.Exception("The parent directory '%s' of '%s' does not exist." % (os.path.dirname(outfile), outfile))
	p = subprocess.Popen(["tar", "-zcvf", outfile, inpath], stdout = stdout, stderr = stderr)
	stdoutdata, stderrdata = p.communicate()
	if stderrdata:
		raise colortext.Exception("\nFailure/warning during zip:\n%s" % stderrdata)
	return stdoutdata, stderrdata
	
def safeMkdir(p, permissions = permissions755):
	'''Wrapper around os.mkdir which does not raise an error if the directory exists.'''
	try:
		os.mkdir(p)
	except OSError:
		pass
	os.chmod(p, permissions)

def getSubdirectories(d):
	'''Returns a list of subdirectories in a directory.
		This function performed three times better for me than 
		"for root, dirs, files in os.walk(d):
			return dirs"
	'''
	return [f for f in os.listdir(d) if os.path.isdir(f) ]
