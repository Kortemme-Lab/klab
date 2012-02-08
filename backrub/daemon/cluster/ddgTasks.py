import os
import re
from string import join
import traceback
import rosettahelper
from conf_daemon import *
from ClusterTask import ClusterTask, ddGClusterScript, FAILED_TASK
from ClusterScheduler import TaskScheduler, RosettaClusterJob
from RosettaTasks import PostProcessingException
import ddgproject
ddgfields = ddgproject.FieldNames()

# Generic classes

class ddgScore(object):
	type = None
	version = None
	
	def __init__(self, data = {}):
		self.data = data
	
	def getType(self):
		return type
	
	def getVersion(self):
		return version
	
	def setData(self, data):
		self.data = data

	def getScores(self):
		return {"type" : self.type, "version" : self.version, "data" : self.data}

class ddgTestScore(ddgScore):
	type = "test"
	version = "0.1"

class GenericDDGTask(ClusterTask):

	# additional attributes
	def __init__(self, workingdir, targetdirectory, jobparameters, taskparameters, name="", prefix = "ddG"):
		self.prefix = prefix
		self.taskparameters = taskparameters
		self.inputs = {"BIN_DIR" : taskparameters["ToolVersion"], "DATABASE_DIR" : taskparameters["DBToolVersion"]}
		self.outputs = {}
		super(GenericDDGTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, jobparameters["ID"]), jobparameters, name, numtasks = 1) # todo: do not hardcode numtasks
		
	def addInputs(self, inpts):
		self._status("Adding inputs: %s" % inpts)
		for k, v in inpts.iteritems():
			if self.inputs.get(k):
				raise Exception("Overwriting task input %s (old value = %s, attempted new value = %s)", (k, self.inputs[k], v))
			self.inputs[k] = v
		
	def addOutputs(self, outputs):
		self.outputs = outputs
	
	def getOutputs(self, taskref):
		self._status("Asking for outputs for %s" % str(taskref))
		for taskRefandIDPair, params in self.outputs.iteritems():
			if taskRefandIDPair[0] == taskref:
				self._status("Found a match: %s" % params)
				return params
		self._status("No match for you! Come back, one year!")
		return {}			
		
	def setOutput(self, key, val, taskID = None):
		outputs = self.outputs
		if taskID:
			# Set the value for a specific task based on the StepID field of the ProtocolStep table
			for taskRefandIDPair, params in outputs.iteritems():
				self._status("YOP %s:%s" % taskRefandIDPair, params)
				if taskRefandIDPair[1] == taskID:
					if key in params:
						params[key] = val
						break
					else:
						raise Exception("Trying to set a value %s for key %s between tasks %s->%s when the key does not exist in the parameter table for the target task." % (val, key, self.name, taskID))
		else:
			# Set the value for all tasks
			foundkey = False
			for taskRefandIDPair, params in outputs.iteritems():
				if key in params:
					params[key] = val
					foundkey = True
			if not foundkey:
				raise Exception("Trying to set a value %s for key %s of task %s when the key does not exist in the parameter table." % (val, key, self.name))

	def _initialize(self):
		pass
		#jobparameters = self.parameters
		#taskparameters = self.taskparameters
		
	def start(self, sgec, dbID):
		# Create script
		self._status("starting")
		inputs = self.inputs
		for k, v in inputs.iteritems():
			if not v:
				self._status("The input parameter %s has not been specified." % k)
				raise Exception("The input parameter %s has not been specified." % k)
		ct = ddGClusterScript(self.workingdir, inputs, numtasks = self.numtasks)
		self.script = ct.createScript(self.taskparameters["Command"].split("\n"), type="ddG")
		return super(GenericDDGTask, self).start(sgec, dbID)
				

