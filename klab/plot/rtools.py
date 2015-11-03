import sys
import os
import inspect
import subprocess
import time

from klab.fs.fsio import read_file, write_temp_file

class RInterface(object):

    @staticmethod
    def _runRScript(RScript):
        rscriptname = write_temp_file(".", RScript)
        #p = subprocess.Popen(["/opt/R-2.15.1/bin/R","CMD", "BATCH", rscriptname])
        p = subprocess.Popen(["R", "CMD", "BATCH", rscriptname])
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
        return rout_contents


    @staticmethod
    def correlation_coefficient_gplot(inputfname, output_filename, filetype, experiment_field = "Experimental", title = ''):
        '''File suffix: pearsons_r_gplot
           Description: Pearson's r
           Filename: ggplot_pearsons.R
           Priority: 1
           '''
        script_path = os.path.abspath(os.path.dirname(inspect.getsourcefile(sys.modules[__name__])))
        RScript = read_file(os.path.join(script_path, "ggplot_pearsons.R")) % vars()
        return RInterface._runRScript(RScript)