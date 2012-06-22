import os
import time
import subprocess
import shutil
import shlex
import string

if os.path.exists("copytemp1"):
	shutil.rmtree("copytemp1")
if os.path.exists("copytemp2"):
	shutil.rmtree("copytemp2")

os.mkdir("copytemp1")
os.mkdir("copytemp2")

listoffiles = []
t1 = time.time()
resultsdir = "/backrub/benchmarks/KIC/temp/tmpcTqWbA_bmarkKIC/3cla/"
prefix = "KICBenchmark_18.cmd.o7569925"

listfile = open(os.path.join("copytemp1", "filelist.txt"), "w")
for f in sorted(os.listdir(resultsdir)):
	if f.startswith(prefix):
		listoffiles.append(os.path.join(resultsdir, f))
		listfile.write("%s\n" % f)
listfile.close()

count = 0
print("*** TESTING shutil.copy ***")
t1 = time.time()
for f in listoffiles:
	shutil.copy(f, "copytemp1")
	count += 1
	if count % 200 == 0:
		print("%d files copied." % count)
timetaken = time.time() - t1
print("\nTime taken: %ds\n" % timetaken)

print("*** TESTING rsync shell call ***\n")
t2 = time.time()
cmdargs = shlex.split("rsync --archive --files-from=copytemp1/filelist.txt %s copytemp2/" % resultsdir)
p = subprocess.Popen(cmdargs)
returncode = p.wait()
print("returncode = %d" % returncode)
timetaken = time.time() - t2
print("\nTime taken: %ds\n" % timetaken)



