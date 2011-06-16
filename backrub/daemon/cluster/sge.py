#!/usr/bin/python2.4
# encoding: utf-8
"""
sge.py

Created by Shane O'Connor 2011.
Copyright (c) 2011 __UCSF__. All rights reserved.
"""


import sys
if __name__ == "__main__":
    sys.path.insert(0, "../")
import commands
import re
import subprocess
import time
from string import join, strip
from conf_daemon import *

DEBUG = False

qstatus = {
    'r'    :    'active',
    'qw'   :    'pending',
    't'    :    'transferring',
}

class SGEConnection(object):
         
    def __init__(self):
        self.pauseBetweenQStats = float(CLUSTER_qstatpause) - 0.2
        self.lastCalled = time.time() - self.pauseBetweenQStats - 0.2    # So we can be called immediately
        self.OldCachedList = {}
        self.CachedList = None
        self.mapClusterToDB = {}
    
    # SGE Functions
    
    def qstat(self, waitForFresh = False, force = False, user = CLUSTER_UserAccount):
        """ Returns a table of jobs run by the user.
            If waitForFresh is true, this call blocks and waits until qstat can be called again.
            If so, or if force is true, we call qstat and return the results.
            Otherwise, return the cached list of jobs. """
        
        #debug: for testing without submission - 
        if DEBUG:
            return {}
        
        if not force and waitForFresh:
            currentTime = time.time()
            if self.lastCalled + CLUSTER_qstatpause > currentTime:
                # Use min(CLUSTER_qstatpause,_) here in case something goes screwy
                timeToSleep = min(CLUSTER_qstatpause, self.lastCalled + CLUSTER_qstatpause - currentTime)
                time.sleep(timeToSleep)
            force = True
            
        if force or self.CachedList == None:
            if self.lastCalled > 0 and ((time.time() - self.lastCalled) < self.pauseBetweenQStats):
                print('<sge warning="QSTAT is being called more regularly than %fs."/>' % qstatWaitingPeriod)
            
            self.lastCalled = time.time()
            
            command = 'qstat -u "%s"' % user
            output = commands.getoutput(command)
            output = output.split("\n")
            jobs = {}
            if len(output) > 2:
                newmapClusterToDB = {}
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
                    if DEBUG:
                        details["line"] = line
                        details["tokens"] = tokens
                    
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

                    # Rebuild mapClusterToDB otherwise its size would keep increasing 
                    dbID = self.mapClusterToDB.get(jid)
                    if dbID:
                        newmapClusterToDB[jid] = dbID

                self.mapClusterToDB = newmapClusterToDB

            self.OldCachedList = self.CachedList or {}
            self.CachedList = jobs
        
        return self.CachedList
    
    def qdel(self, jobid):
        user = "klabqb3backrub"
        if jobid == "all":
            command = 'qdel -u klabqb3backrub'
        else:
            command = 'qdel %d' % jobid
        status, output = commands.getstatusoutput(command)
        return status, output
        
    def qsub_submit(self, command_filename, workingdir, dbID, hold_jobid = None, name = None, showstdout = False):
        """Submit the given command filename to the queue.
        
        ARGUMENTS
            command_filename (string) - the name of the command file to submit
        
        OPTIONAL ARGUMENTS
            hold_jobid (int) - job id to hold on as a prerequisite for execution
        
        RETURNS
            jobid (integer) - the jobid
        """
        
        #debug: for testing without submission - 
        if DEBUG:
            return 1
    
        # Open streams
        file_stdout = open(command_filename + ".temp.out", 'w')
        file_stderr = open(command_filename + ".temp.out", 'w')
            
        # Form command
        command = ['qsub']
        if name:
            command.append('-N')
            command.append('%s' % name)
        if CLUSTER_debugmode:
            command.append('-q')
            command.append('short.q')
        if hold_jobid:
            command.append('-hold_jid')
            command.append('%d' % hold_jobid)
        command.append('%s' % command_filename)
        
        # Submit the job and capture output.
        try:
            subp = subprocess.Popen(command, stdout=file_stdout, stderr=file_stderr, cwd=workingdir)
        except Exception, e:
            print('<sge message="Failed running qsub command: %s in cwd %s"/>' % (command, workingdir))
            raise
        
        waitfor = 0
        errorcode = subp.wait()
        file_stdout.close()
        file_stdout = open(command_filename + ".temp.out", 'r')
        output = strip(file_stdout.read())
        file_stdout.close()
        file_stderr.close()
            
        # Match job id
        # This part of the script is probably error-prone as it depends on the server message.
        matches = re.match('Your job-array (\d+).(\d+)-(\d+):(\d+)', output)
        if not matches:
            matches = re.match('Your job (\d+) \(".*"\) has been submitted.*', output)
        
        if matches:
            jobid = int(matches.group(1))
            self.mapClusterToDB[jobid] = dbID
        else:
            jobid = -1
        
        output = output.replace('"', "'")
        msg = '<sge message="%s"/>' % output
        if output.startswith("qsub: ERROR"):
            raise Exception(msg)            
        print(msg)
            
        return jobid, output
        
    # Informational functions

    def cachedStatus(self, jobid):
        return self.CachedList.get(jobid)
                                        
    def qdiff(self):
        difftbl = self._diff(self.CachedList, self.OldCachedList, ["state"], ["prior"])
        completedjobs = self._getCompleted()
        return difftbl, completedjobs
    
    def statusList(self):
        jobsByDBID = self._getJobsByDBID(self.CachedList)
        pending = {}
        for dbid, jobids in sorted(jobsByDBID.iteritems()):
            pending[dbid] = {}
            for jobid in jobids:
                cachedstatus = self.CachedList.get(jobid)
                if type(cachedstatus) == type(pending):
                    pending[dbid][jobid] = {}
                    for task, details in cachedstatus.iteritems():
                        status = qstatus.get(details["state"])
                        status = status or details["state"] # "%s (unhandled)" %
                        pending[dbid][jobid][task] = status
        return pending
    
    def summary(self):
        slist = self.statusList()
        summary = []
        for dbid, jobs in sorted(slist.iteritems()):
            numjobs = 0
            numtasks = 0
            for jobid, tasks in sorted(jobs.iteritems()):
                numjobs += 1
                numtasks += len(tasks)
            summary.append((dbid, numjobs, numtasks))
        return summary

    def _getJobsByDBID(self, jobtable):
        # group jobs by DB ID
        jobsByDBID = {}
        for jobid, tasks in sorted(jobtable.iteritems()):
            dbid = self.mapClusterToDB.get(jobid) or 0
            jobsByDBID[dbid] = jobsByDBID.get(dbid) or []
            jobsByDBID[dbid].append(jobid)
        return jobsByDBID

    def _getCompleted(self):
        # specific function - depends on structure of CachedList
        difftbl = {}
        for jobid, tasklist in self.OldCachedList.iteritems():
            if not self.CachedList.get(jobid):
                dbid = self.mapClusterToDB.get(jobid) or 0
                difftbl[dbid] = difftbl.get(dbid) or {} 
                difftbl[dbid][jobid] = tasklist
            else:
                if type(tasklist) == type(difftbl):
                    clvalue = self.CachedList[jobid]
                    if type(clvalue) == type(difftbl):
                        for taskid, taskdetails in tasklist.iteritems():
                            if not clvalue.get(taskid):
                                 dbid = self.mapClusterToDB.get(jobid) or 0
                                 difftbl[dbid] = difftbl.get(dbid) or {} 
                                 difftbl[dbid][jobid] = difftbl[dbid].get(jobid) or {}
                                 difftbl[dbid][jobid][taskid] = taskdetails
        return difftbl                
                     
    def _diff(self, t1, t2, retain = [], ignore = []):
         # generic function
         difftbl = {}
         retained = {}
         
         for key, value in t1.iteritems():
             if not key in ignore:
                 if not t2.get(key):
                     difftbl[key] = value
                 else:
                     v1 = t1[key]
                     v2 = t2[key]
                     if type(v1) == type(v2):
                         if type(v1) == type(difftbl):
                             subdiff = self._diff(t1[key], t2[key], retain, ignore)
                             if subdiff:
                                 difftbl[key] = subdiff
                         elif v1 != v2:
                             # We assume simple types here which can be distinguished by equality
                             difftbl[key] = v1
                         elif key in retain:
                             # Always return this field but only if another non-ignored field differs
                             # Remember it here so we can append it below on diff
                             retained[key] = v1                         
                     else:
                        difftbl[key] = v1
         
         if difftbl:
             for k,v in retained.iteritems():
                 difftbl[k] = v  
         return difftbl 
     
     
     

