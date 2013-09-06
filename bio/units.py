#!/usr/bin/python
# encoding: utf-8
"""
units.py
Basic units and conversions for bioinformatics.

Created by Shane O'Connor 2013
"""

NUMBER_KJ_IN_KCAL = 4.184 # Thermochemical calorie
NUMBER_KELVIN_AT_ZERO_CELSIUS = 273.15

def kcal_to_kJ(x):
    return x * NUMBER_KJ_IN_KCAL

def kJ_to_kcal(x):
    return x / NUMBER_KJ_IN_KCAL