class GenericddGJob(RosettaClusterJob):

	suffix = "ddG"
	flatOutputDirectory = True
	name = "ddG"

	def _defineOutputFiles(self):
		self.resultFilemasks.append((".", "*"))
		
	def getddG(self):
		return self.ddG.getScores()

	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
		# The tempdir is the one on the submission host e.g. chef
		# targetdirectory is the one on your host e.g. your PC or the webserver
		# The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
		# The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
		self.ddG = ddgTestScore()
		super(GenericddGJob, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
			
	def _initialize(self):
		parameters = self.parameters
		parameters['_CMD'] = {} # This stores task parameters set up by the Job. The keys must have unique names per task if different values are required for each task.
		parameters['_FILE_ID'] = "%s-%s" % (parameters[ddgfields.ExperimentID], parameters[ddgfields.PDB_ID])
		ProtocolGraph = parameters["ProtocolGraph"]
		for taskID, details in ProtocolGraph.iteritems():
			if details["ToolVersion"][0] != "r":
				details["ToolVersion"] = "r%s" % details["ToolVersion"]
			if details["DBToolVersion"][0] != "r":
				details["DBToolVersion"] = "r%s" % details["DBToolVersion"]
		
		# Create files
		self.describe()
		self._generateFiles()
		
		# Create tasks from the protocol steps
		tasks = {}
		ProtocolGraph = parameters["ProtocolGraph"]
		for taskID, details in ProtocolGraph.iteritems():
			taskcls = details["ClassName"] or "GenericDDGTask"
			taskcls = taskcls.replace(".", "") # todo : remove this step later when everything is separated into modules
			taskcls = globals()[taskcls]
			targetsubdirectory = details["DirectoryName"]
			taskdir = self._make_taskdir(targetsubdirectory)
			details["_task"] = taskcls(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), parameters, details, name=details["ProtocolStepID"], prefix=details["ProtocolStepID"])

		# Define the input and output parameters
		for taskID, details in ProtocolGraph.iteritems():
			task_inputs = {}
			task_outputs = {}
			stepID = details["ProtocolStepID"]
			for tpl, cparams in parameters["CommandParameters"].iteritems():
				jobparam = None
				if tpl[0] == tpl[1]:
					raise Exception("Badly specified protocol parameters - step %s feeds into itself." % tpl[0])
				elif tpl[0] == stepID:
					trgt_o = ProtocolGraph[tpl[1]]["_task"]
					for cmdparam in cparams:
						task_outputs[(trgt_o, trgt_o.prefix)] = task_outputs.get((trgt_o, trgt_o.prefix), {})
						task_outputs[(trgt_o, trgt_o.prefix)][cmdparam[0]] = cmdparam[1] or jobparam 
				elif tpl[1] == stepID:
					for cmdparam in parameters["CommandParameters"][tpl]:
						jobparam = parameters['_CMD'].get(cmdparam[0])
						if jobparam and cmdparam[1]:
							raise Exception("Task #%d: %s is defined by both the Job and the database entry." % (stepID, cmdparam[0]))
						elif not(jobparam or cmdparam[1]) and tpl[0] == None: # Allow null values to be filled in by parent tasks
							raise Exception("Task #%d: %s is undefined." % (stepID, cmdparam[0]))
						else:
							task_inputs[cmdparam[0]] = cmdparam[1] or jobparam
			ProtocolGraph[stepID]["_task"].addInputs(task_inputs)
			ProtocolGraph[stepID]["_task"].addOutputs(task_outputs)
		
		self.ProtocolGraph = ProtocolGraph
				 
		# Create a scheduler from the protocol graph
		scheduler = TaskScheduler(self.workingdir) 
		for taskID, details in ProtocolGraph.iteritems():
			for p in details["Parents"]:
				details["_task"].addPrerequisite(ProtocolGraph[p]["_task"])
		for itask in parameters["InitialTasks"]:
			scheduler.addInitialTasks(ProtocolGraph[itask]["_task"])
		self.scheduler = scheduler

	def _generateFiles(self):
		'''Create input files here. This function must be implemented.'''
		# todo: Add profiling step for this
		raise Exception("Implement this function.")
	
	def _analyze(self):
		'''Run analysis here.'''
		raise Exception("Implement this function.")

