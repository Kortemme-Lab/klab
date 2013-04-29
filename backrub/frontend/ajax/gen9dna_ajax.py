#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

#import cgi


#import json

#import serial
#ser = serial.Serial('/dev/ttyUSB0', 57600)
#ser.write("Hello, this is a command for value %s from slider id!\n" % (form["rating"]))      # write a string
#ser.close()

#F = open("/tmp/testfile.txt", "w")
#F.write(estr)
#F.close()

import cgi
import cgitb
import traceback
import simplejson as json
import sys
import os
import base64

F = open("/tmp/testfile.txt", "w")
gen9db = None

def return_json_null():
	F.write("\n***NULL RETURN\n")
	print 'Content-Type: application/json\n\n'
	print(json.dumps(None))
	sys.exit(0)

def return_html(html_list):
	F.write("\n***HTML RETURN\n")
	html = "\n".join(html_list)
	print 'Content-Type: text/html\n\n'
	print(html)
	F.write(html)
	#sys.exit(0)

def return_json_dict(d):
	F.write("\n***JSON RETURN\n")
	print 'Content-Type: application/json\n\n'
	print(json.dumps(d))
	F.write(str(d))
	
try:
	sys.path.insert(0, '../..')
	sys.path.insert(0, '..')
	
	import common.rosettadb as rosettadb
	
	from gen9api.gen9api import Gen9Interface, DesignInformation, DNAConstructInformation, DNASequenceList
	form = cgi.FieldStorage()
	
	from common.rosettahelper import WebsiteSettings
	settings = WebsiteSettings(sys.argv, os.environ['SCRIPT_NAME'])
	
	gen9Interface = Gen9Interface(username = 'oconchus', password = settings['SQLPassword'])
	gen9db = rosettadb.ReusableDatabaseInterface(settings, host = "kortemmelab.ucsf.edu", db = "Gen9Design")
	
	if form.has_key('request'):
		if form['request'].value == 'DNATranslation':
			
			success = False
			Translation = 'No DNA sequence specified'
			
			if form.has_key('Sequence'):
				sequence = form['Sequence'].value.strip().replace(" ", "").replace("\n", "")
				F.write("sequence\n")
				F.write(sequence)
				
				a_front = DNAConstructInformation.getAFrontSequence()
				a_back = DNAConstructInformation.getABackSequence()
				b_front = DNAConstructInformation.getBFrontSequence()
				b_back = DNAConstructInformation.getBBackSequence()
				
				if sequence.startswith(a_front) and sequence.endswith(a_back):
					 sequence = sequence[len(a_front):-len(a_back)]
				elif sequence.startswith(b_front) and sequence.endswith(b_back):
					 sequence = sequence[len(b_front):-len(b_back)]
				F.write("\ncropped sequence\n")
				F.write(sequence)
				
				try:
					F.write("\ntranslated sequence\n")
					F.write(DNASequenceList._translate(sequence))
					Translation = DNASequenceList._translate(sequence)
					success = True 
				except Exception, e:
					F.write(str(e))
					Translation = "The sequence could not be translated. Please make sure it is entered correctly."
				
				
			return_json_dict({'Translation' : Translation, 'Success': success})
			
		if form['request'].value == 'DesignDetails':
			if form.has_key('DesignID'):
				DesignID = form['DesignID'].value
				PlateID = None
				if form.has_key('PlateID'):
					PlateID = form['PlateID'].value
				results = gen9db.execute("SELECT * FROM ManualDesign WHERE DesignID=%s", parameters=(DesignID,))
				if results:
					assert(len(results) == 1)
					results = results[0]
					
					original_design_results = gen9db.execute("SELECT * FROM Design WHERE ID=%s", parameters=(results['OriginalDesignID']))
					assert(len(original_design_results) == 1)
					original_design_results = original_design_results[0]
					
					ManualDesignID = results['DesignID']
					ManualDesignDescription = results['MutationDescription']
					
					design_object = DesignInformation(gen9db, ManualDesignID)
					errors = []
					
					DNAPlates = design_object.getDNAPlates()
					if not(DNAPlates):
						errors.append("Can not assemble design %d. No DNA plates were found for the relevant constructs." % ManualDesignID)
					
					master_plate = 'plate10089' # may want to rethink whether we want this hardcoded in the future
					
					assembly_details = design_object.getSummaryInformationForAssembly([DNAPlates[0]])
					if len(assembly_details) != 2:
						assert(len(assembly_details) == 1)
						errors.append("Can not assemble design %d. Information available for %s only." % (ManualDesignID, ", ".join([dca['DNAChain.CloningType'] for dca in assembly_details])))
					
					html = []
					
					DNAChain_to_ProteinChain = {}
					DNAChain_to_Construct = {}
					DNAChain_to_WildTypeChain = {}
					
					translated_sequences = []
					translations = {}
					construct_map = design_object.getDNAConstructsFilteredByDNAPlate(["plate10089"])
					F.write("\n*** construct_map ***\n")
					F.write(str(construct_map))
					F.write("\n*** /construct_map ***\n")
					
					for k, constructs in construct_map.iteritems():
						for construct in constructs:
							#html += construct.toHTML()
							#html += "<br>"
							
							for DNAChain in design_object.DNAChains:
								
								chainIndex = construct.getChainIndex(DNAChain)
								if chainIndex != None:
									assert(translations.get(DNAChain.CloningType, None) == None)
									translation = construct.translate(chainIndex + 1)
									translations[DNAChain.CloningType] = translation
									
									design_object.FullComplexChains
									
									for chain_id, chain_details in design_object.Chains.iteritems():
										if len(chain_details['Sequence']) > 30 and translation.find(chain_details['Sequence'][7:-7]) != -1:
											assert(DNAChain.CloningType not in DNAChain_to_ProteinChain)
											assert(DNAChain.CloningType not in DNAChain_to_WildTypeChain)
											assert(DNAChain.CloningType not in DNAChain_to_Construct)
											
											DNAChain_to_ProteinChain[DNAChain.CloningType] = chain_id
											DNAChain_to_WildTypeChain[DNAChain.CloningType] = chain_details['WildTypeChain']
											DNAChain_to_Construct[DNAChain.CloningType] = construct
										elif len(chain_details['Sequence']) > 15 and translation.find(chain_details['Sequence'][2:-2]) != -1:
											assert(DNAChain.CloningType not in DNAChain_to_ProteinChain)
											assert(DNAChain.CloningType not in DNAChain_to_WildTypeChain)
											assert(DNAChain.CloningType not in DNAChain_to_Construct)
											
											DNAChain_to_ProteinChain[DNAChain.CloningType] = chain_id
											DNAChain_to_WildTypeChain[DNAChain.CloningType] = chain_details['WildTypeChain']
											DNAChain_to_Construct[DNAChain.CloningType] = construct
										elif len(chain_details['Sequence']) > 15 and translation.find(chain_details['Sequence'][2:8]) != -1 and translation.find(chain_details['Sequence'][-8:-2]) != -1:
											assert(DNAChain.CloningType not in DNAChain_to_ProteinChain)
											assert(DNAChain.CloningType not in DNAChain_to_WildTypeChain)
											assert(DNAChain.CloningType not in DNAChain_to_Construct)
											
											DNAChain_to_ProteinChain[DNAChain.CloningType] = chain_id
											DNAChain_to_WildTypeChain[DNAChain.CloningType] = chain_details['WildTypeChain']
											DNAChain_to_Construct[DNAChain.CloningType] = construct
					
					for chain_id, chain_details in design_object.Chains.iteritems():
						DNAChain_to_ProteinChain[DNAChain.CloningType] = DNAChain_to_ProteinChain.get(DNAChain.CloningType, None)
						DNAChain_to_WildTypeChain[DNAChain.CloningType] = DNAChain_to_WildTypeChain.get(DNAChain.CloningType, None)
						DNAChain_to_Construct[DNAChain.CloningType] = DNAChain_to_Construct.get(DNAChain.CloningType, None)
						
					assert(len(translations) == 2)
					assert(len(DNAChain_to_ProteinChain) == 2)
					assert(len(DNAChain_to_WildTypeChain) == 2)
					assert(len(DNAChain_to_Construct) == 2)
					
					html.append("<div>Description: %s%s</div>" % (ManualDesignDescription[0].upper(), ManualDesignDescription[1:]))
					html.append("<div><span>%s, Design <a style='color:#00a;' class='gen9well_dialog' target='Gen9Designs' href='http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py?query=Gen9#d%d'>#%d</a></span>" % (design_object.TargetSmallMolecule.ID, design_object.ID, design_object.ID))
					
					html.append("<div style='float:right;'>")
					if original_design_results['PyMOLSessionFile']:
						html.append('''<span  class='Gen9PyMOL-link'>PyMOL session for design <a onclick='getDesignPyMOLFile(%(ID)d); return false;' href=''><img width="18" height="18" src='../images/pse32o.png' alt='pdf'></a></span>''' % original_design_results)
					if original_design_results['ManualDesignsPyMOLSessionFile']:
						html.append('''<span style='margin-left: 30px' class='Gen9PyMOL-link'>PyMOL session for manual designs <a onclick='getManualDesignsPyMOLFile(%(ID)d); return false;' id='PSELink-%(ID)d' href=''><img width="18" height="18" src='../images/pse32o.png' alt='pdf'></a></span>''' % original_design_results)
					html.append('</div>')
					html.append('</div>')
					html.append("""<div>Wildtype scaffold: <a style='color:#00a;' class='gen9well_dialog' target='_blank' href='http://www.rcsb.org/pdb/explore.do?structureId=%s'>%s.%s</a></div><br>""" % (design_object.WildtypeScaffold.PDBFileID, design_object.WildtypeScaffold.PDBFileID, design_object.WildtypeScaffold.BiologicalUnit))
					
					html.append("""<div style='color:#a00'>NOTE: Master plate values below (base pair count, concentration, <i>etc.</i>) are for the entire construct in the master plate.</div>""")
					
					#html.append(design_object.)
					chain_html = {}
					for chain_info in design_object.getSummaryInformationForAssembly([master_plate]):
						sub_html = []
						cloning_type = chain_info['DNAChain'].CloningType
						assert(cloning_type == 'Chain1' or cloning_type == 'Chain2')
						StorageLocation = chain_info['StorageLocation']
						
						sub_html.append("<div>Location of %s in master(%s): %s%02d</div>" % (cloning_type, StorageLocation.DNAPlateID, StorageLocation.PlateRow, StorageLocation.PlateColumn))
						sub_html.append("<div>Master plate: Base pair count = %d, concentration: %0.2f ng/&#x3BC;l, volume = %0.2f &#x3BC;l, total yield = %0.2f ng</div>" % (StorageLocation.NumberOfBasePairs, StorageLocation.Concentration, StorageLocation.Volume, StorageLocation.TotalYield))
						
						if DNAChain_to_ProteinChain.get(cloning_type):
							
							sub_html.append("<div><b>Design PDB ATOM record protein sequence</b></div>")
							ATOM_sequence = design_object.Chains[DNAChain_to_ProteinChain[cloning_type]]['Sequence']
							sub_html.append("<div class='gen9well_dialog_chain_sequence'>")
							for sub_sequence in [ATOM_sequence[x:x+100] for x in xrange(0, len(ATOM_sequence), 100)]:
								sub_html.append("%s" % sub_sequence)
							sub_html.append("</div>")
									
						sub_html.append("<div><b>Protein sequence translated from DNA below</b></div>")
						sub_html.append("<div class='gen9well_dialog_chain_sequence'>")
						translation = translations[cloning_type]
						for sub_sequence in [translation[x:x+100] for x in xrange(0, len(translation), 100)]:
							sub_html.append("%s" % sub_sequence)
						sub_html.append("</div>")
						
						construct = DNAChain_to_Construct[cloning_type]
						substr = []
						if construct:
							bpcount = construct.getBasePairCount()
							for bp_chain_name, chain_bpcount in sorted(bpcount.iteritems()):
								if bp_chain_name != 'Total':
									substr.append("%d in %s" % (chain_bpcount, bp_chain_name))
							sub_html.append("<div><b>DNA construct #%d, #base pairs = %d total: %s</b></div>" % (construct.ID, bpcount['Total'], ", ".join(substr)))
						else:
							sub_html.append("<div><b>DNA construct</b></div>")

						sub_html.append("<div class='gen9well_dialog_chain_sequence'>")
						if DNAChain_to_Construct[cloning_type]:
							sub_html.append(DNAChain_to_Construct[cloning_type].toHTML(100, showonly=cloning_type))
						else:
							sub_html.append("Could not match the protein sequence with the translation from DNA.")
						sub_html.append("</div>")
						
						sub_html.append("<br>")
						chain_html[cloning_type] = sub_html
					
					
					for cloning_type, sub_html in sorted(chain_html.iteritems()):
						if cloning_type == "Chain%s" % str(PlateID):
							html.append("<div style='border:2px solid #008; margin-bottom:7px'>" )
						if DNAChain_to_ProteinChain.get(cloning_type):
							chain_results = gen9db.execute_select("SELECT * FROM PDBMoleculeChain INNER JOIN PDBMolecule ON PDBMoleculeChain.PDBFileID=PDBMolecule.PDBFileID AND PDBMoleculeChain.MoleculeID=PDBMolecule.MoleculeID WHERE Chain=%s AND PDBMoleculeChain.PDBFileID=%s", parameters=(DNAChain_to_WildTypeChain[cloning_type], design_object.WildtypeScaffold.PDBFileID,))
							if chain_results:
								assert(len(chain_results) == 1)
								F.write("chain_results %s" % str(chain_results))
								if chain_results[0]['Synonym']:
									div_title ="title='Wildtype chain is %s / %s from %s'" % (chain_results[0]['Name'], chain_results[0]['Synonym'], chain_results[0]['Organism']) 
									if len(chain_results[0]['Name']) + len(chain_results[0]['Synonym']) < 50:
										html.append("<div %s class='gen9well_dialog_chain_header'><b>%s, design chain %s (Wildtype chain is %s / %s from %s)</b></div>" % (div_title, cloning_type, DNAChain_to_ProteinChain[cloning_type], chain_results[0]['Name'], chain_results[0]['Synonym'], chain_results[0]['Organism']))
									else:
										html.append("<div %s class='gen9well_dialog_chain_header'><b>%s, design chain %s (Wildtype chain is %s from %s)</b></div>" % (div_title, cloning_type, DNAChain_to_ProteinChain[cloning_type], chain_results[0]['Name'], chain_results[0]['Organism']))
								else:
									div_title ="title='Wildtype chain is %s from %s'" % (chain_results[0]['Name'], chain_results[0]['Organism']) 
									html.append("<div %s class='gen9well_dialog_chain_header'><b>%s, design chain %s (Wildtype chain is %s from %s)</b></div>" % (div_title, cloning_type, DNAChain_to_ProteinChain[cloning_type], chain_results[0]['Name'], chain_results[0]['Organism']))
							else:
								html.append("<div class='gen9well_dialog_chain_header'><b>%s, design chain %s</b></div>" % (cloning_type, DNAChain_to_ProteinChain[cloning_type]))
						else:
							html.append("<div class='gen9well_dialog_chain_header'><b>%s</b></div>" % cloning_type)
						
						html.extend(sub_html)
						
						if cloning_type == "Chain%s" % str(PlateID):
							html.append("</div>")
						
					
					#construct = DNAConstructInformation(gen9db,45)
					#print(construct.toHTML())
					#print(construct.toColorTerminal())
			
					#chain_html.append()
					#print(sorted(design_object.FullComplexChains), sorted(translations.values()))
					
					
					return_html(html)
				
					
	
	else:
		return_json_null()
	
	F.close()
	
	gen9db.close()
	
