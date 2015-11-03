import sys
sys.path.insert(0, "../..")
import traceback
import commands
import gc

from klab.bio.pdb import PDB
from klab.fs.fsio import read_file
from klab import colortext

from pdbml import PDBML, PDBML_slow
from uniprot import pdb_to_uniparc
from fasta import FASTA
from clustalo import SequenceAligner, PDBUniParcSequenceAligner
from sifts import SIFTS, MissingSIFTSRecord, BadSIFTSMapping, NoSIFTSPDBUniParcMapping
from relatrix import ResidueRelatrix
import time

rosetta_scripts_path = '~/Rosetta3.5/rosetta_source/build/src/release/linux/3.8/64/x86/gcc/4.7/default/rosetta_scripts.default.linuxgccrelease'
rosetta_database_path = '~/Rosetta3.5/rosetta_database/'

cache_dir = '/home/oconchus/temp'

class SpecificException(Exception): pass


#PDB_UniParc_SA = PDBUniParcSequenceAligner('3ZKB', cache_dir = '/home/oconchus/temp', cut_off = 80)


#PDB_UniParc_SA = PDBUniParcSequenceAligner('3ZKB', cache_dir = '/home/oconchus/temp', cut_off = 80)


def FASTA_alignment():
    # example for talk
    f = FASTA.retrieve('1YGV', cache_dir) + FASTA.retrieve('3HQV', cache_dir)
    sa = SequenceAligner.from_FASTA(f)
    print(sa)