class GenericBatchDDGTask(ClusterTask):

	# additional attributes
	def __init__(self, workingdir, targetdirectory, jobparameters, taskparameters, name="", prefix = "ddG"):
		self.prefix = prefix
		self.taskparameters = taskparameters
		self.inputs = {"BIN_DIR" : taskparameters["ToolVersion"], "DATABASE_DIR" : taskparameters["DBToolVersion"]}
		self.outputs = {}
		super(GenericDDGTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, jobparameters["ID"]), jobparameters, name, numtasks = 1) # todo: do not hardcode numtasks
		
	def addInputs(self, inpts):
		self._status("Adding inputs: %s" % inpts)
		for k, v in inpts.iteritems():
			if self.inputs.get(k):
				raise Exception("Overwriting task input %s (old value = %s, attempted new value = %s)", (k, self.inputs[k], v))
			self.inputs[k] = v
		
	def addOutputs(self, outputs):
		self.outputs = outputs
	
	def getOutputs(self, taskref):
		self._status("Asking for outputs for %s" % str(taskref))
		for taskRefandIDPair, params in self.outputs.iteritems():
			if taskRefandIDPair[0] == taskref:
				self._status("Found a match: %s" % params)
				return params
		self._status("No match for you! Come back, one year!")
		return {}			
		
	def setOutput(self, key, val, taskID = None):
		outputs = self.outputs
		if taskID:
			# Set the value for a specific task based on the StepID field of the ProtocolStep table
			for taskRefandIDPair, params in outputs.iteritems():
				self._status("YOP %s:%s" % taskRefandIDPair, params)
				if taskRefandIDPair[1] == taskID:
					if key in params:
						params[key] = val
						break
					else:
						raise Exception("Trying to set a value %s for key %s between tasks %s->%s when the key does not exist in the parameter table for the target task." % (val, key, self.name, taskID))
		else:
			# Set the value for all tasks
			foundkey = False
			for taskRefandIDPair, params in outputs.iteritems():
				if key in params:
					params[key] = val
					foundkey = True
			if not foundkey:
				raise Exception("Trying to set a value %s for key %s of task %s when the key does not exist in the parameter table." % (val, key, self.name))

	def _initialize(self):
		pass
		#jobparameters = self.parameters
		#taskparameters = self.taskparameters
		
	def start(self, sgec, dbID):
		# Create script
		self._status("starting")
		inputs = self.inputs
		for k, v in inputs.iteritems():
			if not v:
				self._status("The input parameter %s has not been specified." % k)
				raise Exception("The input parameter %s has not been specified." % k)
		ct = ddGClusterScript(self.workingdir, inputs, numtasks = self.numtasks)
		self.script = ct.createScript(self.taskparameters["Command"].split("\n"), type="ddG")
		return super(GenericDDGTask, self).start(sgec, dbID)
				