class SGEPlainPrinter(object):
    def __init__(self, sgeconnection):
        self.sgec = sgeconnection
        
    def statusList(self):
        return self.sgec.statusList()
    
    def summary(self):
        summary = []
        summarylist = self.sgec.summary()
        for item in summarylist:
            summary.append("DBJob #%d: %d jobs, %d tasks" % (item[0], item[1], item[2]))
        return join(summary, "\n")
        
    def qdiff(self): 
        updatedjobs, completedjobs = self.sgec.qdiff()
        if not updatedjobs and not completedjobs:
            return None
        
        s = []
        if updatedjobs:
            uj = ["Updates:"]
            jobsByDBID = self.sgec._getJobsByDBID(updatedjobs)
            for dbid, jobids in sorted(jobsByDBID.iteritems()):
                uj.append("  #%d: " % dbid)
                js = []
                for jobid in jobids:
                    tasks = updatedjobs[jobid]
                    for taskid, details in tasks.iteritems():
                        status = qstatus.get(details["state"])
                        status = status or ("(%s)" % details["state"]) 
                        js.append('%d-%d => %s' % (jobid, taskid, status))
                uj.append("    %s" % join(js, ", "))
            s.append("%s\n" % join(uj, "\n"))
        
        if completedjobs:
            cj = ["Completed:"]
            for dbid, jobs in completedjobs.iteritems():
                cj.append("  #%d: " % dbid)
                for jobid, tasks in jobs.iteritems():
                    js = []
                    if type(tasks) == type({}):
                        for taskid in tasks.keys():
                            js.append('%d' % taskid)
                    cj.append('    job #%d: %s' % (jobid, join(js, ", ")))
            s.append("%s" % join(cj, "\n"))
        
        return join(s, "")    


