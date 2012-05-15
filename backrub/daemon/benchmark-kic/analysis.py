#!/usr/bin/python
#This file was developed and written by Roland A. Pache, Ph.D., Copyright (C) 2011, 2012.

#import libraries
import re
import os
import time
import sys
import math
import functions_lib

print '\nAnalyses the KIC scientific benchmark and creates a pdf report of the results.\n'


#constants

#patterns

#define classes
class Model:
    def __init__(self):
        self.id=None
        self.loop_rms=float('inf')
        self.total_energy=float('inf')
        self.runtime=None

#define functions
def getEnergyStats(models):
    energies=[]
    for model in models:
        if model.id!=None:
            energies.append(model.total_energy)
    #--
    return (min(energies),functions_lib.median(energies),max(energies))

def getRmsdStats(models):
    rmsds=[]
    for model in models:
        if model.id!=None:
            rmsds.append(model.loop_rms)
    #--
    return (min(rmsds),functions_lib.median(rmsds),max(rmsds))

def scatterplot(sorted_models,best_model,outfile_name):
    outfile=open(outfile_name,'w')
    outfile.write('#Model\tLoop_rmsd\tTotal_energy\n')
    energies=[]
    for model in sorted_models:
        outfile.write(model.id+'\t'+str(model.loop_rms)+'\t'+str(model.total_energy)+'\n')
        energies.append(model.total_energy)
    #-
    #third_quartile=functions_lib.quantile(energies,0.75)
    outfile.write('\n\n')
    for i in range(5):
        model=sorted_models[i]
        outfile.write(model.id+'\t'+str(model.loop_rms)+'\t'+str(model.total_energy)+'\n')
    #-
    outfile.write('\n\n')
    #best_model=sorted_models[0]
    outfile.write(best_model.id+'\t'+str(best_model.loop_rms)+'\t'+str(best_model.total_energy)+'\n')
    outfile.close()
    eps_outfile_name=outfile_name.split('.')[0]+'_all.eps'
    #eps_outfile_name2=outfile_name.split('.')[0]+'_third_quartile.eps'
    gnuplot_commands='\nset autoscale\
    \nset border 31\
    \nset tics out\
    \nset terminal postscript eps enhanced color solid "Helvetica" 24\
    \n#set size 1,1.5\
    \n#set size ratio 1\
    \n#set xtics ("default" 1, "default" 2, "H/Y" 3, "Y/H" 4, "default" 6, "default" 7, "H/Y" 8, "Y/H" 9) rotate by -45\
    \nset xtics autofreq\
    \nset xtics nomirror\
    \nset ytics autofreq\
    \nset ytics nomirror\
    \nset noy2tics\
    \nset nox2tics\
    \n\
    \nset style line 1 lt rgb "dark-magenta" lw 2\
    \nset style line 2 lt rgb "blue" lw 2 ps 1 pt 7\
    \nset style line 3 lt rgb "forest-green" lw 2 ps 2 pt 13\
    \nset style line 4 lt rgb "gold" lw 2 ps 1 pt 7\
    \nset style line 5 lt rgb "red" lw 2 ps 2 pt 13\
    \nset style line 6 lt rgb "black" lw 2\
    \nset style line 7 lt rgb "dark-gray" lw 2\
    \nset style line 8 lt rgb "gray" lw 2\
    \n\
    \nset boxwidth 0.75\
    \n\
    \nset key top right\
    \nset xrange [0:]\
    \nset title "'+outfile_name.split('/')[-1].split('_')[0]+'"\
    \nset encoding iso_8859_1\
    \nset xlabel "r.m.s. deviation to crystal loop [{/E \305}]"\
    \nset ylabel "Rosetta all-atom score"\
    \nset output "'+eps_outfile_name+'"\
    \nplot "'+outfile_name+'" index 0 using ($2):($3) with points ls 2 title "KIC protocol (all models)" axes x1y1,\
    "'+outfile_name+'" index 1 using ($2):($3) with points ls 4 title "KIC protocol (5 lowest energy models)" axes x1y1,\
    "'+outfile_name+'" index 2 using ($2):($3) with points ls 5 title "KIC protocol (top '+str(top_X)+' best model)" axes x1y1\
    \n'
    ## \nset yrange [:'+str(third_quartile)+']\
    ## \nset output "'+eps_outfile_name2+'"\
    ## \nplot "'+outfile_name+'" index 0 using ($2):($3) with points ls 2 title "KIC protocol (75% lowest-scoring models)" axes x1y1,\
    ## "'+outfile_name+'" index 1 using ($2):($3) with points ls 4 title "KIC protocol (5 lowest energy models)" axes x1y1,\
    ## "'+outfile_name+'" index 2 using ($2):($3) with points ls 5 title "KIC protocol (top '+str(top_X)+' best model)" axes x1y1\
    ## \n'
    gnuplot_scriptname=outfile_name.split('.')[0]+'.gnu'
    functions_lib.newFile(gnuplot_commands,gnuplot_scriptname)
    functions_lib.run('gnuplot '+gnuplot_scriptname)
    functions_lib.run('epstopdf --nocompress '+eps_outfile_name)
    #functions_lib.run('epstopdf --nocompress '+eps_outfile_name2)