class GenericBatchDDGJob(RosettaClusterJob):

	suffix = "ddG"
	flatOutputDirectory = True
	name = "ddG"

	def _defineOutputFiles(self):
		self.resultFilemasks.append((".", "*"))
		
	def getddG(self):
		return self.ddG.getScores()

	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
		# The tempdir is the one on the submission host e.g. chef
		# targetdirectory is the one on your host e.g. your PC or the webserver
		# The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
		# The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
		self.ddG = ddgTestScore()
		super(GenericBatchDDGJob, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
			
	def _initialize(self):
		parameters = self.parameters
		parameters['_CMD'] = {} # This stores task parameters set up by the Job. The keys must have unique names per task if different values are required for each task.
		parameters['_FILE_ID'] = "%s-%s" % (parameters[ddgfields.ExperimentID], parameters[ddgfields.PDB_ID])
		ProtocolGraph = parameters["ProtocolGraph"]
		for taskID, details in ProtocolGraph.iteritems():
			if details["ToolVersion"][0] != "r":
				details["ToolVersion"] = "r%s" % details["ToolVersion"]
			if details["DBToolVersion"][0] != "r":
				details["DBToolVersion"] = "r%s" % details["DBToolVersion"]
		
		# Create files
		self.describe()
		self._generateFiles()
		
		# Create tasks from the protocol steps
		tasks = {}
		ProtocolGraph = parameters["ProtocolGraph"]
		for taskID, details in ProtocolGraph.iteritems():
			taskcls = details["ClassName"] or "GenericDDGTask"
			taskcls = taskcls.replace(".", "") # todo : remove this step later when everything is separated into modules
			taskcls = globals()[taskcls]
			targetsubdirectory = details["DirectoryName"]
			taskdir = self._make_taskdir(targetsubdirectory)
			details["_task"] = taskcls(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), parameters, details, name=details["ProtocolStepID"], prefix=details["ProtocolStepID"])

		# Define the input and output parameters
		for taskID, details in ProtocolGraph.iteritems():
			task_inputs = {}
			task_outputs = {}
			stepID = details["ProtocolStepID"]
			for tpl, cparams in parameters["CommandParameters"].iteritems():
				jobparam = None
				if tpl[0] == tpl[1]:
					raise Exception("Badly specified protocol parameters - step %s feeds into itself." % tpl[0])
				elif tpl[0] == stepID:
					trgt_o = ProtocolGraph[tpl[1]]["_task"]
					for cmdparam in cparams:
						task_outputs[(trgt_o, trgt_o.prefix)] = task_outputs.get((trgt_o, trgt_o.prefix), {})
						task_outputs[(trgt_o, trgt_o.prefix)][cmdparam[0]] = cmdparam[1] or jobparam 
				elif tpl[1] == stepID:
					for cmdparam in parameters["CommandParameters"][tpl]:
						jobparam = parameters['_CMD'].get(cmdparam[0])
						if jobparam and cmdparam[1]:
							raise Exception("Task #%d: %s is defined by both the Job and the database entry." % (stepID, cmdparam[0]))
						elif not(jobparam or cmdparam[1]) and tpl[0] == None: # Allow null values to be filled in by parent tasks
							raise Exception("Task #%d: %s is undefined." % (stepID, cmdparam[0]))
						else:
							task_inputs[cmdparam[0]] = cmdparam[1] or jobparam
			ProtocolGraph[stepID]["_task"].addInputs(task_inputs)
			ProtocolGraph[stepID]["_task"].addOutputs(task_outputs)
		
		self.ProtocolGraph = ProtocolGraph
				 
		# Create a scheduler from the protocol graph
		scheduler = TaskScheduler(self.workingdir) 
		for taskID, details in ProtocolGraph.iteritems():
			for p in details["Parents"]:
				details["_task"].addPrerequisite(ProtocolGraph[p]["_task"])
		for itask in parameters["InitialTasks"]:
			scheduler.addInitialTasks(ProtocolGraph[itask]["_task"])
		self.scheduler = scheduler

	def _generateFiles(self):
		'''Create input files here. This function must be implemented.'''
		# todo: Add profiling step for this
		raise Exception("Implement this function.")
	
	def _analyze(self):
		'''Run analysis here.'''
		raise Exception("Implement this function.")
	
# Jobs and tasks for specific protocols

