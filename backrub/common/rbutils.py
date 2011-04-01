import sys, os
import re

#############################################################################################
# read_config_file()                                                                        #
# parser for configuration file                                                             #
#############################################################################################
def read_config_file(): 
    try:
        handle = open('/etc/rosettaweb/parameter.conf', 'r')
        lines  = handle.readlines()
        handle.close()
        parameter = {}
        for line in lines:
            if line[0] != '#' and len(line) > 1  : # skip comments and empty lines
                # format is: "parameter = value"
                list_data = line.split()
                parameter[list_data[0]] = list_data[2]
    except IOError:
        print filename_config, "could not be found."
        sys.exit(2)
        
    return parameter