def test_ddg_pdb_ids():

    # Test set - 845 PDB IDs. A small number required manual intervention but most are parsed and mapped automatically. 5 needed to use the SIFTS mappings.

    ddG_pdb_ids = ['107L','108L','109L','110L','111L','112L','113L','114L','115L','118L','119L','120L','122L','123L','125L','126L','127L','128L','129L','130L','131L','137L','149L','150L','151L','160L','161L','162L','163L','164L','165L','168L','169L','171L','172L','173L','190L','191L','192L','195L','196L','1A23','1A2I','1A2P','1A3Y','1A43','1A4Y','1A53','1A5E','1A70','1A7A','1A7H','1A7V','1AAL','1AAR','1AAZ','1ABE','1ACB','1ADO','1ADW','1AG2','1AG4','1AG6','1AIE','1AIN','1AJ3','1AJQ','1AKK','1AKM','1AM7','1AMQ','1ANF','1ANK','1ANT','1AO6','1AON','1AOZ','1APC','1APL','1APS','1AQH','1AR1','1ARR','1ATJ','1ATN','1AU1','1AUT','1AV1','1AVR','1AX1','1AXB','1AYE','1AYF','1AZP','1B0O','1B26','1B5M','1B8J','1BAH','1BAN','1BAO','1BCX','1BD8','1BET','1BF4','1BFM','1BGD','1BGL','1BJP','1BKE','1BKS','1BLC','1BMC','1BNI','1BNL','1BNS','1BNZ','1BOY','1BP2','1BPI','1BPL','1BPR','1BPT','1BRF','1BRG','1BRH','1BRI','1BRJ','1BRK','1BSA','1BSB','1BSC','1BSD','1BSE','1BSR','1BTA','1BTI','1BTM','1BUJ','1BVC','1BVU','1BZO','1C0L','1C17','1C2R','1C52','1C53','1C5G','1C6P','1C9O','1CAH','1CBW','1CDC','1CEA','1CEY','1CHK','1CHO','1CHP','1CLW','1CM7','1CMB','1CMS','1COA','1COK','1COL','1CPM','1CSP','1CTS','1CUN','1CUS','1CVW','1CX1','1CX8','1CYC','1CYO','1D0X','1D1G','1DAQ','1DDN','1DE3','1DEC','1DEQ','1DFO','1DFX','1DHN','1DIL','1DIV','1DJU','1DKG','1DKT','1DLC','1DM0','1DO9','1DPM','1DTD','1DTO','1DVC','1DVF','1DVV','1DXX','1DYA','1DYB','1DYC','1DYD','1DYE','1DYF','1DYG','1DYJ','1E21','1E6K','1E6L','1E6M','1E6N','1EDH','1EFC','1EG1','1EHK','1EKG','1EL1','1ELV','1EMV','1EQ1','1ERU','1ESF','1ETE','1EVQ','1EW4','1EXG','1EZA','1F88','1FAJ','1FAN','1FC1','1FEP','1FGA','1FKB','1FKJ','1FLV','1FMK','1FMM','1FNF','1FR2','1FRD','1FTG','1FTT','1FXA','1G6N','1G6V','1G6W','1GA0','1GAD','1GAL','1GAY','1GAZ','1GB0','1GB2','1GB3','1GB7','1GBX','1GD1','1GF8','1GF9','1GFA','1GFE','1GFG','1GFH','1GFJ','1GFK','1GFL','1GFR','1GFT','1GFU','1GFV','1GKG','1GLH','1GLM','1GOB','1GPC','1GQ2','1GRL','1GRX','1GSD','1GTM','1GTX','1GUY','1GXE','1H09','1H0C','1H2I','1H7M','1H8V','1HA4','1HCD','1HEM','1HEN','1HEO','1HEP','1HEQ','1HER','1HEV','1HFY','1HFZ','1HGH','1HGU','1HIB','1HIC','1HIO','1HIX','1HK0','1HME','1HML','1HNG','1HNL','1HOR','1HQK','1HTI','1HUE','1HXN','1HYN','1HYW','1HZ6','1I4N','1I5T','1IAR','1IC2','1IDS','1IFB','1IFC','1IGS','1IGV','1IHB','1IMQ','1INQ','1INU','1IO2','1IOB','1IOF','1IOJ','1IR3','1IRL','1IRO','1ISK','1IX0','1J0X','1J4S','1J7N','1JAE','1JBK','1JHN','1JIW','1JJI','1JKB','1JNK','1JTD','1JTG','1JTK','1K23','1K3B','1K40','1K9Q','1KA6','1KBP','1KDN','1KDU','1KDX','1KEV','1KFD','1KFW','1KJ1','1KKJ','1KTQ','1KUM','1KVA','1KVB','1KVC','1L00','1L02','1L03','1L04','1L05','1L06','1L07','1L08','1L09','1L10','1L11','1L12','1L13','1L14','1L15','1L16','1L17','1L18','1L19','1L20','1L21','1L22','1L23','1L24','1L33','1L34','1L36','1L37','1L38','1L40','1L41','1L42','1L43','1L44','1L45','1L46','1L47','1L48','1L49','1L50','1L51','1L52','1L53','1L54','1L55','1L56','1L57','1L59','1L60','1L61','1L62','1L63','1L65','1L66','1L67','1L68','1L69','1L70','1L71','1L72','1L73','1L74','1L75','1L76','1L77','1L85','1L86','1L87','1L88','1L89','1L90','1L91','1L92','1L93','1L94','1L95','1L96','1L97','1L98','1L99','1LAV','1LAW','1LBI','1LFO','1LHH','1LHI','1LHJ','1LHK','1LHL','1LHM','1LHP','1LLI','1LMB','1LOZ','1LPS','1LRA','1LRE','1LRP','1LS4','1LSN','1LUC','1LVE','1LYE','1LYF','1LYG','1LYH','1LYI','1LYJ','1LZ1','1M7T','1MAX','1MBD','1MBG','1MCP','1MGR','1MJC','1MLD','1MSI','1MUL','1MX2','1MX4','1MX6','1MYK','1MYL','1N02','1N0J','1NAG','1NM1','1NZI','1OA2','1OA3','1OCC','1OH0','1OIA','1OKI','1OLR','1OMU','1ONC','1OPD','1ORC','1OSA','1OSI','1OTR','1OUA','1OUB','1OUC','1OUD','1OUE','1OUF','1OUG','1OUH','1OUI','1OUJ','1OVA','1P2M','1P2N','1P2O','1P2P','1P2Q','1P3J','1PAH','1PBA','1PCA','1PDO','1PGA','1PHP','1PII','1PIN','1PK2','1PMC','1POH','1PPI','1PPN','1PPP','1PQN','1PRE','1PRR','1Q5Y','1QEZ','1QGV','1QHE','1QJP','1QK1','1QLP','1QLX','1QM4','1QND','1QQR','1QQV','1QT6','1QT7','1QU0','1QU7','1QUW','1R2R','1RBN','1RBP','1RBR','1RBT','1RBU','1RBV','1RCB','1RDA','1RDB','1RDC','1REX','1RGC','1RGG','1RH1','1RHD','1RHG','1RIL','1RIS','1RN1','1ROP','1RRO','1RTB','1RTP','1RX4','1S0W','1SAK','1SAP','1SCE','1SEE','1SFP','1SHF','1SHG','1SHK','1SMD','1SPD','1SPH','1SSO','1STF','1STN','1SUP','1SYC','1SYD','1SYE','1SYG','1T3A','1T7C','1T8L','1T8M','1T8N','1T8O','1TBR','1TCA','1TCY','1TEN','1TFE','1TGN','1THQ','1TI5','1TIN','1TIT','1TLA','1TML','1TMY','1TOF','1TPE','1TPK','1TTG','1TUP','1TUR','1U5P','1UBQ','1UCU','1UOX','1URK','1UW3','1UWO','1UZC','1V6S','1VAR','1VFB','1VIE','1VQA','1VQB','1VQC','1VQD','1VQE','1VQF','1VQG','1VQH','1VQI','1VQJ','1W3D','1W4E','1W4H','1W99','1WIT','1WLG','1WPW','1WQ5','1WQM','1WQN','1WQO','1WQP','1WQQ','1WQR','1WRP','1WSY','1XAS','1XY1','1Y4Y','1Y51','1YAL','1YAM','1YAN','1YAO','1YAP','1YAQ','1YCC','1YEA','1YGV','1YHB','1YMB','1YNR','1YPA','1YPB','1YPC','1YPI','1Z1I','1ZNJ','200L','206L','216L','217L','219L','221L','224L','227L','230L','232L','233L','235L','236L','237L','238L','239L','240L','241L','242L','243L','244L','246L','247L','253L','254L','255L','2A01','2A36','2ABD','2AC0','2ACE','2ACY','2ADA','2AFG','2AIT','2AKY','2ASI','2ATC','2B4Z','2BBM','2BQA','2BQB','2BQC','2BQD','2BQE','2BQF','2BQG','2BQH','2BQI','2BQJ','2BQK','2BQM','2BQN','2BQO','2BRD','2CBR','2CHF','2CI2','2CPP','2CRK','2CRO','2DQJ','2DRI','2EQL','2FAL','2FHA','2FX5','2G3P','2GA5','2GSR','2GZI','2HEA','2HEB','2HEC','2HED','2HEE','2HEF','2HIP','2HMB','2HPR','2IFB','2IMM','2L3Y','2L78','2LZM','2MBP','2MLT','2NUL','2OCJ','2PDD','2PEC','2PEL','2PRD','2Q98','2RBI','2RN2','2RN4','2SNM','2SOD','2TMA','2TRT','2TRX','2TS1','2WSY','2ZAJ','2ZTA','3BCI','3BCK','3BD2','3BLS','3CHY','3D2A','3ECA','3FIS','3HHR','3K0NA_lin','3K0NB_lin','3K0On_lin','3MBP','3PGK','3PRO','3PSG','3SSI','3TIM','3VUB','451C','487D','4BLM','4CPA','4GCR','4LYZ','4SGB','4TLN','4TMS','5AZU','5CPV','5CRO','5MDH','5PEP','6TAA','7AHL','7PTI','8PTI','8TIM','9INS','9PCY',]
    print(len(ddG_pdb_ids))
    fix_later = set([
        # SELECT * FROM `Experiment` WHERE `PDBFileID` IN ('1OLR')
        # SELECT * FROM `DataSetDDG` WHERE `PDBFileID` IN ('1OLR')
        # SELECT * FROM `UserDataSetExperiment` WHERE `PDBFileID` IN ('1OLR')
        # SELECT * FROM `UserAnalysisSet` WHERE `PDB_ID` IN ('1OLR')
        ])

    failed_cases = []

    specific_cut_offs = {
        '1AR1' : (78, 76, 73.00), # Chain C has a Clustal Omega match at 77%
        '1BF4' : (80, 77, 87.00), # Chain A has a Clustal Omega match at 79%
        '1MCP' : (100, 98, 50.00), # Chain H has a Clustal Omega match at 100% but only half the chain
        '2ZAJ' : (75, 72, 70.00), #
        '1CPM' : (73, 71, 70.00), #
    }

    to_be_hardcoded = {
        # Special case: 1N02. This needs to be handled manually.
        # DBREF  1N02 A    1     3  UNP    P81180   CVN_NOSEL        1      3
        # DBREF  1N02 A    4    49  UNP    P81180   CVN_NOSEL       54     992IMM
        # DBREF  1N02 A   50    54  UNP    P81180   CVN_NOSEL       49     53
        # DBREF  1N02 A   55    99  UNP    P81180   CVN_NOSEL        4     48
        # DBREF  1N02 A  100   101  UNP    P81180   CVN_NOSEL      100    101
        '1N02',
        ('2IMM'), # No PDB <-> UniProt mapping
    }
    test_these = [
        '1KJ1'
    ]

    colortext.message('Testing %d PDB files for the DDG database.' % len(ddG_pdb_ids))
    #start_x = 0
    start_x = 0

    for x in range(start_x, len(ddG_pdb_ids)):
        ddG_pdb_id = ddG_pdb_ids[x]
        if test_these and ddG_pdb_id not in test_these:
            continue
        if ddG_pdb_id not in fix_later:
            colortext.warning('Testing PDB file number %d: %s' % (x, ddG_pdb_id))
            starting_clustal_cut_off = 100
            min_clustal_cut_off = 71
            acceptable_sequence_percentage_match = 80.0
            if specific_cut_offs.get(ddG_pdb_id):
                starting_clustal_cut_off, min_clustal_cut_off, acceptable_sequence_percentage_match = specific_cut_offs[ddG_pdb_id]
            try:
                rr = ResidueRelatrix(ddG_pdb_id, rosetta_scripts_path, rosetta_database_path, starting_clustal_cut_off = starting_clustal_cut_off, min_clustal_cut_off = min_clustal_cut_off, acceptable_sequence_percentage_match = acceptable_sequence_percentage_match, cache_dir = '/home/oconchus/temp')

            except SpecificException:
                failed_cases.append((x, ddG_pdb_id, str(e)))
        else:
            colortext.warning('SKIPPING PDB file number %d: %s' % (x, ddG_pdb_id))

        if failed_cases:
            colortext.error('Failed cases:')
            fcc = 0
            for f in failed_cases:
                if fcc == 0:
                    colortext.warning(str(f))
                else:
                    colortext.printf(str(f), color = 'cyan')
                fcc = (fcc + 1) % 2


    print("failed_cases", failed_cases)

