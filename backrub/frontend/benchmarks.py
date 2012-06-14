#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Code for the benchmarks page
########################################

import os, re
import datetime
from datetime import date
from string import join
import pickle
import string
import rosettadb
from rosettahelper import DEVELOPMENT_HOSTS, DEVELOPER_USERNAMES, ggplotColorWheel
import locale
locale.setlocale(locale.LC_ALL, 'en_US')
script_filename = None

def initGoogleCharts(chartfnlist):
	html = []
	# The corechart library contains AreaChart, BarChart, and PieChart among others.
	html.append("""
			<!--Load the AJAX API-->
			<script type="text/javascript" src="https://www.google.com/jsapi"></script>
			<script type="text/javascript">
			
			// Load the Visualization API and the piechart package.
			google.load('visualization', '1', {'packages':['corechart', 'gauge', 'geochart']});
			</script>

			<script type="text/javascript">
			// Set a callback to run when the Google Visualization API is loaded.
			google.setOnLoadCallback(drawCharts);
			function drawCharts() {
				%s
			}
			</script>
			""" % join(chartfnlist,"\n"))
	return html

def getApplications():
	return [
		'backrub',
		'ddg_monomer',
		'loopmodel',
		'minimize_with_cst',
		'rosetta_scripts',
		'score_jd2',
		'sequence_tolerance',
		'--------',
		'AbinitioRelax',
		'relax',
		'fixbb',
		'fix_bb_monomer_ddg',
		'format_converter',
		'minimize',
		'minirosetta',
		'score',
		'(some application not mentioned here)',
		'--------',
		'analyze_casp9',
		'analyze_rtmin_failures',
		'AnchoredDesign',
		'AnchoredPDBCreator',
		'AnchorFinder',
		'angle_recovery_stats',
		'angles',
		'antibody_assemble_CDRs',
		'antibody_mode',
		'assemble_domains_jd2',
		'atom_design',
		'backrub_pilot',
		'batch_distances',
		'batchrelax',
		'benchmark',
		'BuildPeptide',
		'ca_to_allatom',
		'cluster_alns',
		'cluster',
		'combine_silent',
		'ComputeSAXSSpectrum',
		'crossaln',
		'CstfileToTheozymePDB',
		'cst_quality',
		'ddg_benchmark',
		'design_contrast_and_statistic',
		'design_DL',
		'design_frags',
		'distances',
		'disulf_stat',
		'dna_motifs_collector',
		'docking_prepack_protocol',
		'docking_protocol',
		'doug_dock_design_min_mod2_cal_cal',
		'EnzdesFixBB',
		'enzyme_design',
		'exposed_strand_finder',
		'extract_atomtree_diffs_jd1',
		'extract_atomtree_diffs',
		'extract_pdbs',
		'FastGap',
		'fix_alignment_to_match_pdb',
		'FlexPepDocking',
		'FloppyTail',
		'for_dkim',
		'fragmentpicker_integration_demo',
		'fragment_picker',
		'full_length_model',
		'FunGroupTK',
		'FunGroupTK_test',
		'gen3bpy',
		'gen_apo_grids',
		'gen_d2_4his',
		'gen_d2_hhhc',
		'gen_d2',
		'gen_disulf_homodimer',
		'gen_homo_hc',
		'genI213_2comp',
		'genI213_2dsf',
		'genI213',
		'genI213_nocontacts',
		'gen_lig_grids',
		'gentetra_bpy_from_znhis',
		'gentetra_from_trimer',
		'hbonds_test',
		'hierarchical_clustering',
		'holes_daball_input',
		'holes',
		'homodimer_design',
		'homodimer_maker',
		'hotspot_hash',
		'hotspot_stub_constraint_test',
		'hshash_utils',
		'idealize_jd2',
		'idealize',
		'ig_dump',
		'IKFGDB',
		'InterfaceAnalyzer',
		'inv_kin_lig_loop_design',
		'isct_test',
		'jcluster',
		'jd2test',
		'jdock',
		'jrelax',
		'jscore',
		'kcluster',
		'ligand_dock_jd1',
		'ligand_dock',
		'ligand_rpkmin_jd1',
		'ligand_rpkmin',
		'ligands_to_database',
		'loophash_createdb',
		'loophash_createfiltereddb',
		'loophash',
		'loops_from_density',
		'make_rot_lib',
		'match',
		'matdes_design',
		'matdes_dock',
		'matdes_mutalyze',
		'medal_exchange',
		'medal',
		'membrane_abinitio2',
		'minimalCstHomology',
		'minimalCstRelax',
		'minirosetta_graphics',
		'min_pack_min',
		'mm_params',
		'motif_dna_packer_design',
		'motif_loop_build',
		'mpi_msd',
		'mr_protocols',
		'MSA_design',
		'pack_stat_energy',
		'packstat',
		'partial_thread',
		'pdb_to_map',
		'pepspec_anchor_dock',
		'pepspec',
		'per_residue_energies',
		'per_residue_features',
		'pH_protocol',
		'pmut_scan_parallel',
		'print_dunscores',
		'ragul_darc_run',
		'ragul_darc_score',
		'r_broker',
		'r_cst_tool',
		'r_dock_tempered',
		'report_hbonds_for_plugin',
		'RescorePDDF',
		'RescoreSAXS',
		'residue_energy_breakdown',
		'revert_design_to_native',
		'r_frag_quality',
		'rna_cluster',
		'rna_database',
		'rna_denovo',
		'rna_design',
		'rna_extract',
		'rna_helix',
		'rna_minimize',
		'rna_score',
		'r_noe_assign',
		'roc_optimizer',
		'rosettaDNA',
		'rotamer_recovery',
		'r_pdb2top',
		'r_play_with_etables',
		'r_rmsf',
		'r_score_rdc',
		'r_tempered_sidechains',
		'r_trjconv',
		'sc',
		'score_aln2',
		'score_aln',
		'select_best_unique_ligand_poses_jd1',
		'select_best_unique_ligand_poses',
		'sequence_recovery',
		'silent2frag',
		'simple_dna_regression_test',
		'star_abinitio',
		'super_aln',
		'supercharge',
		'superdev',
		'sup_test',
		'surface_docking_jd2',
		'symdock_enum_3_1',
		'symdock_enum',
		'symdock_hybrid_cc3',
		'symdock_hybrid',
		'SymDock',
		'SymMetalInterface_TwoZN_design',
		'SymMetalInterface_TwoZN_setup',
		'template_features',
		'test1',
		'tester',
		'test_ikrs',
		'test_kc',
		'test_string',
		'test_surf_vol',
		'UBQ_E2_thioester',
		'UBQ_Gp_CYD-CYD',
		'UBQ_Gp_CYX-Cterm',
		'UBQ_Gp_LYX-Cterm',
		'UnfoldedStateEnergyCalculator',
		'version_scorefunction',
		'VIP_app',
		'vip',
		'willmatch_chorismate',
		'willmatch_d6_bpy',
		'windowed_rama',
		'windowed_rmsd',
		'yeates_align',
	]

