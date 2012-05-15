#This file was developed and written by Roland A. Pache, Ph.D., Copyright (C) 2011, 2012.

import os
from subprocess import *


#parser for parameter file
#input: name of the parameter file
#output: map: parameter -> value
def parseParameterFile(param_filename):
    parameters={}
    file=open(param_filename)
    lines=file.read().split('\n')
    file.close()
    for line in lines:
        data=line.split('=')
        if len(data)>1:
            #parameter
            parameter=data[0].lstrip(' ').rstrip(' ')
            #value
            value=data[1].lstrip(' ').rstrip(' ')
            parameters[parameter]=value
    #--
    return parameters


#Quantile
#input: list of values (floats/ints), p in [0,1)
#output: p-Quantile, 'n/a' if not applicable
def quantile(values,p):
    quantile='n/a'
    if values!=[]:
        dummy_values=[]
        for value in values:
            if value!='n/a':
                dummy_values.append(value)
        #--
        dummy_values.sort()
        num_values=len(dummy_values)
        index=int(float(num_values)*p)
        quantile=dummy_values[index]
    #-
    return quantile


#Median
#input: list of values (floats/ints)
#output: median, 'n/a' if not applicable
def median(values):
    median=quantile(values,0.5)
    return median


#executes the given program using the shell, writing output to stdout
#input: command (string)
#output: -
def run(args):
    process=Popen(args,shell=True)
    status=os.waitpid(process.pid, 0)
    return status[1]


#executes the given program using the shell, returning the output
#input: command (string)
#output: string
def run_return(args):
    process=Popen(args,shell=True,stdout=PIPE)
    return process.communicate()[0]


#generates a new file containing the given string
#input: string, filename
#output: -
def newFile(string,filename):
    file=open(filename,"w")
    file.write(string)
    file.close()


#Box-and-Whisker plot with median bars
#input: map x (float/int) -> list of y (float/int)
#output: list of (x,min,1st_quartile,median,3rd_quartile,max) tuples ready for gnuplot
def boxAndWhisker(data):
    tuples=[]
    for x in data:
        y_values=data[x]
        if y_values!=[]:
            minimum=min(y_values)
            maximum=max(y_values)
            median_value=median(y_values)
            first_quartile=quantile(y_values,0.25)
            third_quartile=quantile(y_values,0.75)
            tuples.append([x,minimum,first_quartile,median_value,third_quartile,maximum])
    #--
    return tuples