class SGEXMLPrinter(SGEPlainPrinter):
    
    def __init__(self, sgeconnection):
        super(SGEXMLPrinter, self).__init__(sgeconnection)
        
    def statusList(self):
        slist = self.sgec.statusList()
        if slist:
            slxml = []
            for dbid, jobs in sorted(slist.iteritems()):
                slxml.append('<dbjob id="%d">' % dbid)
                s = {}
                for jobid, tasks in sorted(jobs.iteritems()):
                    for taskid, ts in tasks.iteritems():
                        s[ts] = s.get(ts) or []
                        if str(taskid) != "0":
                            s[ts].append("%d-%s" % (jobid, str(taskid)))
                        else:
                            s[ts].append("%d" % jobid)
                
                for abb, status in qstatus.iteritems():
                    if s.get(status):
                        slxml.append('<%s tasks="%s"/>' % (status, join(s[status], " ")))
                        del s[status]
                for other in s.keys():
                    slxml.append('<unhandled_%s tasks="%s"/>' % (other, join(s[other], " ")))
                slxml.append('</dbjob>')
            return '<sge type="status">\n%s\n</sge>' % (join(slxml, "\n")) 
        return None
    
    def summary(self):
        summary = []
        summarylist = self.sgec.summary()
        if summarylist:
            for item in summarylist:
                summary.append('<dbjob id="%d" numjobs="%d" numtasks="%d"/>' % (item[0], item[1], item[2]))
            return '<sge type="summary">\n%s\n</sge>' % join(summary, "\n")
        return None

    def qdiff(self): 
        updatedjobs, completedjobs = self.sgec.qdiff()
        if not updatedjobs and not completedjobs:
            return None
        
        s = ['<sge type="diff">\n']
        if updatedjobs:
            s.append("<updated>")
            
            jobsByDBID = self.sgec._getJobsByDBID(updatedjobs)
            
            #jobsByDB = {}
            # group jobs by DB ID
            #for jobid, tasks in sorted(updatedjobs.iteritems()):
            #    dbid = self.mapClusterToDB.get(jobid) or 0
            #    jobsByDB[dbid] = jobsByDB.get(dbid) or []
            #    jobsByDB[dbid].append(jobid)
            
            for dbid, jobids in sorted(jobsByDBID.iteritems()):
                s.append('\n<dbjob id="%d">' % dbid)
                for jobid in jobids:
                    s.append('\n<job id="%d">' % jobid)
                    tasks = updatedjobs[jobid]
                    for taskid, details in tasks.iteritems():
                        status = qstatus.get(details["state"])
                        status = status or ("(%s)" % details["state"]) #("%s (unhandled)" % details["state"])
                        if str(taskid) != "0":
                            s.append('<task id="%s" status="%s"/>' % (taskid, status))
                        else:
                            s.append('<task status="%s"/>' % status)
                        
                    s.append('</job>')
                s.append('\n</dbjob>')
            
            s.append("</updated>\n")
            
        if completedjobs:
            s.append("<completed>")
            for dbid, jobs in completedjobs.iteritems():
                s.append('\n<dbjob id="%d">' % dbid)
                for jobid, tasks in jobs.iteritems():
                    s.append('\n<job id="%d">' % jobid)
                    if type(tasks) == type({}):
                        for taskid in tasks.keys():
                            if str(taskid) != "0":
                                s.append('<task id="%s"/>' % taskid)
                    s.append('</job>')
                s.append('\n</dbjob>')
            s.append("</completed>\n")
        s.append("</sge>\n")
        return join(s, "")
    
    
