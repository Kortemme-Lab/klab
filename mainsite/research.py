content = '''
      <td style="width:100%">
        <table style="width: 100%;" border="0" cellpadding="0" cellspacing="0"> 
          <tbody> 
            <tr valign="top"> 
              <td style="width: 486px;">
                <img src="img/research.jpg" alt="research" style="border: 0px solid ; width: 271px; height: 35px;">
                <br>
                <table style="text-align: left; width: 600px; height: 19px;" border="0" cellpadding="0" cellspacing="2">
                    <tr>
                      <td>
                        <span class="style14">Our research program focuses on simulation, analysis, design and evolution of proteins, protein interactions and networks. We approach these areas at different levels of detail: On the atomistic level, we aim to develop more accurate computational models for the prediction and design of proteins, their dynamics and their interactions. On the molecular level, we aim to quantitatively characterize biological recognition and signaling through a combination of computational modeling, protein engineering, biochemistry and cellular biology. On the systems level, we study the evolution of proteins and interaction networks using bioinformatics, mathematical modeling and experimental analysis of organismal fitness in bacterial model systems.</span>
                        <br>
                    <tr>
                      <td style="height:10px">
                    <tr>
                      <td>
                        <span class="ital13">COMPUTATIONAL MODELS FOR THE PREDICTION AND DESIGN OF PROTEINS, THEIR DYNAMICS AND INTERACTIONS (Colin Smith, Dan Mandell, Elisabeth Humphris, Greg Friedland, Mariana Babor)</span>
                    <tr>
                      <td>
                        <img src="img/website.001.jpg" alt="research" class="floatleft">
                        <div class="style14">
                            We have developed methods to improve computational protein design: (1) to accurately model changes in protein conformation in response to sequence perturbations predicted by design simulations, and (2), to optimize protein sequences for multiple fitness criteria, such as function within a network of proteins where correct interactions should be favored and unwanted interactions avoided.
                            <p>First, we have developed strategies to predict, at high resolution, conformational variability of the protein backbone. The new methods enable sampling of alternative conformations reflecting those seen in high-resolution structures and generate conformational ensembles consistent with experimental measurements of protein dynamics by nuclear magnetic resonance. When applying these methods to flexible backbone protein design, we find encouraging agreement between sets of sequences selected in comprehensive phage display experiments and amino acid distributions predicted to be structurally tolerated. 
                            <p>Second, we have developed a &quot;multi-constraint&quot; computational design strategy that allows us to optimize a protein sequence for multiple functional and structural requirements simultaneously. We have applied this method to analyze whether and how protein networks place constraints on naturally occurring protein interface sequences to form desired interactions. We identify two strategies to achieve multi-specificity, where promiscuous interfaces use either (i) shared or (ii) distributed &quot;multi-faceted&quot; binding hot spots to recognize multiple partners. These findings suggest routes to target each type of interface: Shared interfaces may be better small molecule targets, whereas multi-faceted interactions may be more &quot;designable&quot; for altered specificity patterns, both by evolution as well as for synthetic applications to design proteins with desired interaction patterns.
                        </div>
                            <p>
                        <span class="ital11">
                          <span style="text-decoration: underline;">This work is funded by:</span>
                            Alfred P. Sloan Foundation,
                            NIH nanomedicine development center,
                            Graduate Student Fellowships from NSF (Greg Friedland), Genentech/Sandler (Elisabeth Humphris), ARCS (Dan Mandell) and DOD/NSF (Colin Smith)
                        </span>
                    <tr>
                      <td style="height:15px">
                    <tr>
                      <td>
                        <span class="ital13">DESIGNED SETS OF PROTEIN-PROTEIN INTERACTIONS TO QUANTITATIVELY CHARACTERIZE BIOLOGICAL REGULATION (Cristina Melero, Greg Kapp, Rich Oberdorf)</span>
                    <tr>
                      <td>
                        <img src="img/website.002.jpg" alt="research2" class="floatleft">
                        <div class="style14">
                            We combine computational design and high-resolution structural modeling with experimental protein engineering to build new sets of protein-protein interactions. The long-term goal is to use these engineered signaling assemblies to quantitatively link regulatory mechanisms to interaction parameters, such as rates, affinities, local concentrations and topologies of the sets of interacting proteins. We chose protein interactions involving a key family of signaling proteins, the small guanine nucleotide binding proteins (GTPase proteins), and protein scaffold components (PDZ domains) as model systems. We have computationally designed and experimentally characterized new pairs of PDZ domain interfaces, and interactions of the GTPase cdc42 and its activator intersectin. We succeeded in engineering a new interaction in which each of the designed proteins is orthogonal with respect to their original wild-type partners (i.e. there is no detectable or significantly reduced cross-talk between engineered and wild-type proteins). We are characterizing the engineered interactions crystallographically and testing their ability to control biological response in reconstituted systems and cell culture. 
                            <p>We are also building mathematical models for representing sets of protein-protein interactions and the sub-species from which they are composed in terms of connected graphs. An initial simple model ignores some of the complexity that exists in complex formation, but makes it possible to enumerate a wide range of possible systems of interacting proteins and their associated behaviors.
                            <p>
                        </div>
                        <span class="ital11">
                          <span style="text-decoration: underline;">This work is funded by:</span>
                          NIH nanomedicine development center,
                          NSF: Synthetic Biology Engineering Research Center
                        </span>
                    <tr>
                      <td style="height:15px">
                    <tr>
                      <td>
                        <span class="ital13">EVOLUTION OF PROTEINS AND PROTEIN INTERACTION NETWORKS (Matt Eames, Rich Oberdorf</span>
                    <tr>
                      <td>
                        <img src="img/website.003.jpg" alt="research3" class="floatleft">
                        <div class="style14">
                          The determinants of protein evolutionary rates are not well understood. Recent work has concluded that the best predictor of evolutionary rates is protein expression level: Highly expressed proteins evolve more slowly, on average, but the mechanisms underlying this correlation are unclear. To characterize evolutionary constraints on proteins and protein interfaces, we have integrated three-dimensional structural information on protein complexes with data on mRNA expression levels and protein abundance in yeast species. We find, first, that pressures imposed by high mRNA expression level affect all protein residues uniformly, effectively eliminating a distinction in conservation between protein cores, interfaces and surfaces; all residues appear uniformly conserved. In contrast, interfaces of proteins with low mRNA expression level have higher evolutionary flexibility, and may constitute the raw material for evolving new functions. Second, we detect a difference in pressures correlated with mRNA-expression and protein-abundance levels, where in highly abundant proteins, but not in proteins with high mRNA levels, interfaces and non-interface surfaces can evolve at different rates. This is surprising given the correlation between mRNA expression level and protein abundance. We suggest that each parameter reports on distinct selective pressures that may be associated primarily with the cost (mRNA expression) and functional benefit (protein abundance) of protein production. 
                          <p>To determine why mRNA expression level and protein abundance reveal such different pressures on protein evolution, we now combine experimental measurements of growths rates in E. coli and mathematical modeling to quantify how alternative mechanisms of protein evolution affect organismal fitness by modulating cost and benefit of protein production.
                          <p>
                        </div>
                        <span class="ital11">
                          <span style="text-decoration: underline;">This work is funded by:</span>
                          Opportunity Award, Sandler Program in Basic Sciences
                        </span>
                </table>
              </td>
            </tr>
          </tbody>
        </table>
      </td>
'''

def getHTML(page):
	return [(page, content)] 