def setupBenchmarkOptions(benchmarks):
	#Ideally we'd use the JSON module here but we need to upgrade to 2.6
	#import json
	#json.dumps(benchmarks) # use default=longhandler?
	for b in benchmarks.keys():
		for option in benchmarks[b]['options']:
			for k, v in option.iteritems():
				if v == None:
					option[k] = 'null'
				elif type(v) == type(1L):
					if v < 2^31:
						option[k] = int(v)
					else:
						raise Exception("Need to reformat longs for JSON.")
			option['FormElement'] = 'Benchmark%(BenchmarkID)sOption%(OptionName)s' % option

def getRunParameters(form, benchmarks):
	setupBenchmarkOptions(benchmarks)
	
	runtype = None
	benchmark = form['BenchmarkType'].value
	if form['BenchmarkCommandLineType'].value == 'Standard':
		cmdline = "%s %s" % (benchmarks[benchmark]['ParameterizedFlags'], benchmarks[benchmark]['SimpleFlags'])
		runtype = "Standard" 
	elif form['BenchmarkCommandLineType'].value == 'ExtraFlags':
		cmdline = "%s %s %s" % (benchmarks[benchmark]['ParameterizedFlags'], benchmarks[benchmark]['SimpleFlags'], form['BenchmarkAlternateFlags'].value)
		runtype = form['BenchmarkAlternateFlags'].value 
	elif form['BenchmarkCommandLineType'].value == 'Custom':
		cmdline = "%s %s" % (form['BenchmarkCommandLine_1'].value.replace("\n", " "), form['BenchmarkCommandLine_2'].value.replace("\n", " "))
		runtype = "Custom" 

		
	runoptions = {}
	for option in benchmarks[benchmark]['options']:
		val = form[option['FormElement']].value
		if option["Type"] == 'int':
			runoptions[option['OptionName']] = int(val)
		else:
			raise Exception("Unhandled benchmark option type '%s'. New code needs to be written to handle this case." % option["Type"])
	emailList = None
	if form.has_key('BenchmarkNotificationEmailAddresses'):
		emailList = form['BenchmarkNotificationEmailAddresses'].value
		if emailList.find(",") != -1:
			emailList = emailList.replace(",", ";")
			
	return {
		'BenchmarkID': benchmark, 
		'RunLength': form['BenchmarkRunLength'].value, 
		'RosettaSVNRevision': form['BenchmarkRosettaRevision'].value, 
		'RosettaDBSVNRevision': form['BenchmarkRosettaDBRevision'].value,
		'RunType' : runtype, 
		'CommandLine': cmdline,
		'BenchmarkOptions': pickle.dumps(runoptions),
		'ClusterQueue': form['BenchmarkClusterQueue'].value, 
		'ClusterArchitecture': form['BenchmarkClusterArchitecture'].value, 
		'ClusterMemoryRequirementInGB': float(form['BenchmarkMemoryRequirement'].value), 
		'ClusterWalltimeLimitInMinutes': int(form['BenchmarkWalltimeLimit'].value), 
		'NotificationEmailAddress': emailList, 
		'Status': 'queued', 
		}