test_ddg_pdb_ids()
sys.exit(0)

sifts_map = SIFTS.retrieve('1DEQ', cache_dir = cache_dir)
print(sifts_map.atom_to_uniparc_sequence_maps['D'])
print('--')
print(sifts_map.atom_to_seqres_sequence_maps['D'])
print('--')
print(sifts_map.seqres_to_uniparc_sequence_maps['D'])

sys.exit(0)
test_ddg_pdb_ids()
sys.exit(0)

def test_sifts_module():
    failures = []
    ddG_pdb_ids = ['107L','108L','109L','110L','111L','112L','113L','114L','115L','118L','119L','120L','122L','123L','125L','126L','127L','128L','129L','130L','131L','137L','149L','150L','151L','160L','161L','162L','163L','164L','165L','168L','169L','171L','172L','173L','190L','191L','192L','195L','196L','1A23','1A2I','1A2P','1A3Y','1A43','1A4Y','1A53','1A5E','1A70','1A7A','1A7H','1A7V','1AAL','1AAR','1AAZ','1ABE','1ACB','1ADO','1ADW','1AG2','1AG4','1AG6','1AIE','1AIN','1AJ3','1AJQ','1AKK','1AKM','1AM7','1AMQ','1ANF','1ANK','1ANT','1AO6','1AON','1AOZ','1APC','1APL','1APS','1AQH','1AR1','1ARR','1ATJ','1ATN','1AU1','1AUT','1AV1','1AVR','1AX1','1AXB','1AYE','1AYF','1AZP','1B0O','1B26','1B5M','1B8J','1BAH','1BAN','1BAO','1BCX','1BD8','1BET','1BF4','1BFM','1BGD','1BGL','1BJP','1BKE','1BKS','1BLC','1BMC','1BNI','1BNL','1BNS','1BNZ','1BOY','1BP2','1BPI','1BPL','1BPR','1BPT','1BRF','1BRG','1BRH','1BRI','1BRJ','1BRK','1BSA','1BSB','1BSC','1BSD','1BSE','1BSR','1BTA','1BTI','1BTM','1BUJ','1BVC','1BVU','1BZO','1C0L','1C17','1C2R','1C52','1C53','1C5G','1C6P','1C9O','1CAH','1CBW','1CDC','1CEA','1CEY','1CHK','1CHO','1CHP','1CLW','1CM7','1CMB','1CMS','1COA','1COK','1COL','1CPM','1CSP','1CTS','1CUN','1CUS','1CVW','1CX1','1CX8','1CYC','1CYO','1D0X','1D1G','1DAQ','1DDN','1DE3','1DEC','1DEQ','1DFO','1DFX','1DHN','1DIL','1DIV','1DJU','1DKG','1DKT','1DLC','1DM0','1DO9','1DPM','1DTD','1DTO','1DVC','1DVF','1DVV','1DXX','1DYA','1DYB','1DYC','1DYD','1DYE','1DYF','1DYG','1DYJ','1E21','1E6K','1E6L','1E6M','1E6N','1EDH','1EFC','1EG1','1EHK','1EKG','1EL1','1ELV','1EMV','1EQ1','1ERU','1ESF','1ETE','1EVQ','1EW4','1EXG','1EZA','1F88','1FAJ','1FAN','1FC1','1FEP','1FGA','1FKB','1FKJ','1FLV','1FMK','1FMM','1FNF','1FR2','1FRD','1FTG','1FTT','1FXA','1G6N','1G6V','1G6W','1GA0','1GAD','1GAL','1GAY','1GAZ','1GB0','1GB2','1GB3','1GB7','1GBX','1GD1','1GF8','1GF9','1GFA','1GFE','1GFG','1GFH','1GFJ','1GFK','1GFL','1GFR','1GFT','1GFU','1GFV','1GKG','1GLH','1GLM','1GOB','1GPC','1GQ2','1GRL','1GRX','1GSD','1GTM','1GTX','1GUY','1GXE','1H09','1H0C','1H2I','1H7M','1H8V','1HA4','1HCD','1HEM','1HEN','1HEO','1HEP','1HEQ','1HER','1HEV','1HFY','1HFZ','1HGH','1HGU','1HIB','1HIC','1HIO','1HIX','1HK0','1HME','1HML','1HNG','1HNL','1HOR','1HQK','1HTI','1HUE','1HXN','1HYN','1HYW','1HZ6','1I4N','1I5T','1IAR','1IC2','1IDS','1IFB','1IFC','1IGS','1IGV','1IHB','1IMQ','1INQ','1INU','1IO2','1IOB','1IOF','1IOJ','1IR3','1IRL','1IRO','1ISK','1IX0','1J0X','1J4S','1J7N','1JAE','1JBK','1JHN','1JIW','1JJI','1JKB','1JNK','1JTD','1JTG','1JTK','1K23','1K3B','1K40','1K9Q','1KA6','1KBP','1KDN','1KDU','1KDX','1KEV','1KFD','1KFW','1KJ1','1KKJ','1KTQ','1KUM','1KVA','1KVB','1KVC','1L00','1L02','1L03','1L04','1L05','1L06','1L07','1L08','1L09','1L10','1L11','1L12','1L13','1L14','1L15','1L16','1L17','1L18','1L19','1L20','1L21','1L22','1L23','1L24','1L33','1L34','1L36','1L37','1L38','1L40','1L41','1L42','1L43','1L44','1L45','1L46','1L47','1L48','1L49','1L50','1L51','1L52','1L53','1L54','1L55','1L56','1L57','1L59','1L60','1L61','1L62','1L63','1L65','1L66','1L67','1L68','1L69','1L70','1L71','1L72','1L73','1L74','1L75','1L76','1L77','1L85','1L86','1L87','1L88','1L89','1L90','1L91','1L92','1L93','1L94','1L95','1L96','1L97','1L98','1L99','1LAV','1LAW','1LBI','1LFO','1LHH','1LHI','1LHJ','1LHK','1LHL','1LHM','1LHP','1LLI','1LMB','1LOZ','1LPS','1LRA','1LRE','1LRP','1LS4','1LSN','1LUC','1LVE','1LYE','1LYF','1LYG','1LYH','1LYI','1LYJ','1LZ1','1M7T','1MAX','1MBD','1MBG','1MCP','1MGR','1MJC','1MLD','1MSI','1MUL','1MX2','1MX4','1MX6','1MYK','1MYL','1N02','1N0J','1NAG','1NM1','1NZI','1OA2','1OA3','1OCC','1OH0','1OIA','1OKI','1OLR','1OMU','1ONC','1OPD','1ORC','1OSA','1OSI','1OTR','1OUA','1OUB','1OUC','1OUD','1OUE','1OUF','1OUG','1OUH','1OUI','1OUJ','1OVA','1P2M','1P2N','1P2O','1P2P','1P2Q','1P3J','1PAH','1PBA','1PCA','1PDO','1PGA','1PHP','1PII','1PIN','1PK2','1PMC','1POH','1PPI','1PPN','1PPP','1PQN','1PRE','1PRR','1Q5Y','1QEZ','1QGV','1QHE','1QJP','1QK1','1QLP','1QLX','1QM4','1QND','1QQR','1QQV','1QT6','1QT7','1QU0','1QU7','1QUW','1R2R','1RBN','1RBP','1RBR','1RBT','1RBU','1RBV','1RCB','1RDA','1RDB','1RDC','1REX','1RGC','1RGG','1RH1','1RHD','1RHG','1RIL','1RIS','1RN1','1ROP','1RRO','1RTB','1RTP','1RX4','1S0W','1SAK','1SAP','1SCE','1SEE','1SFP','1SHF','1SHG','1SHK','1SMD','1SPD','1SPH','1SSO','1STF','1STN','1SUP','1SYC','1SYD','1SYE','1SYG','1T3A','1T7C','1T8L','1T8M','1T8N','1T8O','1TBR','1TCA','1TCY','1TEN','1TFE','1TGN','1THQ','1TI5','1TIN','1TIT','1TLA','1TML','1TMY','1TOF','1TPE','1TPK','1TTG','1TUP','1TUR','1U5P','1UBQ','1UCU','1UOX','1URK','1UW3','1UWO','1UZC','1V6S','1VAR','1VFB','1VIE','1VQA','1VQB','1VQC','1VQD','1VQE','1VQF','1VQG','1VQH','1VQI','1VQJ','1W3D','1W4E','1W4H','1W99','1WIT','1WLG','1WPW','1WQ5','1WQM','1WQN','1WQO','1WQP','1WQQ','1WQR','1WRP','1WSY','1XAS','1XY1','1Y4Y','1Y51','1YAL','1YAM','1YAN','1YAO','1YAP','1YAQ','1YCC','1YEA','1YGV','1YHB','1YMB','1YNR','1YPA','1YPB','1YPC','1YPI','1Z1I','1ZNJ','200L','206L','216L','217L','219L','221L','224L','227L','230L','232L','233L','235L','236L','237L','238L','239L','240L','241L','242L','243L','244L','246L','247L','253L','254L','255L','2A01','2A36','2ABD','2AC0','2ACE','2ACY','2ADA','2AFG','2AIT','2AKY','2ASI','2ATC','2B4Z','2BBM','2BQA','2BQB','2BQC','2BQD','2BQE','2BQF','2BQG','2BQH','2BQI','2BQJ','2BQK','2BQM','2BQN','2BQO','2BRD','2CBR','2CHF','2CI2','2CPP','2CRK','2CRO','2DQJ','2DRI','2EQL','2FAL','2FHA','2FX5','2G3P','2GA5','2GSR','2GZI','2HEA','2HEB','2HEC','2HED','2HEE','2HEF','2HIP','2HMB','2HPR','2IFB','2IMM','2L3Y','2L78','2LZM','2MBP','2MLT','2NUL','2OCJ','2PDD','2PEC','2PEL','2PRD','2Q98','2RBI','2RN2','2RN4','2SNM','2SOD','2TMA','2TRT','2TRX','2TS1','2WSY','2ZAJ','2ZTA','3BCI','3BCK','3BD2','3BLS','3CHY','3D2A','3ECA','3FIS','3HHR','3MBP','3PGK','3PRO','3PSG','3SSI','3TIM','3VUB','451C','487D','4BLM','4CPA','4GCR','4LYZ','4SGB','4TLN','4TMS','5AZU','5CPV','5CRO','5MDH','5PEP','6TAA','7AHL','7PTI','8PTI','8TIM','9INS','9PCY',]
    for no_xml_case in ['1GTX', '1SEE', '1UOX', '1WSY', '1YGV', '2MBP']:
        ddG_pdb_ids.remove(no_xml_case)
    for bad_sifts_mapping_case in ['1N02', '487D']:
        ddG_pdb_ids.remove(bad_sifts_mapping_case)
    for no_pdb_uniprot_mapping_case in ['2IMM']:
        ddG_pdb_ids.remove(no_pdb_uniprot_mapping_case)

    ddG_pdb_ids = ['1GTX', '1SEE', '1UOX', '1WSY', '1YGV', '2MBP']
    ddG_pdb_ids = ['1N02', '487D'] + ['2IMM']

    count = 1
    num_cases = len(ddG_pdb_ids)
    for pdb_id in ddG_pdb_ids:
        try:
            print('Case %d/%d: %s' % (count, num_cases, pdb_id))
            sifts_map = SIFTS.retrieve(pdb_id, cache_dir = cache_dir, acceptable_sequence_percentage_match = 80.0)
        except MissingSIFTSRecord:
            colortext.warning('No SIFTS XML exists for %s.' % pdb_id)
        except BadSIFTSMapping:
            colortext.warning('The SIFTS mapping for %s was considered a bad mapping at the time of writing.' % pdb_id)
        except NoSIFTSPDBUniParcMapping:
            colortext.warning('The SIFTS file for %s does not map to UniParc sequences at the time of writing.' % pdb_id)
        except Exception, e:
            colortext.warning(str(e))
            colortext.error(traceback.format_exc())
            failures.append(pdb_id)
        count += 1
    if failures:
        colortext.error('Failures: %d/%d' % (len(failures), num_cases))
        for f in failures:
            colortext.warning(f)

