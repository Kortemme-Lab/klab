import sys
import re
import datetime
import time

class LogFile(object):

    class LogFileException(Exception): pass

    def __init__(self, flname):
        self.logfile = flname
        self.format = "%s: Job ID %s results will be saved in %s.%s"
        self.regex = re.compile(self.format % ("^(.*)", "(\\d+)", "(.+)\\", "$"))

    def getName(self):
        return self.logfile

    def readFromLogfile(self):
        joblist = {}
        F = open(self.logfile, "r")
        lines = F.read().strip().split("\n")
        F.close()
        for line in lines:
            mtchs = self.regex.match(line)
            if mtchs:
                jobID = int(mtchs.group(2))
                jobdir = mtchs.group(3)
                nt = mtchs.group(1)
                nt = nt.replace("-", "")
                nt = nt[:nt.find(".")]
                timetaken = datetime.datetime.now() - datetime.datetime(*time.strptime(nt, "%Y%m%dT%H:%M:%S")[0:6])
                jobtime = timetaken.seconds
                joblist[jobID] = {"Directory" : jobdir, "TimeInSeconds" : jobtime}
            else:
                raise LogFileException("Error parsing logfile: '%s' does not match regex." % line)
        return joblist

    def writeToLogfile(self, o_datetime, jobid, location):
        F = open(self.logfile, "a")
        F.write(self.format % (o_datetime.isoformat(), jobid, location, "\n"))
        F.close()

class colorprinter(object):

    @staticmethod
    def error(s):
        print('\033[91m%s\033[0m' %s) #\x1b\x5b1;31;40m%s\x1b\x5b0;40;40m' % s)

    @staticmethod
    def warning(s):
        print('\033[93m%s\033[0m' %s) #\x1b\x5b1;31;40m%s\x1b\x5b0;40;40m' % s)

    @staticmethod
    def prompt(s = None):
        if s:
            print('\033[93m%s\033[0m' %s) #\x1b\x5b1;31;40m%s\x1b\x5b0;40;40m' % s)
        else:
            sys.stdout.write("\033[93m $ \033[0m")

    @staticmethod
    def message(s):
        print('\033[92m%s\033[0m' %s) #\x1b\x5b1;31;40m%s\x1b\x5b0;40;40m' % s)