def generateKICReport(BenchmarksDB, Benchmark1ID, Benchmark2ID, Benchmark1Name, Benchmark2Name):
	import sys
	sys.path.insert(0, "../daemon")
	import benchmark_kic.evaluate as KICEvaluation

	flatfile1 = None
	flatfile2 = None
	top_X = []
	results = BenchmarksDB.execute('SELECT BenchmarkOptions, File FROM BenchmarkRunOutputFile INNER JOIN BenchmarkRun ON BenchmarkRunID=BenchmarkRun.ID WHERE BenchmarkRunID=%s AND FileID=1 AND FileType="Flat file"', parameters = (Benchmark1ID, ))
	if results and results[0]:
		flatfile1 = results[0]["File"]
		options = pickle.loads(results[0]['BenchmarkOptions'])
		top_X.append(options['NumberOfLowestEnergyModelsToConsiderForBestModel'])
		top_X.append(options['NumberOfModelsPerPDB'])
	results = BenchmarksDB.execute('SELECT BenchmarkOptions, File FROM BenchmarkRunOutputFile INNER JOIN BenchmarkRun ON BenchmarkRunID=BenchmarkRun.ID WHERE BenchmarkRunID=%s AND FileID=1 AND FileType="Flat file"', parameters = (Benchmark2ID, ))
	if results and results[0]:
		flatfile2 = results[0]["File"]
		options = pickle.loads(results[0]['BenchmarkOptions'])
		top_X.append(options['NumberOfLowestEnergyModelsToConsiderForBestModel'])
		top_X.append(options['NumberOfModelsPerPDB'])
	if not flatfile1:
		print('''<script type="text/javascript">alert("Could not find the results file for benchmark run %s in the database.")</script>''' % Benchmark1ID) 
		return
	if not flatfile2:
		print('''<script type="text/javascript">alert("Could not find the results file for benchmark run %s in the database.")</script>''' % Benchmark2ID) 
		return
	
	top_X = min(top_X)
	evaluator = KICEvaluation.BenchmarkEvaluator('/backrub/temp/benchmarkdata/', Benchmark1Name, Benchmark2Name, flatfile1, flatfile2, passingFileContents = True, top_X = top_X, quiet = True)
	try:
		evaluator.run()
		return evaluator.PDF 
	except Exception, e:
		import traceback
		print("An error occurred creating the report.<br>Error: '%s'<br>Traceback:<br>%s" % (str(e), traceback.format_exc().replace("\n", "<br>")))
	
def generateReport(form, BenchmarksDB):
	Benchmark1Name = "Benchmark 1"
	if form.has_key('Benchmark1Name'):
		Benchmark1Name = form['Benchmark1Name'].value
	Benchmark2Name = "Benchmark 2"
	if form.has_key('Benchmark2Name'):
		Benchmark2Name = form['Benchmark2Name'].value
	Benchmark1ID = form['Benchmark1ID'].value
	Benchmark2ID = form['Benchmark2ID'].value
	if True: # todo: generalize KIC:
		return generateKICReport(BenchmarksDB, Benchmark1ID, Benchmark2ID, Benchmark1Name, Benchmark2Name)
	