def test_pdbml_speed():

    test_cases = [
        '1WSY',
        '1YGV',
        '487D',
        '1HIO',
        '1H38',
        '3ZKB',
    ]
    for test_case in test_cases:
        print("\n")

        colortext.message("Creating PDBML object for %s" % test_case)
        #PDBML.retrieve(test_case, cache_dir = cache_dir)

        print("")
        colortext.printf("Using the old minidom class", color = 'cyan')
        t1 = time.clock()
        p_minidom = PDBML_slow.retrieve(test_case, cache_dir = cache_dir)
        t2 = time.clock()
        colortext.message("Done in %0.2fs!" % (t2 - t1))

        print("")
        colortext.printf("Using the new sax class", color = 'cyan')
        t1 = time.clock()
        p_sax = PDBML.retrieve(test_case, cache_dir = cache_dir)
        t2 = time.clock()
        colortext.message("Done in %0.2fs!" % (t2 - t1))

        colortext.write("\nEquality test: ", color = 'cyan')
        try:
            assert(p_minidom.atom_to_seqres_sequence_maps.keys() == p_sax.atom_to_seqres_sequence_maps.keys())
            for c, s_1 in p_minidom.atom_to_seqres_sequence_maps.iteritems():
                s_2 = p_sax.atom_to_seqres_sequence_maps[c]
                assert(str(s_1) == str(s_2))
            colortext.message("passed\n")
        except:
            colortext.error("failed\n")

