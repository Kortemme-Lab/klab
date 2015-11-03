#!/usr/bin/python
# encoding: utf-8
"""
stats.py
For profiling functions
"""

import time
from klab import colortext

class ProfileTimer(object):
    '''A dumb profiler. Cheap and cheerful.'''

    def __init__(self):
        self.stages = []
        self.stage_times = {}
        self.current_stage = None
        self.last_start_time = None
        self.stopped = True

    def start(self, stage):
        time_now = time.time()
        self.stopped = False

        if stage not in self.stage_times.keys():
            self.stages.append(stage)

        if self.current_stage:
            self.stage_times[self.current_stage] = self.stage_times.get(self.current_stage, 0)
            self.stage_times[self.current_stage] += time_now - self.last_start_time
            self.last_start_time = time_now
            self.current_stage = stage
        else:
            self.current_stage = stage
            self.last_start_time = time_now
            self.stage_times[stage] = 0

    def stop(self):
        time_now = time.time()
        if self.current_stage:
            self.stage_times[self.current_stage] = self.stage_times.get(self.current_stage, 0)
            self.stage_times[self.current_stage] += time_now - self.last_start_time
            self.last_start_time = None
            self.current_stage = None
        self.stopped = True

    def getTotalTime(self):
        if not self.stopped:
            return None
        t = 0
        for stage in self.stages:
            t += self.stage_times[stage]
        return t

    def _getProfileForTerminal(self):
        if not self.stopped:
            return False

        s = [colortext.make('Total time: %fs' % self.getTotalTime(), color = 'white', effect = colortext.BOLD)]

        stage_times = sorted([self.stage_times[stage] for stage in self.stages])
        if len(stage_times) < 10:
            top_time_cutoff = stage_times[-2]
        else:
            top_time_cutoff = stage_times[-(len(stage_times) / 5)]

        for stage in self.stages:
            if self.stage_times[stage] == stage_times[-1]:
                s.append(colortext.make("  %s: %fs" % (stage, self.stage_times[stage]), 'pink'))
            elif self.stage_times[stage] >= top_time_cutoff:
                s.append(colortext.make("  %s: %fs" % (stage, self.stage_times[stage]), 'red'))
            else:
                s.append(colortext.make("  %s: %fs" % (stage, self.stage_times[stage]), 'silver'))
        return "\n".join(s)

    def _getProfileForWeb(self):
        if not self.stopped:
            return False
        s = ['<b>Total time: %fs</b>' % self.getTotalTime()]

        stage_times = sorted([self.stage_times[stage] for stage in self.stages])
        if len(stage_times) < 10:
            top_time_cutoff = stage_times[-2]
        else:
            top_time_cutoff = stage_times[-(len(stage_times) / 5)]

        for stage in self.stages:
            if self.stage_times[stage] == stage_times[-1]:
                s.append("<b><font color='#550000'>%s: %fs</font></b>" % (stage, self.stage_times[stage]))
            elif self.stage_times[stage] >= top_time_cutoff:
                s.append("<b><font color='red'>%s: %fs</font></b>" % (stage, self.stage_times[stage]))
            else:
                s.append("%s: %fs" % (stage, self.stage_times[stage]))
        return "<br>".join(s)

    def getProfile(self, html = True):
        if html:
            return self._getProfileForWeb()
        else:
            return self._getProfileForTerminal()
