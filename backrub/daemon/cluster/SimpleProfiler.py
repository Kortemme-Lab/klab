#!/usr/bin/python2.4
# encoding: utf-8
"""
SimpleProfiler.py

Created by Shane O'Connor 2011.
Copyright (c) 2011 __UCSF__. All rights reserved.
"""


import time
from string import join

class ProfilerException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

class SimpleProfiler(object):
    maintaskname = "__main"
    
    def __init__(self, name):
        self.name = name
        self.timers = {}
        self.order_of_timers = []

    def PROFILE_START(self, task):
        if self.timers.get(task):
            raise ProfilerException("A timer for task %s was already created.")
        self.timers[task] = (time.time(), False)
        self.order_of_timers.append(task)
        
    def PROFILE_STOP(self, task):
        starttime = self.timers.get(task)
        if not starttime:
            raise ProfilerException("The timer was task %s was attempted to be stopped before it was created." % task)
        self.timers[task] = (time.time() - starttime[0], True)
    
    def PROFILE_STATS(self):
        results = []
        for task in self.order_of_timers:
            timer = self.timers[task]
            if timer[1] != True:
                task = "The timer for task %s was never stopped." % task # raise ProfilerException("The timer for task %s was never stopped." % subtask)
                results.append((task, time.time() - timer[0]))
            results.append((task, timer[0]))
        return results
            
        #todo delete
        for task, timer in self.timers.items():
            if timer[1] != True:
                results[task] = "The timer for task %s was never stopped." % task # raise ProfilerException("The timer for task %s was never stopped." % subtask)
            results[task] = timer[0]
        return results

indentationsize = 4

def sumTuples(listoftuples):
    total = 0.0
    for i in range(len(listoftuples)):
        tl = listoftuples[i]
        if type(tl[1]) == type(listoftuples):
            sumt = sumTuples(tl[1])
            listoftuples[i] = ('%s inclusive_time="%f"'% (tl[0], sumt), tl[1])
            total = total + sumt
        else:
            total = total + tl[1]
    return total
    
def listsOfTuplesToXML(listoftuples, level = 0):
    s = []
    indentation = " " * level * indentationsize or " " * (indentationsize / 2)
    for tpl in listoftuples:
        s.append("%s<%s>" % (indentation, tpl[0]))
        if type(tpl[1]) != type(s):
            s.append("%s%s" % (indentation + (" " * indentationsize), str(tpl[1])))
        else:
            s.extend(listsOfTuplesToXML(tpl[1], level + 1))
        s.append("%s</%s>" % (indentation, tpl[0].split(" ", 1)[0]))    
    if level > 0:
        return s
    else:
        return join(s, "\n")

# Test code for sumTuples and listsOfTuplesToXML
if False:
    testtuples = [('seqtol',
                    [('init', 4.0),
                    ('scheduler', 
                        [('minimization', 
                            [('init', 1.2),
                            ('processing', 100.6),
                            ('analysis', 5.9)]
                        ),
                        ('backrub', 
                            [('init', 0.6),
                            ('processing', 182.8),
                            ('analysis', 0.7)]
                        ),
                        ('sequence_tolerance', 
                            [('init', 0.8),
                            ('processing', 312.5),
                            ('analysis', 11.2)]
                        )]),
                    ('final', 4.0)])]