def test_ResidueRelatrix_1LRP():
    # This case has no Rosetta residues as only CA atoms exist in the PDB and the features database script would crashes. This is a test that the case is handled gracefully.

    rr = ResidueRelatrix('1LRP', rosetta_scripts_path, rosetta_database_path, min_clustal_cut_off = 80, cache_dir = '/home/oconchus/temp')

    atom_id_1 = 'C  89 '
    chain_id = atom_id_1[0]

    # Single jumps forward
    seqres_id_1 = rr.convert(chain_id, atom_id_1, 'atom', 'seqres')
    uniparc_id_1 = rr.convert(chain_id, seqres_id_1, 'seqres', 'uniparc')

    # Double jumps forward
    uniparc_id_2 = rr.convert(chain_id, atom_id_1, 'atom', 'uniparc')

    # Single jumps backward
    seqres_id_2 = rr.convert(chain_id, uniparc_id_1, 'uniparc', 'seqres')
    atom_id_2 = rr.convert(chain_id, seqres_id_1, 'seqres', 'atom')

    # Double/triple jumps backward
    atom_id_3 = rr.convert(chain_id, uniparc_id_1, 'uniparc', 'atom')


    assert(atom_id_1 == atom_id_2 and atom_id_2 == atom_id_3)
    assert(seqres_id_1 == seqres_id_2)
    assert(uniparc_id_1 == uniparc_id_2)


