    def calc_CA_rmsd_over_sequence_lessmem(self, ref_pdb):
        ref_residues = [res for res in ref_pdb.iter_residues()]
        
        numResidues = len(ref_residues)
        residue_map = []
        nres = len(ref_residues)
        for i in range(nres):
            residue_map.append([])
        
        i = 0
        for pdb in self.get_next_pdb():
            i += 1
            if i % 10 == 0:
                print("**** Reading PDB #%d for RMSD calculation ****" % i)
            if len(pdb._res_order) != numResidues:
                raise Exception("ERROR: %s does not have the expected number (%d) of residues" % (pdb.fn, nres))
            
            res_ind = 0
            for resid in pdb._res_order:
                CAatom = pdb._residues[resid]._atoms["CA"]
                residue_map[res_ind].append((CAatom.x, CAatom.y, CAatom.z))
                res_ind += 1
                    
        #util.PRINTHEAP("Finished reading %i PDBs. Starting RMSD calculation" % i)
        
        rmsds = []
        for res_ind in range(nres):
            sequence_residues = residue_map[res_ind]
            referenceCA = ref_residues[res_ind]._atoms["CA"]    
            tmplist = [math.sqrt(((referenceCA.x - CApos[0])**2) + ((referenceCA.y - CApos[1])**2) + ((referenceCA.z - CApos[2])**2)) for CApos in sequence_residues]
            rmsd = num.mean(tmplist)
            rmsds.append(rmsd)
        return rmsds