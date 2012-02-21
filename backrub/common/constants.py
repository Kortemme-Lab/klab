# From the Rosetta 3.3 manual
# © Copyright Rosetta Commons Member Institutions
# Energy terms using in standard.wts

standard_weights = {
	"fa_atr"		:	"Lennard-Jones attractive",
	"fa_rep"		:	"Lennard-Jones repulsive",
	"fa_sol"		:	"Lazaridis-Jarplus solvation energy",
	"fa_intra_rep"	:	"Lennard-Jones repulsive between atoms in the same residue",
	"fa_pair"		:	"Statistics based pair term, favors salt bridges",
	"fa_plane"		:	"pi-pi interaction between aromatic groups, by default = 0",
	"fa_dun"		:	"Internal energy of sidechain rotamers as derived from Dunbrack's statistics",
	"ref"			:	"Reference energy for each amino acid",
	"hbond_lr_bb"	:	"Backbone-backbone hbonds distant in primary sequence",
	"hbond_sr_bb"	:	"Backbone-backbone hbonds close in primary sequence",
	"hbond_bb_sc"	:	"Sidechain-backbone hydrogen bond energy",
	"hbond_sc"		:	"Sidechain-sidechain hydrogen bond energy",
	"p_aa_pp"		:	"Probability of amino acid at phipsi",
	"dslf_ss_dst"	:	"Distance score in current disulfide",
	"dslf_cs_ang"	:	"CSangles score in current disulfide",
	"dslf_ss_dih"	:	"Dihedral score in current disulfide",
	"dslf_ca_dih"	:	"Ca dihedral score in current disulfide",
	"pro_close"		:	"Proline ring closure energy",
}

# Energy Terms using in score12.wts_patch

score12_wts_patch = {
	"rama"			:	"Ramachandran preferences",
	"omega"			:	"Omega dihedral in the backbone",
}