if __name__ == "__main__":
    sgec = SGEConnection()
    
    sgec.mapClusterToDB = {1234 : 1906, 
                           1237 : 1906, 
                           1235 : 1907, 
                           1239 : 1907}
    
    t1 = {1234 : { #1906
                1 : {"state" : "w"},
                2 : {"state" : "q"},
                3 : {"state" : "qw"},
                4 : {"state" : "r"}
                },
          1237 : { #1906
                1 : {"state" : "r"},
          },
          1239 : { #1907
                3 : {"state" : "qw"},
          }}
    t2 = {1234 : { #1906
                    1 : {"state" : "q"},
                    2 : {"state" : "q"},
                    },
          1235 : { #1907
                    1 : {"state" : "r"},
                    2 : {"state" : "q"},
                    }}
    
    t1 = {6133908: 
          {0: 
            {'name': 'backrub_18', 'jobid': 6133908, 'queue': 'lab.q@ih69', 'prior': '0.05071', 'state': 'r', 'user': 'klabqb3backr', 'slots': '1', 'submit/start at': '05/13/2011 13:39:28'}
          }
         }
    t2 = {6133908: 
          {0: 
            {'name': 'backrub_18', 'jobid': 6133908, 'queue': 'lab.q@ih69', 'prior': '0.05293', 'state': 'r', 'user': 'klabqb3backr', 'slots': '1', 'submit/start at': '05/13/2011 13:39:28'}
          }
         }

    sgec.CachedList = t1
    sgec.OldCachedList = t2
    
    plainprinter = SGEPlainPrinter(sgec)
    xmlprinter = SGEXMLPrinter(sgec)
    
    print("\n - qdiff - \n")
    print(plainprinter.qdiff())
    print("\n - qdiffXML - \n")
    print(xmlprinter.qdiff())
    print("\n - statusList - \n")
    print(plainprinter.statusList())
    print("\n - statusListXML - \n")
    print(xmlprinter.statusList())
    print("\n - summary - \n")
    print(plainprinter.summary())
    print("\n - summary - \n")
    print(xmlprinter.summary())
    
    print("\nSWITCH\n")
    
    sgec.CachedList = t2
    sgec.OldCachedList = t1
    print("\n - qdiff - \n")
    print(plainprinter.qdiff())
    print("\n - qdiffXML - \n")
    print(xmlprinter.qdiff())
    print("\n - statusList - \n")
    print(plainprinter.statusList())
    print("\n - statusListXML - \n")
    print(xmlprinter.statusList())
    print("\n - summary - \n")
    print(plainprinter.summary())
    print("\n - summary - \n")
    print(xmlprinter.summary())
    #thisjob, jobs = connection.qstat(1)
    #print(thisjob)