#!/usr/bin/python

import Queue, os.path, gf, time, math

NUM_PROCS = 11
#MACHINE_REQUIREMENTS = "&& Machine != \"riesling.ucsf.edu\" && Machine != \"cabernet.ucsf.edu\" && Machine != \"delaware.ucsf.edu\" " 
MACHINE_REQUIREMENTS = "&& Machine != \"pinot.ucsf.edu\""# && Machine != \"malbec.ucsf.edu\" "
#MACHINE_REQUIREMENTS = "&& Machine == \"airen.ucsf.edu\""
#MACHINE_REQUIREMENTS = ""


def debug(fn, str):
    gf.appendfile(fn, str)

# Class to process jobs using a cluster (a condor cluster by default)
class Pool:
    # mem_required is in megabytes
    def __init__(self, name, size=1, debug_on=False, cluster="condor", mem_required=None):
        self.name = name
        self.size = size
        self.Qin = []
        self.running = []
        self.count = 1
        self.outputs = {}
        self.cluster=cluster
        if debug_on:
            self.debug_file = name + ".debuglog"
            debug(self.debug_file,  "\n====>[Pool] Created '%s'\n" % (self))
        else: self.debug_file = None

        self.requirements = MACHINE_REQUIREMENTS
        if mem_required != None:
            self.requirements += " && Memory >= %d" % mem_required
    def __del__(self):
        if self.debug_file: debug(self.debug_file,  "[Pool] Destroyed '%s'\n" % (self))
    def __str__(self):
        return "%s (%d)" % (self.name, self.size)

    # submit the job to the queue
    # returns the job id for later retrieval in the output dictionary
    def queue(self, cmd):
        id = "%s_%d" % (self.name, self.count)
        self.count += 1
        cwd = gf.zin_abspath(os.getcwd())
        j = Job(id, cmd, cwd, self.debug_file)
        self.Qin.append(j)
        return id

    # private
    def start_next_job(self):
        j = self.Qin[-1]
        self.Qin.remove(j)
        j.start()
        self.running.append(j)

        if self.debug_file: debug(self.debug_file,  "[Pool] Started job '%s'\n" % (j))

    # private
    def cleanup_finished_jobs(self):
        for j in self.running:
            #if self.debug_file: debug(self.debug_file, "[Pool] Checking '%s' status" % (j))
            if j.is_done():
                output = j.get_output()
                self.running.remove(j)
                self.outputs[j.id] = output

                if self.debug_file: debug(self.debug_file,  "[Pool] Finished job '%s':  '%s'\n" % (j, output.strip()))

    # remove jobs from the internal representation of the queue
    def clear(self):
        for j in self.running:
            if self.debug_file: debug(self.debug_file,  "[Pool] Clearing running job '%s'\n" % (j))
            self.running.remove(j)
        for j in self.Qin:
            if self.debug_file: debug(self.debug_file,  "[Pool] Clearing queued job '%s'" % (j))
            self.Qin.remove(j)

    # wait for jobs in the queue to finish
    def run(self, jobs_per_batch=None):
        if self.cluster:
            if jobs_per_batch != None:
                self.cluster_run(jobs_per_batch=jobs_per_batch, condor=(self.cluster=="condor"))
            else:
                self.cluster_run()
        else:
            self.run_local()
            
    # runs until all jobs are completed and returns a dictionary of job id, output
    def run_local(self):
        # add jobs stage
        while len(self.Qin) > 0:
            # add jobs
            while len(self.Qin) > 0 and len(self.running) < self.size:
                self.start_next_job()

            # remove finished jobs
            self.cleanup_finished_jobs()            
            time.sleep(1)

        if self.debug_file: debug(self.debug_file,  "[Pool] Done queing jobs\n")
            
        # cleanup jobs stage
        while len(self.running) > 0:
            self.cleanup_finished_jobs()            
            time.sleep(1)

        if self.debug_file: debug(self.debug_file,  "[Pool] run() returned\n")            
        return self.outputs

    def _cluster_submit_1batch(self, batch_no, job_list):
        # write the batch shell script
        sh_fn = "batch%03d.sh" % (batch_no)
        batch_job = Job("batch%03d" % batch_no, sh_fn, self.debug_file)
        batch_job.running_file = gf.zin_abspath(batch_job.running_file)
        batch_job.done_file = gf.zin_abspath(batch_job.done_file)

        batch_txt = "#!/bin/bash\n" + \
                    "#ulimit -c 5000\n" + \
                    "export PATH=/usr/local/bin:/bin:/usr/bin; export MALLOC_CHECK_=0\n" + \
                    "date; hostname; printenv; echo;\n" + \
                    "echo running > %s\n\n" % batch_job.running_file + \
                    "\n".join(["cd %s; %s" % (j.path,j.cmd) for j in job_list]) + "\n\n" + \
                    "mv %s %s\n" % (batch_job.running_file, batch_job.done_file) 
        gf.writefile(sh_fn, batch_txt)
        gf.run("chmod +x " + sh_fn)

        # write the condor cmd file
        batch_dir = os.getcwd()
        cmd_fn = "batch%03d.cmd" % batch_no
        gf.writefile(cmd_fn,"""\n
                      executable      = %s/%s
                      output          = %s/env%03d.out
                      error           = %s/env%03d.err
                      log	      = %s/env%03d.log
                      IWD             = %s
                      Requirements    = LoadAvg < 1.0 && UidDomain == \"ucsf.edu\" && FileSystemDomain == \"ucsf.edu\" && (Arch == \"x86_64\" || Arch == \"INTEL\") %s
                      universe        = vanilla
                      queue\n""" % \
                     (batch_dir, sh_fn, batch_dir, batch_no, batch_dir, batch_no, batch_dir, batch_no, batch_dir, self.requirements))
        gf.run("condor_submit " + cmd_fn)
        batch_job.status = "running"
        return batch_job

    def cluster_run(self, jobs_per_batch=None, condor=True):
        if jobs_per_batch == None:
            if len(self.Qin) <= 40:
                jobs_per_batch = 1
            else:
                jobs_per_batch = math.ceil(len(self.Qin)/2./NUM_PROCS)
            
        if self.debug_file: debug(self.debug_file,  "[Pool] Cluster mode with size %d\n" % jobs_per_batch)

        # submit jobs to the queue
        job_list, batch_no = [], 1
        while len(self.Qin) > 0:
            # create job_list
            for i in range(int(jobs_per_batch)):
                if len(self.Qin) == 0: break
                j = self.Qin[-1]
                self.Qin.remove(j)
                job_list.append(j)

            if not condor:
                batch_job = self._qb3_cluster_submit_1batch(batch_no, job_list)
            else:
                batch_job = self._cluster_submit_1batch(batch_no, job_list)
            
            if self.debug_file: debug(self.debug_file,  "[Pool] Submitted batch: %s\n" % batch_job.cmd)
            batch_no += 1
            job_list = []
            self.running.append(batch_job)
        if self.debug_file: debug(self.debug_file,  "[Pool] Done queing jobs\n")
            
        # cleanup jobs stage
        while len(self.running) > 0:
            self.cleanup_finished_jobs()            
            time.sleep(1)

        if self.debug_file: debug(self.debug_file,  "[Pool] cluster_run() returned\n")            
        return self.outputs

    def _qb3_cluster_submit_1batch(self, batch_no, job_list):
        cwd = os.getcwd()+"/"
        sh_fn = cwd+"batch%03d.sh" % (batch_no)
        batch_job = Job("batch%03d" % batch_no, sh_fn, self.debug_file)

        script = """#!/bin/sh                          #-- what is the language of this shell
#$ -S /bin/sh                      #-- the shell for the job
#$ -o %s                        #-- output directory (fill in)
#$ -e %s                        #-- error directory (fill in)
#$ -cwd                            #-- tell the job that it should start in your working directory
#$ -r y                            #-- tell the system that if a job crashes, it should be restarted
#$ -j y                            #-- tell the system that the STDERR and STDOUT should be joined
##$ -l ibm32=true                   #-- SGE resources (CPU type)
#$ -l panqb3=1G,scratch=1G         #-- SGE resources (home and scratch disks)
##$ -l h_rt=24:00:00                #-- runtime limit (see above; this requests 24 hours)

date
hostname

echo running > %s
%s
mv %s %s\n
""" % (cwd, cwd, batch_job.running_file,
       "\n".join([j.cmd for j in job_list]) + "\n",
       batch_job.running_file, batch_job.done_file)

        gf.writefile(sh_fn, script)
        gf.run("qsub " + sh_fn)
        os.sleep(3)
        batch_job.status = "running"
        return batch_job

