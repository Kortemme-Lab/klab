#!/usr/bin/python

import os, sys
import re
from subprocess import *

def execute(command):
  return Popen(command.split(), stdout=PIPE).communicate()[0]

output_ps = execute('ps -o user,pid,ppid,command ax')
# print output_ps.split('\n')
expr = re.compile("rosetta_daemon")
line = filter(expr.search,[line.rstrip() for line in output_ps.split('\n')])
# print line

pid = line[0].split()[1]
# print pid

print "------------------------------------------"
output_pstree = execute("pstree -p -n %s" % pid)
print output_pstree
str_pstree = output_pstree.split('\n')
# print str_pstree

print "------------------------------------------"
pids = []
for line in str_pstree:
  for word in line.split(')'):
    # print word, len(word)
    if len( word ) > 2:
      # print word.split('(')
      pids.append( word.split('(')[1] )

print pids


print "------------------------------------------"

output_ps2 = execute('ps -o user,pid,ppid,%mem,%cpu,command ax -H')
# print output_ps2

print output_ps2.split('\n')[0]

lines = []
for pid in pids:
  expr = re.compile(pid)
  for line in filter(expr.search,[line.rstrip() for line in output_ps2.split('\n')]):
    if line not in lines:
      lines.append(line)


for line in lines:
  if len(sys.argv) > 1: 
    if sys.argv[1] == "short":
      print line[0:130]
  else:
    print line

sys.exit(0)

