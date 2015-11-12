import multiprocessing
from Reporter import Reporter

class MultiWorker:
    def __init__(self, func, n_cpu = None, reporter=None, task='multiprocessing', entries='jobs'):
        if not reporter:
            self.reporter = Reporter(task, entries=entries)
        else:
            self.reporter = reporter
        self.func = func
        if n_cpu:
            self.pool = multiprocessing.Pool(n_cpu)
        else:
            self.pool = multiprocessing.Pool()
        self.data = []
    def cb(self, results):
        self.reporter.increment_report()
        self.data.append(results)
    def addJob(self, argsTuple):
        self.pool.apply_async(self.func, argsTuple, callback=self.cb)
    def finishJobs(self):
        self.pool.close()
        self.pool.join()
        self.reporter.done()