class Job:
    def __init__(self, id, cmd, path, debug_file=None):
        self.id = id
        self.cmd = cmd
        self.path = path
        self.debug_file = debug_file
        self.running_file = "%s.running" % (id)
        self.done_file = "%s.done" % (id)
        self.status = "inited" # "inited" | "running" | "done"
        self.output = None

        # make sure the directory is clean
        os.system("rm -f %s %s" % (self.running_file, self.done_file))

    def start(self):
        self.status = "running"
        full_cmd = "/var/www/html/rosettaweb/backrub/bin/start_limited.sh ((%s) > %s; mv %s %s) &" % (self.cmd, self.running_file, self.running_file, self.done_file)

        #if self.debug_file:
        #    print "[Job] started '%s'" % (self)
        os.system(full_cmd)

    # check if the job is done
    def is_done(self):
        #if self.debug_file:
        #    print "[Job]: retrieved job status for '%s' = '%s'" % (self, self.status)

        if self.status == "inited":
            return False
        elif self.status == "running":
            if not os.path.exists(self.done_file):
                return False
            else:
                #if self.debug_file:  debug(self.debug_file, "[Job]: removing '%s'\n" % (self.done_file))

                self.status = "done"
                self.output = gf.readfile(self.done_file)
                os.remove(self.done_file)
                return True
        elif self.status == "done":
            return True
        else:
            gf.fatal("Invalid job status '%s'" % (self.status))

    # contains the output after is_done() returns true
    def get_output(self):
        return self.output

    def __str__(self):
        return "%s ('%s')" % (self.id, self.cmd)
    def __repr__(self):
        return str(self)
    


        
# run cluster commands
if __name__ == "__main__":
    import sys

    cmd_template = sys.argv[1] # eg. 'ls @@@ > @@@.out' where @@@ is replaced by each arg in turn
    args = sys.argv[2:]

    p = Pool("batchpool", 5, True)
    for arg in args:
        cmd = cmd_template.replace("@@@", arg)
        print cmd
        p.queue(cmd)
    p.cluster_run(1)


#    for i in range(15):
#        p.queue("sleep 3; echo -n output-%d" % (i))
#    outputs = p.cluster_run()

#    print "DONE"
#    print
#    print outputs