def generateSubmissionPage(benchmark_details):
	html = []
	
	default_benchmark = "KIC"
	benchmarks = benchmark_details['benchmarks']
		
	benchmark_names = sorted(benchmarks.keys(), key=str.lower)
	
	for benchmarkID, details in benchmarks.iteritems():
		details['revisions'] = sorted([b['Version'] for b in benchmark_details['ExistingBinaries'] if b['Tool'] == details['BinaryName']], reverse = True)
	dbrevisions = sorted([b['Version'] for b in benchmark_details['ExistingBinaries'] if b['Tool'] == 'database'], reverse = True)
	
	benchmarkselector_html = ['<select name="BenchmarkType" onchange="ChangeBenchmark();">']
	for benchmark in benchmark_names:
		if benchmark == default_benchmark:
			benchmarkselector_html.append('<option value="%(benchmark)s" selected="selected">%(benchmark)s</option>' % vars())
		else:
			benchmarkselector_html.append('<option value="%(benchmark)s">%(benchmark)s</option>' % vars())
	benchmarkselector_html.append('</select>')

	runlengths = benchmark_details['runlengths']
	runlengthselector_html = ['<select name="BenchmarkRunLength">']
	for runlength in runlengths:
		runlengthselector_html.append('<option value="%(runlength)s">%(runlength)s</option>' % vars())
	runlengthselector_html.append('</select>')

	rosettarevisionselector_html = ['<select name="BenchmarkRosettaRevision"><option value=""></option></select>']
	
	rosettadbrevisionselector_html = ['<select name="BenchmarkRosettaDBRevision">']
	for rosettadbrevision in dbrevisions:
		rosettadbrevisionselector_html.append('<option value="%(rosettadbrevision)s">%(rosettadbrevision)s</option>' % vars())
	rosettadbrevisionselector_html.append('</select>')
	
	clusterqueues = benchmark_details['ClusterQueues']
	clusterqueueselector_html = ['<select name="BenchmarkClusterQueue">']
	for clusterqueue in clusterqueues:
		clusterqueueselector_html.append('<option value="%(clusterqueue)s">%(clusterqueue)s</option>' % vars())
	clusterqueueselector_html.append('</select>')

	clusterarchitectures = benchmark_details['ClusterArchitectures']
	clusterarchitectureselector_html = ['<select name="BenchmarkClusterArchitecture">']
	for clusterarchitecture in clusterarchitectures:
		clusterarchitectureselector_html.append('<option value="%(clusterarchitecture)s">%(clusterarchitecture)s</option>' % vars())
	clusterarchitectureselector_html.append('</select>')

	# Prepare the record for viewing on the webpage
	for benchmark in benchmark_names:
		ParameterizedFlags = benchmarks[benchmark]['ParameterizedFlags']
		ParameterizedFlags = ParameterizedFlags.replace(" -", "\n-")
		benchmarks[benchmark]['ParameterizedFlags'] = ParameterizedFlags
		SimpleFlags = benchmarks[benchmark]['SimpleFlags']
		SimpleFlags = SimpleFlags.replace(" -", "\n-")
		benchmarks[benchmark]['SimpleFlags'] = SimpleFlags
		benchmarks[benchmark]['CustomFlagsDimensions'] = [
			len(ParameterizedFlags.split("\n")), # Number of rows for ParameterizedFlags 
			1 + len(SimpleFlags.split("\n")), # Number of rows for SimpleFlags
			2 + max(max(map(len, ParameterizedFlags.split("\n"))), max(map(len, SimpleFlags.split("\n")))) # Number of columns for ParameterizedFlags and SimpleFlags 
		]
	setupBenchmarkOptions(benchmarks)
	
	html.append('''<script type="text/javascript">benchmarks=%(benchmarks)s;</script>''' % vars())
	
	benchmark_alternate_flags_selector_html = '<select style="display:none;" name="BenchmarkAlternateFlags"><option value=""></option></select>'

	tablewidth = 200
	
	html.append('''<center><div>''')
	html.append('''<H1 align=left> Submit a new benchmark run</H1><br>''')
	html.append('''<FORM name="benchmarkoptionsform" method="post" action="#">''')
	html.append('''<table id="benchmarksubmissionform" style="width:800px;">''')
	html.append('''<tr><td>''')
	html.append('''<table style="text-align:left">''')
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Benchmark</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(benchmarkselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Run length</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(runlengthselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Rosetta revision</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(rosettarevisionselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Rosetta database revision</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(rosettadbrevisionselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Notification email list</div></td>''' % vars())
	html.append('''<td><input type="text" style="width:200px" maxlength="256" name="BenchmarkNotificationEmailAddresses" value=""></td></tr>''')
	html.append('''</table>''')
	html.append('''</td></tr>''')
	html.append('''<tr><td><span id="benchmarkseparator">%s</span></td></tr>''' % ('&#8226; ' * 45))
	html.append('''<tr><td>''')
	html.append('''<br><b><i>Benchmark settings</i></b><br>''')
	html.append('''<table class="benchmarks"  style="text-align:left; table-layout: fixed;">''')
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Command line flags</div></td><td>
	<input type="radio" onchange='editCommandLine()' name="BenchmarkCommandLineType" checked="checked" value="Standard">Standard
	<input type="radio" onchange='editCommandLine()' name="BenchmarkCommandLineType" value="ExtraFlags">Extra flags
	<input type="radio" onchange='editCommandLine()' name="BenchmarkCommandLineType" value="Custom">Custom
	</td></tr>''' % vars())
	html.append('''<tr><td></td><td>%s</td></tr>''' % join(benchmark_alternate_flags_selector_html,""))
	
	ParameterizedFlags = benchmarks[default_benchmark]['ParameterizedFlags']
	SimpleFlags = benchmarks[default_benchmark]['SimpleFlags']
	html.append('''<tr><td></td><td><div id="BenchmarkCustomSettingsMessage" style="display:none;">The parameters in the first box are fixed as they are interpreted by benchmark's Python class in the scheduler.</div></td></tr>''')
	html.append('''<tr><td></td><td><textarea style="display:none;" readonly="readonly" name="BenchmarkCommandLine_1" rows="1" cols="1"></textarea></td></tr>''')
	html.append('''<tr><td></td><td><textarea style="display:none;" name="BenchmarkCommandLine_2" rows="1" cols="1"></textarea></td></tr>''')
	for benchmark in benchmark_names:
		for option in benchmarks[benchmark]['options']:
			if option["Type"] == 'int':
				html.append('''<tr class="benchmark_%(benchmark)s_options" style="display:none;"><td><div style="width:%(tablewidth)dpx">''' % vars())
				html.append('''%(Description)s</div></td><td><input type="text" style="width:75px" maxlength=8 name="%(FormElement)s" value="%(DefaultValue)s"></td></tr>''' % option)
			else:
				raise Exception("Unhandled benchmark option type '%s'. New code needs to be written to handle this case." % option["Type"])
	html.append('''</table>''')
	html.append('''</td></tr>''')
	
	html.append('''<tr><td>''')
	html.append('''<br><b><i>Cluster settings</i></b><br>''')
		
	html.append('''<table style="text-align:left; table-layout: fixed;">''')
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Cluster queue</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(clusterqueueselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Cluster architecture</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(clusterarchitectureselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Memory requirement (GB)</div></td>''' % vars())
	html.append('''<td><input type="text" style="width:75px" maxlength=8 name="BenchmarkMemoryRequirement" value="2"></td></tr>''' % option) # todo: use default here
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Wall-time limit (mins)</div></td>''' % vars())
	html.append('''<td><input type="text" style="width:75px" maxlength=8 name="BenchmarkWalltimeLimit" value="360"></td></tr>''' % option) # todo: use default here
	html.append('''</table>''')
	html.append('''</td></tr>''')
	
	#form["BenchmarksPage"].value = "report"
	#document.benchmarksform.BenchmarksPage.value = "report"
	html.append('''<tr><td><button onclick="
		if (validate())
		{
			document.benchmarksform.BenchmarksPage.value = 'report';
			document.benchmarkoptionsform.BenchmarksPage.value='report';
			document.benchmarkoptionsform.query.value='benchmarks';
			document.benchmarkoptionsform.submitted.value='T';
			document.benchmarkoptionsform.submit();
		}
		else
		{
			return false;
		}">Submit</button></td></tr>''')
	
	#html.append('''<tr><td><INPUT TYPE="Submit" VALUE="Submit"></td></tr>''')
	
	if False:
		bm_parameters = {}
		for option in benchmarks[selected_benchmark]['options']:
			if option["Type"] == 'int':
				bm_parameters[options['OptionName']] = int(valueof("Benchmark%sOption%s" %(selected_benchmark, options['OptionName'])))
			else:
				raise Exception("Unknown datatype '%s'. Write code to handle more option datatypes here." % option["Type"])
		result = getBenchmarksConnection().execInnoDBQuery("UPDATE BenchmarkRun SET BenchmarkOptions=%s WHERE ID=1", parameters = (pickle.dumps(bm_parameters),))
			
	
	html.append('''</table>''')
	html.append('''<input type="hidden" NAME="submitted" VALUE="F">''')
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''<input type="hidden" NAME="BenchmarksPage" VALUE="">''')
	html.append('''</FORM>''')

	html.append('''</div></center>''')
	return html, []

def generateBinaryBuilderPage():
	html = []
	
	tablewidth = 220
	html.append('''<center><div>''')
	html.append('''<H1 align=left>Request a new binary</H1><br>''')
	html.append('''<FORM name="binarybuilderform" method="post">''')
	html.append('''<table style="width:800px;">''')
	html.append('''<tr><td>''')
	html.append('''<table style="text-align:left">''')
	
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Request type</div></td>''' % vars())
	html.append('''<td><select name='RequestType'>''')
	html.append('''		<option value='BinaryPlusDatabase'>Binary + database</option>''')
	html.append('''		<option value='Binary'>Binary</option>''')
	html.append('''		<option value='Database'>Database</option>''')
	html.append('''</select></td></tr>''')
	
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Tool name</div></td>''' % vars())
	html.append('''<td><select name='ToolName'>''')
	for app in getApplications():
		html.append('''		<option value='%(app)s'>%(app)s</option>''' % vars())

	html.append('''</select></td></tr>''')
	
	html.append('''<tr><td></td><td><input name='ToolName' style='display:none; width:134px;' value=''></td></tr>''')
	
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Version type</div></td>''' % vars())
	html.append('''<td><select name='VersionType'>''')
	html.append('''		<option value='SVNRevision'>SVN Revision</option>''')
	html.append('''		<option value='Release'>Release</option>''')
	html.append('''</select></td></tr>''')
	
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Version</div></td>''' % vars())
	html.append('''<td><input name='Version' style='width:134px;' value=''></td></tr>''')
	
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Build type</div></td>''' % vars())
	html.append('''<td><select name='BuildType'>''')
	html.append('''		<option value='Release'>Release</option>''')
	html.append('''		<option value='Debug'>Debug</option>''')
	html.append('''</select></td></tr>''')
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Email address for build notification</div></td>''' % vars())
	html.append('''<td><input name='EmailList' style='width:134px;' value=''></td></tr>''')
	
	html.append('''<tr><td><div style="width:%(tablewidth)dpx"><b><i><br>Extra build options</i></b></div></td></tr>''' % vars())
	
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Build a static binary</div></td>''' % vars())
	html.append('''<td><select name='Static'>''')
	html.append('''		<option value='Yes'>Yes</option>''')
	html.append('''		<option value='No'>No</option>''')
	html.append('''</select></td></tr>''')
	
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Include OpenGL support (graphics)</div></td>''' % vars())
	html.append('''<td><select name='Graphics'>''')
	html.append('''		<option value='No'>No</option>''')
	html.append('''		<option value='Yes'>Yes</option>''')
	html.append('''</select></td></tr>''')

	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Include MySQL support</div></td>''' % vars())
	html.append('''<td><select name='MySQL'>''')
	html.append('''		<option value='No'>No</option>''')
	html.append('''		<option value='Yes'>Yes</option>''')
	html.append('''</select></td></tr>''')

	html.append('''<tr><td><br><INPUT TYPE="Submit" VALUE="Submit" disabled="disabled"></td></tr>''')
	
	html.append('''</table>''')
	html.append('''</td></tr>''')

	
	html.append('''</table>''')
	html.append('''</FORM>''')
	html.append('''</div></center>''')
	return html, []

