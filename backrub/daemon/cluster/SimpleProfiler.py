import time

class ProfilerException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

class SimpleProfiler(object):
    def __init__(self):
        self.timers = {}

    def PROFILE_START(self, name):
        if self.timers.get(name):
            raise ProfilerException("A timer for task %s was already created.")
        self.timers[name] = (time.clock(), False)
        
    def PROFILE_STOP(self, name):
        starttime = self.timers.get(name):
        if not starttime:
            raise ProfilerException("The timer was task %s was attempted to be stopped before it was created.")
        self.timers[name] = (time.clock() - starttime[0], True)
    
    def PROFILE_STATS(self):
        results = {}
        for subtask, timer in self.timers.items():
            if timer[1] != True:
                raise ProfilerException("The timer for task %s was never stopped." % subtask)
            results[subtask] = timer[0]
        return results
    