def boxplot(models,outfile_name):
    boxplot_data={}
    boxplot_data[1]=[]
    for model in models:
        boxplot_data[1].append(model.loop_rms)
    #-
    tuples=functions_lib.boxAndWhisker(boxplot_data)
    outfile=open(outfile_name,'w')
    outfile.write('#x\t'+'min\t'+'first_quartile\t'+'median\t'+'third_quartile\t'+'max\n')
    for tuple in tuples:
        for item in tuple:
            outfile.write(str(item)+'\t')
        #-
        outfile.write('\n\n\n')
    #-
    outfile.close()
    eps_outfile_name=outfile_name.split('.')[0]+'.eps'
    gnuplot_commands='\nset autoscale\
    \nset border 31\
    \nset tics out\
    \nset terminal postscript eps enhanced color solid "Helvetica" 24\
    \nset size ratio 1\
    \nset xtics ("KIC" 1)\
    \nset xrange [0.5:1.5]\
    \nset nox2tics\
    \nset ytics autofreq\
    \nset ytics nomirror\
    \nset noy2tics\
    \n\
    \nset style line 1 lt rgb "dark-magenta" lw 2\
    \nset style line 2 lt rgb "blue" lw 5 pt 7\
    \nset style line 3 lt rgb "forest-green" lw 2\
    \nset style line 4 lt rgb "gold" lw 2\
    \nset style line 5 lt rgb "red" lw 5 pt 7\
    \nset style line 6 lt rgb "black" lw 5\
    \nset style line 7 lt rgb "dark-gray" lw 2\
    \nset style line 8 lt rgb "gray" lw 2\
    \n\
    \nset boxwidth 0.25\
    \n\
    \nset key tmargin\
    \nset title "Best models performance distribution"\
    \nset noxlabel\
    \nset style fill solid\
    \nset encoding iso_8859_1\
    \nset ylabel "r.m.s. deviation to crystal loop [{/E \305}]"\
    \nset output "'+eps_outfile_name+'"\
    \nplot "'+outfile_name+'" index 0 using 1:3:2:6:5 with candlesticks whiskerbars ls 2 notitle axes x1y1,\
    "'+outfile_name+'"index 0 using 1:4:4:4:4 with candlesticks ls 6 notitle\
    \n'
    gnuplot_scriptname=outfile_name.split('.')[0]+'.gnu'
    functions_lib.newFile(gnuplot_commands,gnuplot_scriptname)
    functions_lib.run('gnuplot '+gnuplot_scriptname)
    functions_lib.run('epstopdf --nocompress '+eps_outfile_name)


def texHeader():
    header='\
    \n\\documentclass[a4paper,10pt]{article}\
    \n\\usepackage{a4wide}\
    \n\\usepackage[utf8]{inputenc}\
    \n\\usepackage[small,bf]{caption}\
    \n\\usepackage{times}\
    \n\\usepackage{amsmath,amsthm,amsfonts}\
    \n\\usepackage{graphicx}\
    \n\\usepackage{rotating}\
    \n\\usepackage[usenames,dvipsnames]{color}\
    \n\\usepackage{textcomp}\
    \n\\definecolor{deepblue}{rgb}{0,0,0.6}\
    \n\\usepackage[pdfpagemode=UseNone,pdfstartview=FitH,colorlinks=true,linkcolor=deepblue,urlcolor=deepblue,citecolor=black,pdftitle=KIC scientific benchmark]{hyperref} %for ideal pdf layout and hyperref\
    \n\\usepackage{booktabs}\
    \n\\usepackage{colortbl}\
    \n\\usepackage{multirow}\
    \n\\usepackage[round]{natbib}\
    \n\\bibliographystyle{apalike}\
    \n\\renewcommand{\\thefootnote}{\\fnsymbol{footnote}}\
    \n\\begin{document}\
    \n\\setcounter{page}{1}\
    \n\\setcounter{footnote}{0}\
    \n\\renewcommand{\\thefootnote}{\\arabic{footnote}}\
    \n\
    \n\\begin{center}\
    \n{\\huge KIC scientific benchmark}\\\\[0.5cm]\
    \n\\today\
    \n\\end{center}'
    return header

            