class ddGK16Job(GenericddGJob):
	
	def _generateFiles(self):
		# Create input files
		self._write_lst(self._write_pdb())
		self._write_resfile()

	#def _name_constraints_file(self):
	#	self.parameters['CONSTRAINTS_FILE'] = self._workingdir_file_path("%(_FILE_ID)s.cst" % self.parameters)
	
	def _write_pdb(self):
		"""Import a pdb file from the database and write it to the temporary directory"""
		filename = self._workingdir_file_path("%(_FILE_ID)s.pdb" % self.parameters)
		F = open(filename, "w")
		F.write(self.parameters[ddgfields.StrippedPDB])
		F.close()
		return filename
		
	def _write_lst(self, pdbfilename):
		# Create lst file
		pdbfilename = self._workingdir_file_path("%(_FILE_ID)s.pdb" % self.parameters)
		filename = self._workingdir_file_path("%(_FILE_ID)s.lst" % self.parameters)
		F = open(filename, "w")
		F.write(pdbfilename)
		F.close()
		self.parameters['_CMD']['in:file:l'] = filename
		return filename

	def _write_resfile(self):
		"""create a resfile for the chains
			residues in interface: NATAA (conformation can be changed)
			residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
		
		resfile = self.parameters[ddgfields.InputFiles].get("RESFILE")
		if resfile:
			filename = self._workingdir_file_path("%(_FILE_ID)s.resfile" % self.parameters)
			F = open(filename, "w")
			F.write(resfile)
			F.close()
			self.parameters['_CMD']['resfile'] = filename
			return filename
		else:
			raise Exception("An error occurred creating a resfile for the ddG job.")

	def _analyze(self):
		# Run the analysis on the originating host
		
		try:
			Scores = {}
			
			ddGtask = self.ProtocolGraph["ddG"]["_task"] 
			ddGout = rosettahelper.readFileLines(ddGtask._workingdir_file_path(ddGtask.getExpectedOutputFileNames()[0]))
			self._status("examining ddg output:")
			ddGout = [l for l in ddGout if l.startswith("protocols.moves.ddGMover: mutate")]
			self._status(ddGout)
			assert(len(ddGout) == 1)
			ddGout = ddGout[0].strip()
			ddGregex = re.compile("^protocols.moves.ddGMover:\s*mutate\s*.*?\s*wildtype_dG\s*is:\s*.*?and\s*mutant_dG\s*is:\s*.*?\s*ddG\s*is:\s*(.*)$")
			mtchs = ddGregex.match(ddGout)
			assert(mtchs)
			Scores["ddG"] = float(mtchs.group(1))
			
			score_data = rosettahelper.readFileLines(ddGtask._workingdir_file_path("ddg_predictions.out"))
			score_data = [l for l in score_data if l.strip()]
			self._status("examining ddg_predictions.out:")
			assert(len(score_data) == 1) # Assuming only one line here
			score_data = score_data[0].split() 
			assert(len(score_data) > 2)
			assert(score_data[0] == "ddG:")
			scores = map(float, score_data[2:])
			Scores["components"] = scores
			
			self.ddG.setData(Scores)
			
			return True
		except Exception, e:
			errors = [str(e), traceback.format_exc()]
			self._status("<errors>\n\t<error>%s</error>\n</errors>" % join(errors,"</error>\n\t<error>"))
			return False

		return True
		#def parseResults(logfile, predictions_file):
		scoresHeader='''
	------------------------------------------------------------
	 Scores                       Weight   Raw Score Wghtd.Score
	------------------------------------------------------------'''
		scoresFooter = '''---------------------------------------------------'''
		
		F = open(logfile, "r")
		log = F.read()
		F.close()
		
		componentNames = []
		idx = log.find(scoresHeader)
		if idx:
			log = log[idx + len(scoresHeader):]
			idx = log.find(scoresFooter)
			if idx:
				log = log[:idx].strip()
				log = log.split("\n")
				for line in log:
					componentNames.append(line.strip().split()[0])
				componentNames.remove("atom_pair_constraint")
		
		F = open(predictions_file, "r")
		predictions = F.read().split('\n')
		F.close()
		results = {}
		for p in predictions:
			if p.strip():
				components = p.split()
				assert[components[0] == "ddG:"]
				mutation = components[1]
				score = components[2]
				components = components[3:]
				assert(len(components) == len(componentNames))
				results["Overall"] = score
				componentsd = {}
				for i in range(len(componentNames)):
					componentsd[componentNames[i]] = components[i]
				results["Components"] = componentsd
		return results

class ddGK16PreminTask(GenericDDGTask):

	def getOutputFilename(self, preminimizationLog):
		cmd = self.taskparameters["Command"]
		o = "-ddg::out_pdb_prefix"
		i = cmd.find(o)
		if i != -1: 
			prefix = cmd[i + len(o):].strip().split(" ")[0]
		
		if prefix:
			pdbfilepaths = []
			outputLines = rosettahelper.readFileLines(preminimizationLog)
			str = "examining file:"
			for line in outputLines: 
				if line.startswith(str):
					pdbfilepaths.append(line[len(str):].strip().split()[0])
			
			# todo: The following assumes that the lst file contains only one PDB file which will probably work better in practice w.r.t. running parallel jobs
			if pdbfilepaths:
				fdir, fname = os.path.split(pdbfilepaths[0])
				fname = fname.split(".")[0]
				return os.path.join(fdir, "%(prefix)s.%(fname)s_0001.pdb" % vars())
			else:
				raise Exception("Could not find the input PDB file paths in the log.")
		else:
			raise Exception("Could not determine the out_pdb_prefix of the command.")

	def createConstraintsFile(self, preminimizationLog, outfilepath):
		'''This does the work of convert_to_cst_file.sh'''
		self._status("Creating constraints file")
		constraints = []
		outputLines = rosettahelper.readFileLines(preminimizationLog)
		for line in outputLines: 
			if line.startswith("c-alpha"):
				line = line.split()
				constraints.append("AtomPair CA %s CA %s HARMONIC %s %s" % (line[5], line[7], line[9], line[12]))
		rosettahelper.writeFile(outfilepath, join(constraints, "\n"))

	def retire(self):
		passed = super(ddGK16PreminTask, self).retire()
		try:
			# todo: Expecting only one output file
			stdoutfile = self._workingdir_file_path(self.getExpectedOutputFileNames()[0])
			
			# Set the input PDB filename for the ddG step
			self.setOutput("in:file:s", self._workingdir_file_path(self.getOutputFilename(stdoutfile)), taskID = "ddG")
			
			# Create the constraints file
			cstfile = self._workingdir_file_path("constraints.cst")
			constraints = self.createConstraintsFile(stdoutfile, cstfile)
			self.setOutput("constraints::cst_file", cstfile, taskID = "ddG")
			self._status("Set outputs: %s" % self.outputs)
			# Check whether files were created (and write the total scores to a file)
			# Copy the files from the cluster submission host back to the originating host
			#self._status('Copying pdb, gz, and resfiles back')
			#self._copyFilesBackToHost(["*.pdb", "*.gz", "*.resfile"])
		except Exception, e:
			passed = False
			self.state = FAILED_TASK
			errors = [str(e), traceback.format_exc()]
			self._status("<errors>\n\t<error>%s</error>\n</errors>" % join(errors,"</error>\n\t<error>"))
		  
		return passed

class ddGK16ddGTask(GenericDDGTask):
	pass








### Test functions (not maintained)
def test(ProtocolGraph, InitialTasks, CommandParameters):
	from sge import SGEConnection, SGEXMLPrinter, ClusterException
	sgec = SGEConnection()
	netappRoot = "/netapp/home/klabqb3backrub/temp"
	cluster_temp = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/temp/cluster"
	dldir = "/clustertest/temp/ddG" 
	params = {
		"ID" : 1,
		"ExperimentID" : 10,
		"PDB_ID" : "AAAA",
		"%(ResidueMapping)s" % ddgfields : {},  
		"%(StrippedPDB)s" % ddgfields : "", 
		"%(InputFiles)s" % ddgfields : {"RESFILE" : " "}, 
		"%(CryptID)s" % ddgfields : "abcdtestrun", 
		"ProtocolID" % ddgfields : "Kellogg:10.1002/prot.22921:protocol16:32231",
		"Description" % ddgfields : "Protocol 16 from Kellogg, Leaver-Fay, and Baker",
		"ProtocolGraph" : ProtocolGraph,
		"InitialTasks" : InitialTasks,
		"CommandParameters" : CommandParameters,
	}	
	clusterjob = ddGK16Job(sgec, params, netappRoot, cluster_temp, dldir)
	print("done")
	sys.exit(0)
