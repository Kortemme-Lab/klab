import multiprocessing as mp
from Reporter import Reporter
import time
import Queue

class MultiWorker:
    def __init__(self, func, n_cpu = None, reporter=None, task='multiprocessing', entries='jobs', cb_func=None):
        if not reporter:
            self.reporter = Reporter(task, entries=entries)
        else:
            self.reporter = reporter
        self.func = func
        if n_cpu:
            self.pool = mp.Pool(n_cpu)
        else:
            self.pool = mp.Pool()
        self.cb_func = cb_func
        if self.cb_func:
            self.queue = mp.Queue()
            self.reader_p = mp.Process(target=self.reader_helper)
            self.reader_p.daemon = True
            self.reader_p.start() 
        else:
            self.data = []
    def reader_helper(self):
        while True:
            print 'size', self.queue.qsize()
            while not self.queue.empty():
                msg = self.queue.get()
                if (msg == '_QUEUEDONE'):
                    break
                else:
                    args = msg[0]
                    kwargs = msg[1]
                    self.cb_func(*args, **kwargs)
            time.sleep(2)
    def list_cb(self, results):
        self.reporter.increment_report()
        self.data.append(results)
    def queue_cb(self, results):
        print 'put', results
        self.queue.put(results)
        self.reporter.increment_report()
    def addJob(self, argsTuple):
        if self.cb_func:
            self.pool.apply_async(self.func, argsTuple, callback=self.queue_cb)
        else:
            self.pool.apply_async(self.func, argsTuple, callback=self.list_cb)
    def finishJobs(self):
        self.pool.close()
        self.pool.join()
        if self.cb_func:
            self.queue.put('_QUEUEDONE')
            print 'Pool finished, waiting to process results'
            self.reader_p.join()
        self.reporter.done()