def test_ResidueRelatrix_104L():
    # Rosetta residue 45 -> 'A  44A' is an insertion residue which does not appear in the UniParc sequence

    rr = ResidueRelatrix('104L', rosetta_scripts_path, rosetta_database_path, min_clustal_cut_off = 80, cache_dir = '/home/oconchus/temp')
    rosetta_id_1 = 45

    # Single jumps forward
    atom_id_1 = rr.convert('A', rosetta_id_1, 'rosetta', 'atom')
    seqres_id_1 = rr.convert('A', atom_id_1, 'atom', 'seqres')
    uniparc_id_1 = rr.convert('A', seqres_id_1, 'seqres', 'uniparc')

    # Double/triple jumps forward
    seqres_id_2 = rr.convert('A', rosetta_id_1, 'rosetta', 'seqres')
    uniparc_id_2 = rr.convert('A', rosetta_id_1, 'rosetta', 'uniparc')

    # Double jumps forward
    uniparc_id_3 = rr.convert('A', atom_id_1, 'atom', 'uniparc')

    # Single jumps backward
    seqres_id_3 = rr.convert('A', uniparc_id_1, 'uniparc', 'seqres')
    atom_id_2 = rr.convert('A', seqres_id_2, 'seqres', 'atom')
    rosetta_id_2 = rr.convert('A', atom_id_2, 'atom', 'rosetta')

    # Double/triple jumps backward
    atom_id_3 = rr.convert('A', uniparc_id_1, 'uniparc', 'atom')
    rosetta_id_3 = rr.convert('A', uniparc_id_1, 'uniparc', 'rosetta')

    rosetta_id_4 = rr.convert('A', seqres_id_2, 'seqres', 'rosetta')

    assert(rosetta_id_1 == rosetta_id_2 and rosetta_id_2 == rosetta_id_4)
    assert(rosetta_id_3 == None)
    assert(atom_id_1 == atom_id_2)
    assert(atom_id_3 == None)
    assert(seqres_id_1 == seqres_id_2)
    assert(seqres_id_3 == None)
    assert(uniparc_id_1 == uniparc_id_2 and uniparc_id_2 == uniparc_id_3)

def test_ResidueRelatrix_1A2C():
    # Rosetta residue 45 -> 'A  44A' is an insertion residue which does not appear in the UniParc sequence

    rr = ResidueRelatrix('1A2C', rosetta_scripts_path, rosetta_database_path, min_clustal_cut_off = 80, cache_dir = '/home/oconchus/temp', starting_clustal_cut_off = 82)
    rosetta_id_1 = 157

    chain_id = rr.convert_from_rosetta(rosetta_id_1, 'atom')[0]

    # Single jumps forward

    atom_id_1 = rr.convert(chain_id, rosetta_id_1, 'rosetta', 'atom')
    assert(atom_id_1 == 'H 124 ')
    seqres_id_1 = rr.convert(chain_id, atom_id_1, 'atom', 'seqres')
    assert(seqres_id_1== 121)
    uniparc_id_1 = rr.convert(chain_id, seqres_id_1, 'seqres', 'uniparc')
    assert(uniparc_id_1 == (u'UPI0000136ECD', 484))

    # Double/triple jumps forward
    seqres_id_2 = rr.convert(chain_id, rosetta_id_1, 'rosetta', 'seqres')
    uniparc_id_2 = rr.convert(chain_id, rosetta_id_1, 'rosetta', 'uniparc')

    # Double jumps forward
    uniparc_id_3 = rr.convert(chain_id, atom_id_1, 'atom', 'uniparc')

    # Single jumps backward
    seqres_id_3 = rr.convert(chain_id, uniparc_id_1, 'uniparc', 'seqres')
    atom_id_2 = rr.convert(chain_id, seqres_id_2, 'seqres', 'atom')
    rosetta_id_2 = rr.convert(chain_id, atom_id_2, 'atom', 'rosetta')

    # Double/triple jumps backward
    atom_id_3 = rr.convert(chain_id, uniparc_id_1, 'uniparc', 'atom')
    rosetta_id_3 = rr.convert(chain_id, uniparc_id_1, 'uniparc', 'rosetta')

    rosetta_id_4 = rr.convert(chain_id, seqres_id_2, 'seqres', 'rosetta')

    assert(rosetta_id_1 == rosetta_id_2 and rosetta_id_2 == rosetta_id_3 and rosetta_id_3 == rosetta_id_4)
    assert(atom_id_1 == atom_id_2 and atom_id_2 == atom_id_3)
    assert(seqres_id_1 == seqres_id_2 and seqres_id_2 == seqres_id_3)
    assert(uniparc_id_1 == uniparc_id_2 and uniparc_id_2 == uniparc_id_3)

def test_ResidueRelatrix_1A2P():
    rr = ResidueRelatrix('1A2P', rosetta_scripts_path, rosetta_database_path, min_clustal_cut_off = 80, cache_dir = '/home/oconchus/temp')

    rosetta_id_1 = 79

    # Single jumps forward
    assert(rosetta_id_1 == 79)
    atom_id_1 = rr.convert('A', rosetta_id_1, 'rosetta', 'atom')
    assert(atom_id_1 == 'A  81 ')
    seqres_id_1 = rr.convert('A', atom_id_1, 'atom', 'seqres')
    assert(seqres_id_1 == 81)
    uniparc_id_1 = rr.convert('A', seqres_id_1, 'seqres', 'uniparc')
    assert(uniparc_id_1 == (u'UPI000013432A', 128))

    # Double/triple jumps forward
    seqres_id_2 = rr.convert('A', rosetta_id_1, 'rosetta', 'seqres')
    assert(seqres_id_2 == 81)
    uniparc_id_2 = rr.convert('A', rosetta_id_1, 'rosetta', 'uniparc')
    assert(uniparc_id_2 == (u'UPI000013432A', 128))

    # Double jumps forward
    uniparc_id_3 = rr.convert('A', atom_id_1, 'atom', 'uniparc')
    assert(uniparc_id_3 == (u'UPI000013432A', 128))


    # Single jumps backward
    seqres_id_3 = rr.convert('A', uniparc_id_1, 'uniparc', 'seqres')
    assert(seqres_id_3 == 81)
    atom_id_2 = rr.convert('A', seqres_id_3, 'seqres', 'atom')
    assert(atom_id_2 == 'A  81 ')
    rosetta_id_2 = rr.convert('A', atom_id_2, 'atom', 'rosetta')
    assert(rosetta_id_2 == 79)

    # Double/triple jumps backward
    atom_id_3 = rr.convert('A', uniparc_id_1, 'uniparc', 'atom')
    assert(atom_id_3 == 'A  81 ')
    rosetta_id_3 = rr.convert('A', uniparc_id_1, 'uniparc', 'rosetta')
    assert(rosetta_id_3 == 79)

    rosetta_id_4 = rr.convert('A', seqres_id_3, 'seqres', 'rosetta')
    assert(rosetta_id_4 == 79)

    assert(rosetta_id_1 == rosetta_id_2 and rosetta_id_2 == rosetta_id_3 and rosetta_id_3 == rosetta_id_4)
    assert(atom_id_1 == atom_id_2 and atom_id_2 == atom_id_3)
    assert(seqres_id_1 == seqres_id_2 and seqres_id_2 == seqres_id_3)
    assert(uniparc_id_1 == uniparc_id_2 and uniparc_id_2 == uniparc_id_3)

    # Rosetta residue   3 maps to 'A   5 '
    #print(rr.rosetta_to_atom_sequence_maps)
    assert(rr.convert_from_rosetta(3, 'atom') == 'A   5 ')
    assert(rr.convert_from_rosetta(3, 'seqres') == 5)
    assert(rr.convert_from_rosetta(3, 'uniparc') == (u'UPI000013432A', 52))

    # Rosetta residue 159 maps to 'B  54 '
    # Rosetta residue 248 maps to 'C  35 '