except Exception, e:
	if gen9db:
		gen9db.close()
	#F = open("/tmp/testfile.txt", "w")
	F.write("\nEXCEPTION\n\n%s\n%s" % (str(e), traceback.format_exc()))
	if form:
		F.write("Form:")
		F.write(str(form))
	F.close()
	
if False:
	gen9db = None
	try:
		
		sys.path.insert(0, '../../common')
		import rosettadb
		form = cgi.FieldStorage()
		#estr = ""
		
		from rosettahelper import WebsiteSettings
		settings = WebsiteSettings(sys.argv, os.environ['SCRIPT_NAME'])
	
		gen9db = rosettadb.ReusableDatabaseInterface(settings, host = "kortemmelab.ucsf.edu", db = "Gen9Design")
		
		small_molecule = ''
		if form.has_key('small_molecule'):
			small_molecule = form['small_molecule'].value
			results = gen9db.execute("SELECT Diagram FROM SmallMolecule WHERE ID=%s", parameters=(small_molecule,))
			if results:
				contents = results[0]['Diagram']
		elif form.has_key('size'):
			contents = open('../../images/pse%s.png' % form['size'].value, 'rb').read()
		else:
			contents = open('../../images/pse320.png', 'rb').read()
		
	#print "Content-type: image/png\n\n"
	
	#print "Content-type: image/png"
	#print 'Content-Disposition: inline; filename="%s"' % ('pse320.png')
	#print "Content-Length: %d" % len(contents)
	#print
	#print(json.dumps({"average": '%d' % len(contents)}))
	#print(contents)
		print "Content-type: text/plain\n\n"
		print
		print(base64.b64encode(contents))
		F = open("/tmp/testfile.txt", "w")
		F.write("All okay")
		F.close()
		#sys.stdout.write(contents)
		#sys.stdout.flush()
		gen9db.close()
		
	except Exception, e:
		if gen9db:
			gen9db.close()
		F = open("/tmp/testfile.txt", "w")
		F.write(str(form))
		F.write("%s\n%s" % (str(e), traceback.format_exc()))
		F.close()
	
		#print "Content-type: application/json\n\n"
		#print
		#print(json.dumps({"average": 'error'}))

