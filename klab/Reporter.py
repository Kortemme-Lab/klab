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
        self.maximum_output_string_length = 0
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
                time_remaining_str = 'Est. time remaining: '

                weeks_remaining = math.floor(time_remaining / 604800.0)
                if weeks_remaining > 0:
                    time_remaining_str += '%d weeks' % weeks_remaining
                time_remaining -= weeks_remaining * 604800.0

                days_remaining = math.floor(time_remaining / 86400.0)
                if days_remaining > 0:
                    if time_remaining_str[-1] != ' ' and time_remaining_str[-1] != ',':
                        time_remaining_str += ', '
                    time_remaining_str += '%d days' % days_remaining
                time_remaining -= days_remaining * 86400.0

                hours_remaining = math.floor(time_remaining / 3600.0)
                if hours_remaining > 0:
                    if time_remaining_str[-1] != ' ' and time_remaining_str[-1] != ',':
                        time_remaining_str += ', '
                    time_remaining_str += '%d hours' % hours_remaining
                time_remaining -= hours_remaining * 3600.0

                minutes_remaining = math.floor(time_remaining / 60.0)
                if minutes_remaining > 0:
                    if time_remaining_str[-1] != ' ' and time_remaining_str[-1] != ',':
                        time_remaining_str += ', '
                    time_remaining_str += '%d minutes' % minutes_remaining
                time_remaining -= minutes_remaining * 60.0
                
                seconds_remaining = int(time_remaining)
                if time_remaining_str[-1] != ' ' and time_remaining_str[-1] != ',':
                    time_remaining_str += ', '
                time_remaining_str += '%d seconds' % seconds_remaining

                output_string = "  Processed: %d %s (%.1f%%) %s\r" % (n, self.entries, percent_done*100.0, time_remaining_str)
            else:
                output_string = "  Processed: %d %s\r" % (n, self.entries)

            if len(output_string) > self.maximum_output_string_length:
                self.maximum_output_string_length = len(output_string)
            elif len(output_string) < self.maximum_output_string_length:
                output_string = output_string.ljust(self.maximum_output_string_length)
            sys.stdout.write( output_string )
            sys.stdout.flush()

    def increment_report(self):
        self.report(self.n + 1)
    def increment_report_callback(self, cb_value):
        self.increment_report()
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