start_time=time.time()


#parse input parameters
if len(sys.argv)!=2:
    print
    print 'Usage: ./KIC_scientific_benchmark_analysis.py PARAMETER_FILE'
    print
    sys.exit()
#-
parameter_file=sys.argv[1]
parameters=functions_lib.parseParameterFile(parameter_file)
num_models_offset=int(parameters['num_models_offset'])
num_models_per_PDB=int(parameters['num_models_per_PDB'])
infile_name=parameters['results_flatfile']
placeholder_image=parameters['placeholder_image']
top_X=int(parameters['num_lowest_energy_models_to_consider_for_best_model'])
outdir=parameters['analysis_outdir']


#parse models
pdb_models={}
print
print infile_name
start_index=num_models_offset+1
end_index=num_models_offset+num_models_per_PDB
total_runtime=0
infile=open(infile_name)
for line in infile:
    if not line.startswith('#'):
        data=line.strip('\n').split('\t')
        if len(data)>4:
            pdb=data[0]
            if pdb not in pdb_models:
                 pdb_models[pdb]=[]
            #-
            model_index=int(data[1])
            if model_index>=start_index and model_index<=end_index:
                model=Model()
                model.id=data[0]+'_'+data[1]
                model.loop_rms=float(data[2])
                model.total_energy=float(data[3])
                model.runtime=int(data[4])
                pdb_models[pdb].append(model)
                total_runtime+=int(data[4])
#----
infile.close()
if total_runtime!=0:
    print 'total runtime [hours]:',int(total_runtime/float(3600))
#-


#create outdir
if not os.path.isdir(outdir):
    os.makedirs(outdir)
#-


#compute basic statistics and create rmsd vs. Rosetta score plots per PDB
tex_tables=[]
best_models=[]
closest_models=[]
sorted_pdb_ids=sorted(pdb_models.keys())
print len(sorted_pdb_ids),'PDBs'
#init results tex table
tex_table_string='\\begin{tabular}{rr|rrr|rrr}\n\
PDB &\# models &Top '+str(top_X)+' best model &Loop rmsd &Energy &Closest model &Loop rmsd &Energy\\\\\\hline\n'
for pdb in sorted_pdb_ids:
    print
    print pdb
    models=pdb_models[pdb]
    print len(models),'successful models'
    #determine best and closest model for the given pdb
    sorted_energy_models=sorted(models,lambda x, y: cmp(x.total_energy,y.total_energy))
    sorted_rmsd_models=sorted(models,lambda x, y: cmp(x.loop_rms,y.loop_rms))
    best_model=sorted_energy_models[0]
    #when looking for the best model, consider the top X lowest energy models and pick the one with lowest rmsd
    for i in range(top_X):
        best_model_candidate=sorted_energy_models[i]
        if best_model_candidate.loop_rms<best_model.loop_rms:
            best_model=best_model_candidate
    #--
    closest_model=sorted_rmsd_models[0]
    print 'Top '+str(top_X)+' best model (i.e. lowest rmsd of top '+str(top_X)+' lowest energy models):',best_model.id,best_model.loop_rms,best_model.total_energy
    print 'closest model (i.e. lowest rmsd):',closest_model.id,closest_model.loop_rms,closest_model.total_energy
    best_models.append(best_model)
    closest_models.append(closest_model)
    #create scatterplot for each pdb
    outfile_name=outdir+pdb+'_models.out'
    scatterplot(sorted_energy_models,best_model,outfile_name)
    #store data in results tex table
    tex_table_string+=pdb+' &'+str(len(models))+' &'+best_model.id.split('_')[-1]+' &'+'%0.2f' % best_model.loop_rms+' &'+'%0.2f' % best_model.total_energy+' &'+closest_model.id.split('_')[-1]+' &'+'%0.2f' % closest_model.loop_rms+' &'+'%0.2f' % closest_model.total_energy+'\\\\\n'