test_ResidueRelatrix_1A2P()
test_ResidueRelatrix_104L()
test_ResidueRelatrix_1A2C()
test_ResidueRelatrix_1LRP()

sys.exit(0)
sifts_map = SIFTS.retrieve('1KJ1', cache_dir = cache_dir)
#sifts_map = SIFTS.retrieve('1M7T', cache_dir = cache_dir)
for c, m in sorted(sifts_map.atom_to_uniparc_sequence_maps.iteritems()):
    colortext.message(c)
    print(m)
    print(sifts_map.atom_to_seqres_sequence_maps[c])
    print(sifts_map.seqres_to_uniparc_sequence_maps[c])

#test_ddg_pdb_ids()

sys.exit(0)
print(sifts_map.atom_to_uniparc_sequence_map)

sifts_map = SIFTS.retrieve('1H38', cache_dir = cache_dir)
print(sifts_map.atom_to_uniparc_sequence_map)
sifts_map = SIFTS.retrieve('1ZC8', cache_dir = cache_dir)
print(sifts_map.atom_to_uniparc_sequence_map)
sifts_map = SIFTS.retrieve('4IHY', cache_dir = cache_dir)
print(sifts_map.atom_to_uniparc_sequence_map)
sifts_map = SIFTS.retrieve('1J1M', cache_dir = cache_dir)
print(sifts_map.atom_to_uniparc_sequence_map)
sifts_map = SIFTS.retrieve('1A2C', cache_dir = cache_dir)
print(sifts_map.atom_to_uniparc_sequence_map)

#p = PDB.from_filepath('../.testdata/1H38.pdb') # has protein, DNA, RNA
#p = PDB.from_filepath('../.testdata/1ZC8.pdb')
#p = PDB.from_filepath('../.testdata/4IHY.pdb')
#p = PDB.from_filepath('../.testdata/1J1M.pdb')
#p = PDB.from_filepath('../.testdata/1H38.pdb')
#p = PDB.from_filepath('../.testdata/1A2C.pdb')
#104L


sys.exit(0)


sa = PDBUniParcSequenceAligner('1KI1', cache_dir = '/home/oconchus/temp', cut_off = 85.0)
print('d', sa.residue_mapping)
sys.exit(0)
self.residue_match_mapping = {}
sa = PDBUniParcSequenceAligner('2A1J', cache_dir = '/home/oconchus/temp', cut_off = 85.0)
sys.exit(0)
sa = PDBUniParcSequenceAligner('104L', cache_dir = '/home/oconchus/temp', cut_off = 85.0)
sys.exit(0)
sa = PDBUniParcSequenceAligner('1FQV', cache_dir = '/home/oconchus/temp', cut_off = 85.0)
sys.exit(0)


sa = PDBUniParcSequenceAligner('1KI1', cache_dir = '/home/oconchus/temp', cut_off = 98.0)
print(sa.alignment)
print("***")
print(sa)
print("***")
print(sa.alignment['A'])
print("***")
print(sa.get_alignment_percentage_identity('A'))
print("***")

print(sa.get_residue_mapping('A'))


uparcA = sa.get_uniparc_object('A')


sys.exit(0)
cache_dir = '/home/oconchus/temp'

pdb_id = '1KI1'

uniparc_sequences = {}
pdb_uniparc_mapping = pdb_to_uniparc(['1KI1'], cache_dir = cache_dir)
for upe in pdb_uniparc_mapping['1KI1']:
    uniparc_sequences[upe.UniParcID] = upe.sequence

f = FASTA.retrieve('1KI1', cache_dir = cache_dir)
f = f['1KI1']
chains = sorted(f.keys())

for uniparc_id, uniparc_sequence in uniparc_sequences.iteritems():
    print(uniparc_sequence)

chain_matches = {}
for c in chains:
    chain_matches[c] = []

    colortext.message("MATCHING CHAIN C")
    fasta_sequence = f[c]

    string_matches = []

    # Try some dumb substring based matching first
    for uniparc_id, uniparc_sequence in uniparc_sequences.iteritems():
        idx = uniparc_sequence.find(fasta_sequence)
        if idx != -1:
            string_matches.append((uniparc_id, idx, 0, uniparc_sequence))
        elif len(fasta_sequence) > 30:
            idx = uniparc_sequence.find(fasta_sequence[5:-5])
            if idx != -1:
                string_matches.append((uniparc_id, idx, 5, uniparc_sequence))
            else:
                idx = uniparc_sequence.find(fasta_sequence[7:-7])
                if idx != -1:
                    string_matches.append((uniparc_id, idx, 7, uniparc_sequence))
        elif len(fasta_sequence) > 15:
            idx = uniparc_sequence.find(fasta_sequence[3:-3])
            if idx != -1:
                string_matches.append((uniparc_id, idx, 3, uniparc_sequence))

    assert(len(string_matches) <= 1)
    for m in string_matches:
        colortext.message('matched %s at index %d by cropping %d residues on both sides of the sequence' % m[0:3])

    sequences = [fasta_sequence] + uniparc_sequences.values()
    assert(len(uniparc_sequences) == 2)

    colortext.warning("Trying to match chain %c against UniParc IDs %s" % (c, uniparc_sequences.keys()))
    align_three_simple_sequences(fasta_sequence, uniparc_sequences['UPI00001403C6'], uniparc_sequences['UPI0000000356'], sequence1name = '%s:%s|PDBID|CHAIN|SEQUENCE' % (pdb_id, c), sequence2name = 'UPI00001403C6', sequence3name = 'UPI0000000356')

    #for uniparc_id, uniparc_sequence in uniparc_sequences.iteritems():
    #    colortext.warning("Trying to match chain %c against UniParc ID %s" % (c, uniparc_id))
    #    align_two_simple_sequences(fasta_sequence, uniparc_sequence, sequence1name = '%s:%s|PDBID|CHAIN|SEQUENCE' % (pdb_id, c), sequence2name = uniparc_id)


