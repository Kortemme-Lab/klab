#!/usr/bin/env python2

# I moved this class from misc.py so it can be used without required numpy, 
# scipy, and pandas. -KBK

class FrequencyCounter(object):

    def __init__(self):
        self.items = {}

    def add(self, item):
        self.items[item] = self.items.get(item, 0)
        self.items[item] += 1


