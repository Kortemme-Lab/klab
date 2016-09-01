import sys
import os
import inspect
import subprocess
import time
import tempfile
import getpass
import shutil

from klab.fs.fsio import read_file, write_temp_file

class RInterface(object):

    @staticmethod
    def _runRScript(r_script_filename, cwd = '.', remove_output = True):
        # Reset to new current working directory
        tmp_dir = False
        if cwd == None:
            tmp_dir = True
            cwd = tempfile.mkdtemp( prefix = '%s-%s-%s_' % (time.strftime("%y%m%d"), getpass.getuser(), 'plot-working-dir') )

        rscriptname = write_temp_file(cwd, r_script_filename)
        p = subprocess.Popen(["R", "CMD", "BATCH", rscriptname], cwd = cwd)
        while True:
            time.sleep(0.3)
            errcode = p.poll()
            if errcode != None:
                break
        rout = "%s.Rout" % rscriptname
        os.remove(rscriptname)

        rout_contents = None
        if os.path.exists(rout):
            rout_contents = read_file(rout)
            os.remove(rout)

        if errcode != 0:
            print(rout_contents )
            raise Exception("The R script failed with error code %d." % errcode)

        if tmp_dir and remove_output:
            shutil.rmtree(cwd)

        return rout_contents


    @staticmethod
    def correlation_coefficient_gplot(inputfname, output_filename, filetype, experiment_field = "Experimental", title = ''):
        '''File suffix: pearsons_r_gplot
           Description: Pearson's r
           Filename: ggplot_pearsons.R
           Priority: 1
           '''
        script_path = os.path.abspath(os.path.dirname(inspect.getsourcefile(sys.modules[__name__])))
        r_script_filename = read_file(os.path.join(script_path, "ggplot_pearsons.R")) % vars()
        return RInterface._runRScript(r_script_filename)


def run_r_script(r_script_filename, cwd = '.'):
    '''This function was adapted from the covariation benchmark.'''
    p = subprocess.Popen(["R", "CMD", "BATCH", r_script_filename], cwd = cwd)
    while True:
        time.sleep(0.3)
        errcode = p.poll()
        if errcode != None:
            break
    rout = "{0}out".format(r_script_filename)
    rout_contents = None
    if os.path.exists(rout):
        rout_contents = read_file(rout)
        os.remove(rout)
    rdata_file = os.path.join(os.path.split(r_script_filename)[0], '.RData')
    if os.path.exists(rdata_file):
        os.remove(rdata_file)
    if errcode != 0:
        print(rout_contents)
        raise Exception("The R script failed with error code %d." % errcode)
    return rout_contents