# sanity check - see if uniprotAC in pdb is in the list of the matched uniprot id

print(chains)


sys.exit(0)

px = PDBML.retrieve('1A2C', cache_dir='/home/oconchus/temp')
for k, v in sorted(px.atom_to_seqres_sequence_maps.iteritems(), key=lambda x:(x[0], x[1])):
    print(k,v)


p = PDB.from_filepath('../.testdata/1H38.pdb') # has protein, DNA, RNA
p = PDB.from_filepath('../.testdata/1ZC8.pdb')
p = PDB.from_filepath('../.testdata/4IHY.pdb')
#p = PDB('../.testdata/2GRB.pdb')
p = PDB.from_filepath('../.testdata/1J1M.pdb')
p = PDB.from_filepath('../.testdata/1H38.pdb')
p = PDB.from_filepath('../.testdata/1A2C.pdb')

#print(p.structure_lines)

colortext.message("Resolution")
print(p.get_resolution())

colortext.message("Techniques")
print(p.get_techniques())

colortext.message("References")
refs = p.get_DB_references()
for pdb_id, details in sorted(refs.iteritems()):
    print(pdb_id)
    for db, chain_details in sorted(details.iteritems()):
        print("  %s" % db)
        for chain_id, subdetails in sorted(chain_details.iteritems()):
            print("    Chain %s" % chain_id)
            for k, v in sorted(subdetails.iteritems()):
                if k == 'PDBtoDB_mapping':
                    print("      PDBtoDB_mapping:")
                    for mpng in v:
                        print("          dbRange :  %s -> %s" % (mpng['dbRange'][0].rjust(5), mpng['dbRange'][1].ljust(5)))
                        print("          PDBRange:  %s -> %s" % (mpng['PDBRange'][0].rjust(5), mpng['PDBRange'][1].ljust(5)))

                else:
                    print("      %s: %s" % (k, v))


colortext.message("Molecule information")
molecules = p.get_molecules_and_source()
for m in molecules:
    colortext.warning("Molecule %d" % m['MoleculeID'])
    for k, v in m.iteritems():
        if k != 'MoleculeID':
            print("  %s: %s" % (k,v))

colortext.message("Journal information")
for k,v in p.get_journal().iteritems():
    print("%s : %s" % (k.ljust(20), v))

colortext.message("PDB format version")
print(p.format_version)

colortext.message("SEQRES sequences")
sequences, chains_in_order = p.get_SEQRES_sequences()
for chain_id in chains_in_order:
    colortext.warning("%s (%s)" % (chain_id, p.chain_types[chain_id]))
    print(sequences[chain_id])

colortext.message("get_all_sequences")
print(p.get_all_sequences('~/Rosetta3.5/rosetta_source/build/src/release/linux/3.8/64/x86/gcc/4.7/default/rosetta_scripts.default.linuxgccrelease', '~/Rosetta3.5/rosetta_database/'))

#print(p.get_pdb_to_rosetta_residue_map('/guybrushhome/Rosetta3.5/rosetta_source/build/src/release/linux/3.8/64/x86/gcc/4.7/default/rosetta_scripts.default.linuxgccrelease', '/guybrushhome/Rosetta3.5/rosetta_database/'))


sys.exit(0)

colortext.message("GetRosettaResidueMap")
print(p.GetRosettaResidueMap())


colortext.message("Chains")
print(",".join(p.get_ATOM_and_HETATM_chains()))


sys.exit(0)

for testpdb in ['2GRB', '4IHY', '1ZC8', '1H38']:
    p = PDB('../.testdata/%s.pdb' % testpdb)
    colortext.message("SEQRES sequences for %s" % testpdb)
    sequences, chains_in_order = p.get_SEQRES_sequences()
    for chain_id in chains_in_order:
        colortext.warning("%s (%s)" % (chain_id, p.chain_types[chain_id]))
        print(sequences[chain_id])


p = PDB('../.testdata/2GRB.pdb')
sequences, chains_in_order = p.get_SEQRES_sequences()
assert(p.chain_types['A'] == 'RNA')
assert(sequences['A'] == 'UGIGGU')

p = PDB('../.testdata/4IHY.pdb')
sequences, chains_in_order = p.get_SEQRES_sequences()
assert(p.chain_types['A'] == 'Protein')
assert(p.chain_types['C'] == 'DNA')
assert(sequences['C'] == 'AAATTTGTTTGIICICTGAGCAAATTT')

p = PDB('../.testdata/1ZC8.pdb')
sequences, chains_in_order = p.get_SEQRES_sequences()
assert(p.chain_types['K'] == 'Protein')
assert(p.chain_types['I'] == 'DNA')
assert(p.chain_types['F'] == 'RNA')
assert(sequences['F'] == 'CUUUAGCAGCUUAAUAACCUGCUUAGAGC')
assert(sequences['I'] == 'AUCGCGUGGAAGCCCUGCCUGGGGUUGAAGCGUUAAAACUUAAUCAGGC')

p = PDB('../.testdata/1H38.pdb')
sequences, chains_in_order = p.get_SEQRES_sequences()
assert(p.chain_types['D'] == 'Protein')
assert(p.chain_types['E'] == 'DNA')
assert(p.chain_types['F'] == 'RNA')
assert(sequences['E'] == 'GGGAATCGACATCGCCGC')
assert(sequences['F'] == 'AACUGCGGCGAU')
