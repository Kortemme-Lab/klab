# A dict of Rosetta score types generated from ScoreType.hh
# The tuples are of the form (English description, comments from ScoreType.hh - not necessarily meaningful, and the corresponding weights file)

score_types = {
	"fa_atr"                                            	:	("Lennard-Jones attractive between atoms in different residues", "enumeration starts at 1 for indexing utility::vector1", ['standard_weights']),
	"fa_rep"                                            	:	("Lennard-Jones repulsive between atoms in different residues", None, ['standard_weights']),
	"fa_sol"                                            	:	("Lazaridis-Jarplus solvation energy", None, ['standard_weights']),
	"fa_intra_atr"                                      	:	(None, None, []),
	"fa_intra_rep"                                      	:	("Lennard-Jones repulsive between atoms in the same residue", None, ['standard_weights']),
	"fa_intra_sol"                                      	:	(None, None, []),
	"lk_hack"                                           	:	(None, None, []),
	"lk_ball"                                           	:	(None, None, []),
	"lk_ball_iso"                                       	:	(None, None, []),
	"coarse_fa_atr"                                     	:	(None, None, []),
	"coarse_fa_rep"                                     	:	(None, None, []),
	"coarse_fa_sol"                                     	:	(None, None, []),
	"coarse_beadlj"                                     	:	(None, None, []),
	"mm_lj_intra_rep"                                   	:	(None, None, []),
	"mm_lj_intra_atr"                                   	:	(None, None, []),
	"mm_lj_inter_rep"                                   	:	(None, None, []),
	"mm_lj_inter_atr"                                   	:	(None, None, []),
	"mm_twist"                                          	:	(None, "could be lr 2benergy and not in energy graph", []),
	"mm_bend"                                           	:	("Deviation of bond angles from the mean", "could be lr 2benergy and not in energy graph", []),
	"mm_stretch"                                        	:	(None, "could be lr 2benergy and not in energy graph", []),
	"lk_costheta"                                       	:	(None, None, []),
	"lk_polar"                                          	:	(None, None, []),
	"lk_nonpolar"                                       	:	(None, "Lazaridis-Karplus solvation energy, over nonpolar atoms", []),
	"hack_elec"                                         	:	(None, None, []),

    "fa_elec"                                               :	("Coulombic electrostatic potential with a distance-dependant dielectric", None, []),
	"dslf_fa13"                                             :	("Disulfide geometry potential", None, []),

	"hack_elec_bb_bb"                                   	:	(None, None, []),
	"hack_elec_bb_sc"                                   	:	(None, None, []),
	"hack_elec_sc_sc"                                   	:	(None, None, []),
	"h2o_hbond"                                         	:	(None, None, []),
	"dna_dr"                                            	:	(None, None, []),
	"dna_bp"                                            	:	(None, None, []),
	"dna_bs"                                            	:	(None, None, []),
	"peptide_bond"                                      	:	(None, None, []),
	"pcs"                                               	:	(None, "Pseudocontact Shift Energy", []),
	"pcs2"                                              	:	(None, "Pseudocontact Shift Energy version 2. Will replace pcs end of 2010", []),
	"fastsaxs"                                          	:	(None, "fastsaxs agreement using formulation of Stovgaard et al (BMC Bioinf. 2010)", []),
	"saxs_score"                                        	:	(None, "centroid saxs asessment", []),
	"saxs_cen_score"                                    	:	(None, None, []),
	"saxs_fa_score"                                     	:	(None, "full-atom SAXS score", []),
	"pddf_score"                                        	:	(None, "score based on pairwise distance distribution function", []),
	"fa_mbenv"                                          	:	(None, "depth dependent reference term", []),
	"fa_mbsolv"                                         	:	(None, "burial+depth dependent term", []),
	"hack_elec_rna_phos_phos"                           	:	(None, "Simple electrostatic repulsion term between phosphates", []),
	"hack_elec_rna_phos_sugr"                           	:	(None, None, []),
	"hack_elec_rna_phos_base"                           	:	(None, None, []),
	"hack_elec_rna_sugr_sugr"                           	:	(None, None, []),
	"hack_elec_rna_sugr_base"                           	:	(None, None, []),
	"hack_elec_rna_base_base"                           	:	(None, None, []),
	"hack_elec_aro_aro"                                 	:	(None, None, []),
	"hack_elec_aro_all"                                 	:	(None, None, []),
	"hack_aro"                                          	:	(None, None, []),
	"rna_fa_atr_base"                                   	:	(None, None, []),
	"rna_fa_rep_base"                                   	:	(None, None, []),
	"rna_data_backbone"                                 	:	(None, "Using chemical accessibility data for RNA.", []),
	"ch_bond"                                           	:	(None, "Carbon hydrogen bonds", []),
	"ch_bond_bb_bb"                                     	:	(None, None, []),
	"ch_bond_sc_sc"                                     	:	(None, None, []),
	"ch_bond_bb_sc"                                     	:	(None, None, []),
	"pro_close"                                         	:	("Proline ring closure energy", None, ['standard_weights']),
	"rama2b"                                            	:	(None, None, []),
	"vdw"                                               	:	(None, "centroid", []),
	"cenpack"                                           	:	(None, "centroid", []),
	"cenpack_smooth"                                    	:	(None, "fpd  smooth cenpack", []),
	"cen_hb"                                            	:	(None, "fpd  centroid bb hbonding", []),
	"hybrid_vdw"                                        	:	(None, "hybrid centroid+fa", []),
	"rna_vdw"                                           	:	(None, "low res clash check for RNA", []),
	"rna_base_backbone"                                 	:	(None, "Bases to 2'-OH, phosphates, etc.", []),
	"rna_backbone_backbone"                             	:	(None, "2'-OH to 2'-OH, phosphates, etc.", []),
	"rna_repulsive"                                     	:	(None, "mainly phosphate-phosphate repulsion", []),
	"rna_base_pair_pairwise"                            	:	(None, "Base-base interactions (Watson-Crick and non-Watson-Crick)", []),
	"rna_base_axis_pairwise"                            	:	(None, "Force base normals to be parallel", []),
	"rna_base_stagger_pairwise"                         	:	(None, "Force base pairs to be in same plane.", []),
	"rna_base_stack_pairwise"                           	:	(None, "Stacking interactions", []),
	"rna_base_stack_axis_pairwise"                      	:	(None, "Stacking interactions should involve parallel bases.", []),
	"rna_data_base"                                     	:	(None, "Using chemical accessibility data for RNA.", []),
	"rna_base_pair"                                     	:	(None, "Base-base interactions (Watson-Crick and non-Watson-Crick)", []),
	"rna_base_axis"                                     	:	(None, "Force base normals to be parallel", []),
	"rna_base_stagger"                                  	:	(None, "Force base pairs to be in same plane.", []),
	"rna_base_stack"                                    	:	(None, "Stacking interactions", []),
	"rna_base_stack_axis"                               	:	(None, "Stacking interactions should involve parallel bases.", []),
	"rna_torsion"                                       	:	(None, "RNA torsional potential.", []),
	"rna_sugar_close"                                   	:	(None, "constraints to keep RNA sugar closed, and with reasonably ideal geometry", []),
	"fa_stack"                                          	:	(None, "stacking interaction modeled as pairwise atom-atom interactions", []),
	"fa_stack_aro"                                      	:	(None, None, []),
	"fa_intra_RNA_base_phos_atr"                        	:	(None, "RNA specific score term", []),
	"fa_intra_RNA_base_phos_rep"                        	:	(None, "RNA specific score term", []),
	"fa_intra_RNA_base_phos_sol"                        	:	(None, "RNA specific score term", []),
	"lk_polar_intra_RNA"                                	:	(None, "RNA specific score term", []),
	"lk_nonpolar_intra_RNA"                             	:	(None, "RNA specific score term", []),
	"hbond_intra"                                       	:	(None, "Currently effects only RNA", []),
	"geom_sol_intra_RNA"                                	:	(None, "RNA specific score term", []),
	"CI_geom_sol"                                       	:	(None, "Context independent version. Currently tested only for RNA case.", []),
	"CI_geom_sol_intra_RNA"                             	:	(None, "RNA specific score term", []),
	"fa_cust_pair_dist"                                 	:	(None, "custom short range 2b", []),
	"custom_atom_pair"                                  	:	(None, None, []),
	"orbitals_hpol"                                     	:	(None, None, []),
	"orbitals_haro"                                     	:	(None, None, []),
	"orbitals_orbitals"                                 	:	(None, None, []),
	"orbitals_hpol_bb"                                  	:	(None, None, []),
	"PyRosettaTwoBodyContextIndepenedentEnergy_first"   	:	(None, None, []),
	"PyRosettaTwoBodyContextIndepenedentEnergy_last"    	:	(None, None, []),
	"python"                                            	:	(None, "<-- Deprecated use PyRosettaEnergie* instead", []),
	"n_ci_2b_score_types"                               	:	(None, "/ keep this guy at the end of the ci2b scores", []),
	"fa_pair"                                           	:	("Statistics-based pair term, favors salt bridges (replaced by fa_elec in Talaris2013)", "/ == fa_pair_pol_pol", ['standard_weights']),
	"fa_pair_aro_aro"                                   	:	(None, None, []),
	"fa_pair_aro_pol"                                   	:	(None, None, []),
	"fa_pair_pol_pol"                                   	:	(None, None, []),
	"fa_plane"                                          	:	("pi-pi interaction between aromatic groups, by default = 0", None, ['standard_weights']),
	"hbond_sr_bb"                                       	:	("Backbone-backbone hbonds close in primary sequence", None, ['standard_weights']),
	"hbond_lr_bb"                                       	:	("Backbone-backbone hbonds distant in primary sequence", None, ['standard_weights']),
	"hbond_bb_sc"                                       	:	("Sidechain-backbone hydrogen bond energy", None, ['standard_weights']),
	"hbond_sr_bb_sc"                                    	:	(None, None, []),
	"hbond_lr_bb_sc"                                    	:	(None, None, []),
	"hbond_sc"                                          	:	("Sidechain-sidechain hydrogen bond energy", None, ['standard_weights']),
	"PyRosettaTwoBodyContextDependentEnergy_first"      	:	(None, None, []),
	"PyRosettaTwoBodyContextDependentEnergy_last"       	:	(None, None, []),
	"interface_dd_pair"                                 	:	(None, None, []),
	"geom_sol"                                          	:	(None, "Geometric Solvation energy for polar atoms", []),
	"occ_sol_fitted"                                    	:	(None, None, []),
	"occ_sol_fitted_onebody"                            	:	(None, None, []),
	"occ_sol_exact"                                     	:	(None, None, []),
	"pair"                                              	:	(None, "centroid", []),
	"cen_pair_smooth"                                   	:	(None, "fpd  smooth centroid pair", []),
	"Mpair"                                             	:	(None, None, []),
	"suck"                                              	:	(None, None, []),
	"rna_rg"                                            	:	(None, "Radius of gyration for RNA", []),
	"interchain_pair"                                   	:	(None, None, []),
	"interchain_vdw"                                    	:	(None, None, []),
	"n_shortranged_2b_score_types"                      	:	(None, "keep this guy at the end of the sr ci/cd 2b scores", []),
	"gb_elec"                                           	:	(None, None, []),
	"dslf_ss_dst"                                       	:	("Distance score in current disulfide (replaced by dslf_fa13 in Talaris2013)", None, ['standard_weights']),
	"dslf_cs_ang"                                       	:	("CSangles score in current disulfide (replaced by dslf_fa13 in Talaris2013)", None, ['standard_weights']),
	"dslf_ss_dih"                                       	:	("Dihedral score in current disulfide (replaced by dslf_fa13 in Talaris2013)", None, ['standard_weights']),
	"dslf_ca_dih"                                       	:	("Ca dihedral score in current disulfide (replaced by dslf_fa13 in Talaris2013)", None, ['standard_weights']),
	"dslf_cbs_ds"                                       	:	(None, None, []),
	"dslfc_cen_dst"                                     	:	(None, None, []),
	"dslfc_cb_dst"                                      	:	(None, None, []),
	"dslfc_ang"                                         	:	(None, None, []),
	"dslfc_cb_dih"                                      	:	(None, None, []),
	"dslfc_bb_dih"                                      	:	(None, None, []),
	"dslfc_rot"                                         	:	(None, None, []),
	"dslfc_trans"                                       	:	(None, None, []),
	"dslfc_RT"                                          	:	(None, None, []),
	"atom_pair_constraint"                              	:	(None, "Harmonic constraints between atoms involved in Watson-Crick base pairs specified by the user in the params file", []),
	"constant_constraint"                               	:	(None, None, []),
	"coordinate_constraint"                             	:	(None, None, []),
	"angle_constraint"                                  	:	(None, None, []),
	"dihedral_constraint"                               	:	(None, None, []),
	"big_bin_constraint"                                	:	(None, None, []),
	"dunbrack_constraint"                               	:	(None, None, []),
	"site_constraint"                                   	:	(None, None, []),
	"rna_bond_geometry"                                 	:	(None, "deviations from ideal geometry", []),
	"rama"                                              	:	("Ramachandran preferences", None, ['score12_wts_patch']),
	"omega"                                             	:	("Omega dihedral in the backbone", None, ['score12_wts_patch']),
	"fa_dun"                                            	:	("Internal energy of sidechain rotamers as derived from Dunbrack's statistics", None, ['standard_weights']),
	"p_aa_pp"                                           	:	("Probability of amino acid at phi/psi", None, ['standard_weights']),
	"yhh_planarity"                                     	:	(None, None, []),
	"h2o_intra"                                         	:	(None, None, []),
	"ref"                                               	:	("Reference energy for each amino acid", None, ['standard_weights']),
	"seqdep_ref"                                        	:	(None, None, []),
	"envsmooth"                                         	:	(None, None, []),
	"e_pH"                                              	:	(None, None, []),
	"rna_bulge"                                         	:	(None, None, []),
	"special_rot"                                       	:	(None, None, []),
	"PB_elec"                                           	:	(None, None, []),
	"cen_env_smooth"                                    	:	(None, "fpd smooth centroid env", []),
	"cbeta_smooth"                                      	:	(None, "fpd smooth cbeta", []),
	"env"                                               	:	(None, None, []),
	"cbeta"                                             	:	(None, None, []),
	"DFIRE"                                             	:	(None, None, []),
	"Menv"                                              	:	(None, None, []),
	"Mcbeta"                                            	:	(None, None, []),
	"Menv_non_helix"                                    	:	(None, None, []),
	"Menv_termini"                                      	:	(None, None, []),
	"Menv_tm_proj"                                      	:	(None, None, []),
	"Mlipo"                                             	:	(None, None, []),
	"rg"                                                	:	(None, "radius of gyration", []),
	"co"                                                	:	(None, "contact order", []),
	"hs_pair"                                           	:	(None, None, []),
	"ss_pair"                                           	:	(None, None, []),
	"rsigma"                                            	:	(None, None, []),
	"sheet"                                             	:	(None, None, []),
	"burial"                                            	:	(None, "informatic burial prediction", []),
	"abego"                                             	:	(None, "informatic torsion-bin prediction", []),
	"natbias_ss"                                        	:	(None, None, []),
	"natbias_hs"                                        	:	(None, None, []),
	"natbias_hh"                                        	:	(None, None, []),
	"natbias_stwist"                                    	:	(None, None, []),
	"aa_cmp"                                            	:	(None, None, []),
	"dock_ens_conf"                                     	:	(None, "conformer reference energies for docking", []),
	"rdc"                                               	:	(None, "NMR residual dipolar coupling energy", []),
	"rdc_segments"                                      	:	(None, "fit alignment on multiple segments independently", []),
	"rdc_rohl"                                          	:	(None, None, []),
	"holes"                                             	:	(None, None, []),
	"holes_decoy"                                       	:	(None, None, []),
	"holes_resl"                                        	:	(None, None, []),
	"holes_min"                                         	:	(None, None, []),
	"holes_min_mean"                                    	:	(None, None, []),
	"dab_sasa"                                          	:	(None, "classic 1.4A probe solvant accessible surface area", []),
	"dab_sev"                                           	:	(None, "solvent excluded volume -- volume of atoms inflated by 1.4A", []),
	"sa"                                                	:	(None, "nonpolar contribution in GBSA", []),
	"interchain_env"                                    	:	(None, None, []),
	"interchain_contact"                                	:	(None, None, []),
	"chainbreak"                                        	:	(None, None, []),
	"linear_chainbreak"                                 	:	(None, None, []),
	"overlap_chainbreak"                                	:	(None, None, []),
	"distance_chainbreak"                               	:	(None, None, []),
	"dof_constraint"                                    	:	(None, None, []),
	"cart_bonded"                                       	:	(None, "cartesian bonded potential", []),
	"neigh_vect"                                        	:	(None, None, []),
	"neigh_count"                                       	:	(None, None, []),
	"neigh_vect_raw"                                    	:	(None, None, []),
	"symE_bonus"                                        	:	(None, None, []),
	"sym_lig"                                           	:	(None, None, []),
	"pack_stat"                                         	:	(None, None, []),
	"rms"                                               	:	(None, "All-heavy-atom RMSD to the native structure", []),
    "rms_stem"                                              :	(None, "All-heavy-atom RMSD to helical segments in the native structure, defined by 'STEM' entries in the parameters file", []),
	"res_type_constraint"                               	:	(None, None, []),
	"res_type_linking_constraint"                       	:	(None, None, []),
	"pocket_constraint"                                 	:	(None, None, []),
	"backbone_stub_constraint"                          	:	(None, None, []),
	"surface"                                           	:	(None, None, []),
	"p_aa"                                              	:	(None, None, []),
	"unfolded"                                          	:	(None, None, []),
	"elec_dens_fast"                                    	:	(None, None, []),
	"elec_dens_window"                                  	:	(None, None, []),
	"elec_dens_whole_structure_ca"                      	:	(None, None, []),
	"elec_dens_whole_structure_allatom"                 	:	(None, None, []),
	"elec_dens_atomwise"                                	:	(None, None, []),
	"patterson_cc"                                      	:	(None, None, []),
	"hpatch"                                            	:	(None, None, []),
	"Menv_smooth"                                       	:	(None, None, []),
	"PyRosettaEnergy_first"                             	:	(None, None, []),
	"PyRosettaEnergy_last"                              	:	(None, None, []),
	"total_score"                                       	:	(None, None, []),
	"n_score_types"                                     	:	(None, None, []),
	"end_of_score_type_enumeration"                     	:	(None, None, []),
    "N_WC"                                                  :	(None, "Number of Watson-Crick base pairs", []),
    "N_NWC"                                             	:	(None, "Number of non-Watson-Crick base pairs", []),
    "N_BS"                                             	    :	(None, "Number of base stacks", []),
    "f_natWC"                                               :	(None, "fraction of native Watson-Crick base pairs recovered", []),
    "f_natNWC"                                              :	(None, "fraction of native non-Watson-Crick base pairs recovered", []),
    "f_natBP"                                               :	(None, "fraction of base pairs recovered", []),
}

