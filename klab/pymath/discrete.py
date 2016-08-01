#!/usr/bin/python
# encoding: utf-8
"""
A module for discrete mathematics. Not that this is something we should do in Python.

Created by Shane O'Connor 2016
"""

import fractions


dumb_relative_prime_const = {
    6 : 5,
    5 : 2,
    4 : 3,
    3 : 2,
    2 : 1, # yep, I know
    1 : 0, # yadda yadda
}


def dumb_relative_half_prime(n, divisor = None):
    '''A dumb brute-force algorithm to find a relative prime for n which is approximately n/2 through n/5.
       It is used for generating spaced colors.
       Written on a Friday evening. Do not judge!
    '''
    if n < 1 or not isinstance(n, int):
        raise Exception('n must be a positive non-zero integer.')
    elif n < 7:
        return dumb_relative_prime_const[n]
    elif n < 10:
        divisor = 2.0
    if not divisor:
        if n <= 20:
            divisor = 3.0
        elif n <= 30:
            divisor = 4.0
        else:
            divisor = 5.0
    m = int(n / divisor)
    while m > 1:
        if fractions.gcd(n, m) == 1:
            return m
        m -= 1
    if divisor > 2.0:
        return dumb_relative_half_prime(n, divisor - 1.0) # e.g. 12