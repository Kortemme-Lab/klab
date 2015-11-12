import time
import math
import sys

class Reporter:
    def __init__(self, task, entries='files', print_output=True):
        self.print_output = print_output
        self.start = time.time()
        self.entries = entries
        self.lastreport = self.start
        self.task = task
        self.report_interval = 1 # Interval to print progress (seconds)
        self.n = 0
        self.completion_time = None
        if self.print_output:
            print '\nStarting ' + task
        self.total_count = None # Total tasks to be processed
    def set_total_count(self, x):
        self.total_count = x
    def decrement_total_count(self):
        self.total_count -= 1
    def report(self, n):
        self.n = n
        t = time.time()
        if self.print_output and self.lastreport < (t-self.report_interval):
            self.lastreport = t
            if self.total_count:
                percent_done = float(self.n) / float(self.total_count)
                time_now = time.time()
                est_total_time = (time_now - self.start) * (1.0 / percent_done)
                time_remaining = est_total_time - (time_now - self.start)
                minutes_remaining = math.floor(time_remaining / 60.0)
                seconds_remaining = int(time_remaining - (60*minutes_remaining))
                sys.stdout.write("  Processed: %d %s (%.1f%%) %02d:%02d\r" % (n, self.entries, percent_done*100.0, minutes_remaining, seconds_remaining) )
            else:
                sys.stdout.write("  Processed: %d %s\r" % (n, self.entries) )
            sys.stdout.flush()

    def increment_report(self):
        self.report(self.n + 1)
    def decrement_report(self):
        self.report(self.n - 1)
    def add_to_report(self, x):
        self.report(self.n + x)
    def done(self):
        self.completion_time = time.time()
        if self.print_output:
            print 'Done %s, processed %d %s, took %.3f seconds\n' % (self.task, self.n, self.entries, self.completion_time-self.start)
    def elapsed_time(self):
        if self.completion_time:
            return self.completion_time - self.start
        else:
            return time.time() - self.start