def generateReportPage(benchmark_details):
	html = []
	html.append('''<center><div>''')
	html.append('''<H1 align=left>Benchmark runs</H1><br>''')
	html.append('''<FORM name="reportpageform" method="post" action="#">''')
	html.append('''<table style="width:800px;">''')
	html.append('''<tr><td>''')
	html.append('''<table class="sortable" border=1 cellpadding=4 cellspacing=0  width="1100px" style="font-size:12px;text-align:left">''')
	
	html.append("<tr style='background-color:#dddddd'>")
	html.append("<th>ID</th><th>Benchmark</th><th>Length</th><th>Status</th><th>Revision</th><th>DB Revision</th><th style='width:100px;'>Command line</th><th>Benchmark Options</th><th>Run time</th><th>Errors</th><th>Report</th><th colspan=2>Compare</th>")
	html.append("</tr>")
	for run in benchmark_details['BenchmarkRuns']:
		benchmark_color = benchmark_details['benchmarks'][run['BenchmarkID']]['color']
		html.append("<tr style='background-color:%s'>" % benchmark_color)
		html.append("<td>%(ID)d</td>" % run)
		html.append("<td>%(BenchmarkID)s</td>" % run)
		html.append("<td>%(RunLength)s</td>" % run)
		if run['Status'] == 'queued':
			html.append("<td style='text-align:center; background-color:#ffffff'>%(Status)s</td>" % run)
		elif run['Status'] == 'active':
			html.append("<td style='text-align:center; background-color:#ffff00'>%(Status)s</td>" % run)
		elif run['Status'] == 'done':
			html.append("<td style='text-align:center; text-align:center; background-color:#00aa00'>%(Status)s</td>" % run)
		elif run['Status'] == 'failed':
			html.append("<td style='text-align:center; background-color:#aa0000'>%(Status)s</td>" % run)
		html.append("<td>%(RosettaSVNRevision)s</td>" % run)
		html.append("<td>%(RosettaDBSVNRevision)s</td>" % run)
	
		tooltip = "header=[Command line] body=[%(CommandLine)s] offsetx=[-90] offsety=[20] singleclickstop=[on] cssbody=[tooltipbenchmark] cssheader=[tthbenchmark] length=[600px] delay=[250]" % run
		html.append("<td title='%s'>%s</td>" % (tooltip, run['RunType']))
		
		html.append("<td style='width:400px;'>")
		BenchmarkOptions = pickle.loads(run['BenchmarkOptions'])
		benchmark_options = benchmark_details['benchmarks'][run['BenchmarkID']]['options']
		for BenchmarkOptionName, val in sorted(BenchmarkOptions.iteritems()):
			for boption in benchmark_options:
				if boption['OptionName'] == BenchmarkOptionName:
					html.append("%s : %s<br>" % (boption['Description'], str(val)))
		html.append("</td>")
		
		if run["StartDate"] and run["EndDate"]:
			dInMinutes = int((run["EndDate"] - run["StartDate"]).seconds/60)
			if dInMinutes >= 60:
				dHours = int(dInMinutes / 60)
				dMinutes = dInMinutes % 60
				html.append("<td>%(dHours)dh %(dMinutes)dm</td>" % vars())
			else:
				html.append("<td>%(dInMinutes)dm</td>" % vars())
		else:
			html.append("<td></td>")
			#html.append("<td>%(EntryDate)s</td>" % run)
			
		if run['Errors']:
			tooltip = "header=[Error] body=[%s] offsetx=[-90] offsety=[20] singleclickstop=[on] cssbody=[tooltipbenchmark] cssheader=[tthbenchmark] length=[600px] delay=[250]" % run['Errors'].replace('\n', '<br>')
			html.append("<td title='%s'>Errors</td>" % tooltip)
		else:
			html.append("<td>None</td>" % run)
		
		pdfjavascript = '''window.open('%s?query=benchmarkreport&amp;id=%s&amp;action=view');''' % (script_filename, run["ID"])
		#filesaveasjavascript = '''window.open('%s?query=benchmarkreport&amp;id=%s&amp;action=download','KortemmeLabAdmin','height=400,width=850');''' % (script_filename, run["ID"])
		filesaveasjavascript = '''window.location.href = '%s?query=benchmarkreport&amp;id=%s&amp;action=download';''' % (script_filename, run["ID"])
		#	document.reportpageform.BenchmarksPage.value='report';
		#	document.reportpageform.query.value='benchmarks';
		#	document.reportpageform.benchmarkrunID.value='%(ID)s';
		#	document.reportpageform.submit();
		#	''' % run
		if run["Status"] == "done" and run["HasPDF"]:
			html.append('''<td style='text-align:center; width:20px;'>
				<span style='cursor:pointer;' onclick="%(pdfjavascript)s"><img src='../images/pdf16.png' alt='pdf'></span>
				<span style='cursor:pointer;' onclick="%(filesaveasjavascript)s"><img src='../images/filesaveas16.png' alt='save'></span>
				</td>''' % vars())
		else:
			html.append('''<td></td>''')
		#html.append("<td style='width:20px;'><a href='../images/pdf16.pdf'>PDF</a></td>") # PDFReport
		html.append("<td><input type='radio' name='benchmarkresults1' onchange='benchmarkWasSelected();' value='%(ID)d'></td>" % run)
		html.append("<td><input type='radio' name='benchmarkresults2' onchange='benchmarkWasSelected();' value='%(ID)d'></td>" % run)
		html.append("</tr>")
	
	html.append('''</table>''')
	html.append('''<div style='text-align:right'><button name="CompareButton" disabled="disabled" onclick="
querystring = getBenchmarkNames(); // set the Benchmark1Name/ID and Benchmark2Name/ID values
window.open('%s?' + querystring);
return false;
">Compare</button></div>''' % (script_filename))
	html.append('''</td></tr>''')
	html.append('''</table>''')
	html.append('''<input type="hidden" NAME="benchmarkrunID" VALUE="">''')
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''<input type="hidden" NAME="BenchmarksPage" VALUE="">''')
	html.append('''<input type="hidden" NAME="BenchmarksType" VALUE="">''')
	html.append('''<input type="hidden" NAME="Benchmark1Name" VALUE="">''')
	html.append('''<input type="hidden" NAME="Benchmark2Name" VALUE="">''')
	html.append('''<input type="hidden" NAME="Benchmark1ID" VALUE="">''')
	html.append('''<input type="hidden" NAME="Benchmark2ID" VALUE="">''')
	html.append('''</FORM></div></center>''')
	
	return html, []

def generateBenchmarksPage(settings_, rosettahtml, form, benchmark_details):

	global settings
	global script_filename
	settings = settings_
	script_filename = rosettahtml.script_filename 

	benchmarkspage = ""
	if form.has_key("BenchmarksPage"):
		benchmarkspage = form["BenchmarksPage"].value
	
	benchmarks = benchmark_details['benchmarks']
	if True:
		# For testing Javascript on multiple benchmarks
		benchmarks['backrub'] = {}
		benchmarks['backrub']['BinaryName'] = 'backrub'
		benchmarks['backrub']['ParameterizedFlags'] = 'backrub pflags'
		benchmarks['backrub']['SimpleFlags'] = 'backrub simple flags'
		benchmarks['backrub']['alternate_flags'] = ['none']
		benchmarks['backrub']['options'] = [{'Description': 'Test option', 'OptionName': 'TestOptionName', 'DefaultValue': '33', 'BenchmarkID': 'backrub', 'MaximumValue': None, 'MinimumValue': '0', 'Type': 'int', 'ID': 9999}]

	benchmarktypes = set()
	for run in benchmark_details['BenchmarkRuns']:
		benchmarktypes.add(run['BenchmarkID'])
	for benchmarkname in benchmarks.keys():
		benchmarktypes.add(benchmarkname)
	_benchmarkcolors = ggplotColorWheel(len(benchmarktypes), start = 195, saturation_adjustment = 0.3)
	benchmarktypes = sorted(list(benchmarktypes))
	benchmark_colors = dict.fromkeys(benchmarktypes)
	for i in range(len(benchmarktypes)):
		benchmark_colors[benchmarktypes[i]] = _benchmarkcolors[i] 
	for benchmarkname in benchmarks.keys():
		benchmarks[benchmarkname]['color'] = benchmark_colors[benchmarkname] 
	
	# Set generate to False to hide pages for quicker testing
	subpages = [
		{"name" : "submission",	"desc" : "Submit",			"fn" : generateSubmissionPage,	"generate" :True,	"params" : [benchmark_details]},
		{"name" : "report",		"desc" : "View reports",	"fn" : generateReportPage,		"generate" :True,	"params" : [benchmark_details]},
		{"name" : "binaries",	"desc" : "Build binaries",	"fn" : generateBinaryBuilderPage,"generate" :True,	"params" : []},
		]
	
	# Create menu
	html = ['''''']
	html.append("<td align=center>")
	html.append('''<FORM name="benchmarksform" method="post" action="#">''')
	
	for subpage in subpages:
		if subpage["generate"]:
			html.append('''<input type="button" value="%(desc)s" onClick="showPage('%(name)s');">''' % subpage)
	
	html.append('''<input type="button" value="Refresh" onClick="document.benchmarksform.query.value='benchmarks'; document.benchmarksform.submit();">''')
	html.append('''<input type="hidden" NAME="BenchmarksPage" VALUE="%s">''' % benchmarkspage)
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''</FORM>''')
	html.append("</td></tr><tr>")
	
	html.append("<td align=left>")
	
	# Disk stats
	gchartfns = []
	for subpage in subpages:
		html.append('<div style="display:none" id="%s">' % subpage["name"])
		if subpage["generate"]:
			h, gcf = subpage["fn"](*subpage["params"])
			html.extend(h)
			gchartfns.extend(gcf)
		html.append("</div>")
	
	# Prepare javascript calls
	for i in range(len(gchartfns)):
		gchartfns[i] += "();"


	html.append("</td>")
	html.extend(initGoogleCharts(gchartfns))
	html.append('''
<script src="/backrub/frontend/benchmarks.js" type="text/javascript"></script>
<script src="/javascripts/sorttable.js" type="text/javascript"></script>''')

	return html