class ScoreGroup(object):

    def __init__(self, comment):
        self.comment = comment
        self.score_terms = []

    def add(self, score_term, comment = None):
        self.score_terms.append(dict(name = score_term, comment = comment))

    def __len__(self):
        return len(self.score_terms)


from fs.fsio import read_file
import colortext

def parseScoreType(score_type_header_file):
    contents = read_file(score_type_header_file)
    left_idx = contents.find('enum ScoreType {')
    contents = contents[left_idx+16:]
    right_idx = contents.find('}')
    contents = contents[:right_idx].strip()
    assert(contents.find('{') == -1)
    assert(contents.find('/*') == -1)

    groups = []
    group_comment = None
    current_group = None
    lines = [l.strip() for l in contents.split('\n') if l.strip()]
    x = 0
    while x < len(lines):
        l = lines[x]
        if l.startswith('//'):
            if current_group != None:
                groups.append(current_group)
            group_comment = l[2:]
            for y in range(x + 1, len(lines)):
                l2 = lines[y]
                if l2.startswith('//'):
                    group_comment += ' %s' % l2
                else:
                    x = y - 1
                    break
            group_comment = group_comment.replace('/', '').replace('  ', ' ').strip()
            current_group = ScoreGroup(group_comment)
        else:
            assert(current_group != None)
            comment = None
            score_term = l[:l.find(',')].strip()
            if l.find('//') != - 1:
                comment = l[l.find('//') + 2:].replace('/', '').replace('  ', ' ').strip()
            current_group.add(score_term, comment = comment)
        x += 1
    if current_group != None:
        groups.append(current_group)

    print(len(groups))
    for g in groups:
        #colortext.warning(g.comment)
        #colortext.warning('-' * len(g.comment))
        print(g.comment)
        print('-' * len(g.comment))
        print('\n```')
        for st in g.score_terms:
            comments = [(st['comment'] or '').strip()]
            term = st['name'].strip().replace(' = 1', '')
            if score_types.get(term):
                if score_types[term][0] and score_types[term][0].replace('  ', ' ').strip() not in comments:
                    comments.append(score_types[term][0].replace('  ', ' ').strip())
                if score_types[term][1] and score_types[term][1].replace('  ', ' ').strip() not in comments:
                    comments.append(score_types[term][1].replace('  ', ' ').strip())
            comments = [c[0].capitalize()+c[1:] for c in comments if c.strip()]
            for x in range(len(comments)):
                if comments[x].endswith('.'):
                    comments[x] = comments[x][:-1]
            if comments:
                if len(comments) > 1:
                    print(st['name'].ljust(43))
                    print('    %s' % ('\n    ').join(comments))
                else:
                    print('%s%s' % (st['name'].ljust(43), comments[0]))
            else:
                print(st['name'])
        print('```\n')

    #enum ScoreType {

if __name__ == '__main__':
    parseScoreType('/home/rosetta/trunk/master/source/src/core/scoring/ScoreType.hh')