#-
#write results tex table
tex_table_string+='\\end{tabular}\n'
tex_outfile_name=outdir+'results.tex'
tex_tables.append(tex_outfile_name)
functions_lib.newFile(tex_table_string,tex_outfile_name)
print
print tex_outfile_name


#create rmsd boxplot for the best models
boxplot_outfile_name=outdir+'best_models_rmsd_dist.out'
boxplot(best_models,boxplot_outfile_name)
print outdir


#calculate global stats across all pdbs and write overall performance tex table
print
print 'Global statistics (median rmsd and energy):'
outfile_name=outdir+'global_results.tex'
tex_tables.append(outfile_name)
best_models_median_energy=round(getEnergyStats(best_models)[1],2)
best_models_median_rmsd=round(getRmsdStats(best_models)[1],2)
closest_models_median_energy=round(getEnergyStats(closest_models)[1],2)
closest_models_median_rmsd=round(getRmsdStats(closest_models)[1],2)
print 'best models median rmsd and energy:',best_models_median_rmsd,best_models_median_energy
print 'closest models median rmsd and energy:',closest_models_median_rmsd,closest_models_median_energy
outstring='\
\\begin{tabular}{lrr}\
\nModel selection &Median loop rmsd &Median energy\\\\\\hline\
\n{\\bf Top '+str(top_X)+' best model} &{\\bf '+'%0.2f' % best_models_median_rmsd+'} &{\\bf '+'%0.2f' % best_models_median_energy+'}\\\\\n\
Closest model &'+'%0.2f' % closest_models_median_rmsd+' &'+'%0.2f' % closest_models_median_energy+'\\\\\n\
\\end{tabular}\n'
functions_lib.newFile(outstring,outfile_name)
print
print outfile_name


#put all model output figures into a tex table
score_vs_rmsd_plots=[]
num_pdbs=len(sorted_pdb_ids)
num_rows=3
num_cols=3
num_plots_per_page=num_rows*num_cols
num_pages=int(math.ceil(num_pdbs/float(num_plots_per_page)))
print num_pdbs,'pdbs'
print num_pages,'pages'
index=0
for i in range(num_pages):
    outfile_name=outdir+'all_models_'+str(i+1)+'.tex'
    outstring='\\begin{sidewaysfigure}\n\
    \\resizebox{\\textwidth}{!}{\n\
    \\begin{tabular}{'
    for j in range(num_cols):
        outstring+='c'
    #-
    outstring+='}\n'
    for j in range(num_rows):
        for k in range(num_cols):
            if index<num_pdbs:
                pdb=sorted_pdb_ids[index]
                outstring+='\\includegraphics{'+outdir+pdb+'_models_all.pdf} &'
            else:
                outstring+='\\includegraphics{'+placeholder_image+'} &'
            #-
            index+=1
        #-
        outstring=outstring.rstrip(' &')+'\\\\\n'
    #-
    outstring+='\\end{tabular}\n\
    }\\end{sidewaysfigure}\n'
    functions_lib.newFile(outstring,outfile_name)
    score_vs_rmsd_plots.append(outfile_name)
    print
    print outfile_name
#-


#create report pdf
outfile_name=outdir+'KIC_scientific_benchmark_report_top'+str(top_X)+'_models_'+str(num_models_offset+1)+'-'+str(num_models_per_PDB)+'.tex'
outstring=texHeader()
outstring+='\
\n\\section{Overall benchmark performance}\
\n\\begin{center}\
\n\\input{'+tex_tables[1]+'}\
\n\
\n\\includegraphics[width=10cm]{'+boxplot_outfile_name.split('.out')[0]+'.pdf}\
\n\\end{center}\
\n\
\n\\section{Individual results per input structure}\
\n\\begin{table}[ht]\
\n\\input{'+tex_tables[0]+'}\
\n\\end{table}\
\n\
\n\\clearpage'
for i in range(len(score_vs_rmsd_plots)):
    outstring+='\n\\input{'+score_vs_rmsd_plots[i]+'}'
#-
outstring+='\n\\end{document}'
functions_lib.newFile(outstring,outfile_name)
for i in range(2):
    functions_lib.run('pdflatex -output-directory '+outdir+' '+outfile_name)
#-
print
print 'Final report:',outfile_name.split('.tex')[0]+'.pdf'


end_time=time.time()
print
print "\ntime consumed: "+str(end_time-start_time)
