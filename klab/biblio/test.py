#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""
test.py
Test code for these modules.

Created by Shane O'Connor 2014
"""

RIS_test = u'''
TY  - JOUR
T1  - The Prevalence of Species and Strains in the Human Microbiome: A Resource for Experimental Efforts
A1  - Kraal, Laurens
A1  - Abubucker, Sahar
A1  - Kota, Karthik
A1  - Fischbach, Michael A.
A1  - Mitreva, Makedonka
Y1  - 2014/05/14
N2  - <p>Experimental efforts to characterize the human microbiota often use bacterial strains that were chosen for historical rather than biological reasons. Here, we report an analysis of 380 whole-genome shotgun samples from 100 subjects from the NIH Human Microbiome Project. By mapping their reads to 1,751 reference genome sequences and analyzing the resulting relative strain abundance in each sample we present metrics and visualizations that can help identify strains of interest for experimentalists. We also show that approximately 14 strains of 10 species account for 80% of the mapped reads from a typical stool sample, indicating that the function of a community may not be irreducibly complex. Some of these strains account for &gt;20% of the sequence reads in a subset of samples but are absent in others, a dichotomy that could underlie biological differences among subjects. These data should serve as an important strain selection resource for the community of researchers who take experimental approaches to studying the human microbiota.</p>
JF  - PLoS ONE
JA  - PLoS ONE
VL  - 9
IS  - 5
UR  - http://dx.doi.org/10.1371%2Fjournal.pone.0097279
SP  - e97279
EP  -
PB  - Public Library of Science
M3  - doi:10.1371/journal.pone.0097279
ER  -
TY  - JOUR
A1  - Rosenman, David J.
A1  - Huang, Yao-ming
A1  - Xia, Ke
A1  - Fraser, Keith
A1  - Jones, Victoria E.
A1  - Lamberson, Colleen M.
A1  - Van Roey, Patrick
A1  - Colón, Wilfredo
A1  - Bystroff, Christopher
T1  - Green-lighting green fluorescent protein: Faster and more efficient folding by eliminating a cis-trans peptide isomerization event
JF  - Protein Science
JA  - Protein Science
SN  - 1469-896X
UR  - http://dx.doi.org/10.1002/pro.2421
DO  - doi: 10.1002/pro.2421
SP  - n/a
EP  - n/a
KW  - GFP
KW  - folding kinetics
KW  - protein design
KW  - cis
KW  - trans isomerization
PY  - 2014
Y1  - 2014/01/01
ER  -
TY  - JOUR
A1  - Pitman, Derek J.
A1  - Schenkelberg, Christian D.
A1  - Huang, Yao-ming
A1  - Teets, Frank D.
A1  - DiTursi, Daniel
A1  - Bystroff, Christopher
T1  - Improving computational efficiency and tractability of protein design using a piecemeal approach. A strategy for parallel and distributed protein design
Y1  - 2013/12/25
JF  - Bioinformatics
JO  - Bioinformatics
N1  - doi: 10.1093/bioinformatics/btt735
UR  - http://bioinformatics.oxfordjournals.org/content/early/2014/01/11/bioinformatics.btt735.abstract
N2  - Motivation: Accuracy in protein design requires a fine-grained rotamer search, multiple backbone conformations, and a detailed energy function, creating a burden in runtime and memory requirements. A design task may be split into manageable pieces in both three-dimensional space and in the rotamer search space to produce small, fast jobs that are easily distributed. However, these jobs must overlap, presenting a problem in resolving conflicting solutions in the overlap regions.Results: Piecemeal design, in which the design space is split into overlapping regions and rotamer search spaces, accelerates the design process whether jobs are run in series or in parallel. Large jobs that cannot fit in memory were made possible by splitting. Accepting the consensus amino acid selection in conflict regions led to non-optimal choices. Instead, conflicts were resolved using a second pass, in which the split regions were re-combined and designed as one, producing results that were closer to optimal with a minimal increase in runtime over the consensus strategy. Splitting the search space at the rotamer level instead of at the amino acid level further improved the efficiency by reducing the search space in the second pass.Availability and implementation: Programs for splitting protein design expressions are available at www.bioinfo.rpi.edu/tools/piecemeal.html.Contact: bystrc@rpi.eduSupplementary information: Supplementary data are available at Bioinformatics online.
ER  -
TY  - JOUR
JO  - IEEE/ACM Transactions on Computational Biology and Bioinformatics
TI  - Expanded Explorations into the Optimization of an Energy Function for Protein Design
IS  - 5
SN  - 1545-5963
SP  - 1176
EP  - 1187
A1  - Huang, Yao-ming
A1  - Bystroff, Christopher
PY  - 2013/09/01
KW  - Proteins,Linear programming,Amino acids,Hydrogen,Training,Bonding,Optimization,dead-end elimination,Biology and genetics,physics,chemistry,protein design,energy function,machine learning,correlation,rotamers
VL  - 10
JA  - IEEE/ACM Transactions on Computational Biology and Bioinformatics
UR  - http://doi.ieeecomputersociety.org/10.1109/TCBB.2013.113
DO  - doi: 10.1109/TCBB.2013.113
ER  -
TY  - JOUR
AU  - Hoersch, Daniel
AU  - Roh, Soung-Hun
AU  - Chiu, Wah
AU  - Kortemme, Tanja
TI  - Reprogramming an ATP-driven protein machine into a light-gated nanocage
JA  - Nature Nanotechnology
PY  - 2013/11/24/print
VL  - 8
IS  - 12
SP  - 928
EP  - 932
PB  - Nature Publishing Group
SN  - 1748-3387
UR  - http://dx.doi.org/10.1038/nnano.2013.242
M3  - doi: 10.1038/nnano.2013.242
L3  - http://www.nature.com/nnano/journal/v8/n12/abs/nnano.2013.242.html#supplementary-information
AB  - Natural protein assemblies have many sophisticated architectures and functions, creating nanoscale storage containers, motors and pumps. Inspired by these systems, protein monomers have been engineered to self-assemble into supramolecular architectures including symmetrical, metal-templated and cage-like structures. The complexity of protein machines, however, has made it difficult to create assemblies with both defined structures and controllable functions. Here we report protein assemblies that have been engineered to function as light-controlled nanocontainers. We show that an adenosine-5[prime]-triphosphate-driven group II chaperonin, which resembles a barrel with a built-in lid, can be reprogrammed to open and close on illumination with different wavelengths of light. By engineering photoswitchable azobenzene-based molecules into the structure, light-triggered changes in interatomic distances in the azobenzene moiety are able to drive large-scale conformational changes of the protein assembly. The different states of the assembly can be visualized with single-particle cryo-electron microscopy, and the nanocages can be used to capture and release non-native cargos. Similar strategies that switch atomic distances with light could be used to build other controllable nanoscale machines.
ER  -
TY  - JOUR
T1  - Design of a Photoswitchable Cadherin
AU  - Ritterson, Ryan S.
AU  - Kuchenbecker, Kristopher M.
AU  - Michalik, Michael
AU  - Kortemme, Tanja
Y1  - 2013/08/07
PY  - 2013
DA  - 2013/08/28
M3  - doi: 10.1021/ja404992r
DO  - 10.1021/ja404992r
JF  - Journal of the American Chemical Society
JO  - Journal of the American Chemical Society
SP  - 12516
EP  - 12519
VL  - 135
IS  - 34
PB  - American Chemical Society
SN  - 0002-7863
M3  - doi: 10.1021/ja404992r
UR  - http://dx.doi.org/10.1021/ja404992r
Y2  - 2013/09/03
ER  -
TY  - JOUR
T1  - Improvements to Robotics-Inspired Conformational Sampling in Rosetta
A1  - Stein, Amelie
A1  - Kortemme, Tanja
Y1  - 2013/05/21
N2  - To accurately predict protein conformations in atomic detail, a computational method must be capable of sampling models sufficiently close to the native structure. All-atom sampling is difficult because of the vast number of possible conformations and extremely rugged energy landscapes. Here, we test three sampling strategies to address these difficulties: conformational diversification, intensification of torsion and omega-angle sampling and parameter annealing. We evaluate these strategies in the context of the robotics-based kinematic closure (KIC) method for local conformational sampling in Rosetta on an established benchmark set of 45 12-residue protein segments without regular secondary structure. We quantify performance as the fraction of sub-Angstrom models generated. While improvements with individual strategies are only modest, the combination of intensification and annealing strategies into a new “next-generation KIC” method yields a four-fold increase over standard KIC in the median percentage of sub-Angstrom models across the dataset. Such improvements enable progress on more difficult problems, as demonstrated on longer segments, several of which could not be accurately remodeled with previous methods. Given its improved sampling capability, next-generation KIC should allow advances in other applications such as local conformational remodeling of multiple segments simultaneously, flexible backbone sequence design, and development of more accurate energy functions.
JF  - PLoS ONE
JA  - PLoS ONE
VL  - 8
IS  - 5
UR  - http://dx.doi.org/10.1371%2Fjournal.pone.0063090
SP  - e63090
EP  -
PB  - Public Library of Science
M3  - doi: 10.1371/journal.pone.0063090
ER  -
TY  - JOUR
A1  - Koharudin, Leonardus M. I.
A1  - Liu, Lin
A1  - Gronenborn, Angela M.
T1  - Different 3D domain-swapped oligomeric cyanovirin-N structures suggest trapped folding intermediates
Y1  - 2013/05/07
JF  - Proceedings of the National Academy of Sciences
JO  - Proceedings of the National Academy of Sciences
SP  - 7702
EP  - 7707
N1  - doi: 10.1073/pnas.1300327110
VL  - 110
IS  - 19
UR  - http://www.pnas.org/content/110/19/7702.abstract
N2  - Although it has long been established that the amino acid sequence encodes the fold of a protein, how individual proteins arrive at their final conformation is still difficult to predict, especially for oligomeric structures. Here, we present a comprehensive characterization of oligomeric species of cyanovirin-N that all are formed by a polypeptide chain with the identical amino acid sequence. Structures of the oligomers were determined by X-ray crystallography, and each one exhibits 3D domain swapping. One unique 3D domain-swapped structure is observed for the trimer, while for both dimer and tetramer, two different 3D domain-swapped structures were obtained. In addition to the previously identified hinge-loop region of the 3D domain-swapped dimer, which resides between strands β5 and β6 in the middle of the polypeptide sequence, another hinge-loop region is observed between strands β7 and β8 in the structures. Plasticity in these two regions allows for variability in dihedral angles and concomitant differences in chain conformation that results in the differently 3D domain-swapped multimers. Based on all of the different structures, we propose possible folding pathways for this protein. Altogether, our results illuminate the amazing ability of cyanovirin-N to proceed down different folding paths and provide general insights into oligomer formation via 3D domain swapping.
ER  -
TY  - JOUR
T1  - Serverification of Molecular Modeling Applications: The Rosetta Online Server That Includes Everyone (ROSIE)
A1  - Lyskov, Sergey
A1  - Chou, Fang-Chieh
A1  - Ó Conchúir, Shane
A1  - Der, Bryan S.
A1  - Drew, Kevin
A1  - Kuroda, Daisuke
A1  - Xu, Jianqing
A1  - Weitzner, Brian D.
A1  - Renfrew, P. Douglas
A1  - Sripakdeevong, Parin
A1  - Borgo, Benjamin
A1  - Havranek, James J.
A1  - Kuhlman, Brian
A1  - Kortemme, Tanja
A1  - Bonneau, Richard
A1  - Gray, Jeffrey J.
A1  - Das, Rhiju
Y1  - 2013/05/22
N2  - <p>The Rosetta molecular modeling software package provides experimentally tested and rapidly evolving tools for the 3D structure prediction and high-resolution design of proteins, nucleic acids, and a growing number of non-natural polymers. Despite its free availability to academic users and improving documentation, use of Rosetta has largely remained confined to developers and their immediate collaborators due to the code’s difficulty of use, the requirement for large computational resources, and the unavailability of servers for most of the Rosetta applications. Here, we present a unified web framework for Rosetta applications called ROSIE (Rosetta Online Server that Includes Everyone). ROSIE provides (a) a common user interface for Rosetta protocols, (b) a stable application programming interface for developers to add additional protocols, (c) a flexible back-end to allow leveraging of computer cluster resources shared by RosettaCommons member institutions, and (d) centralized administration by the RosettaCommons to ensure continuous maintenance. This paper describes the ROSIE server infrastructure, a step-by-step ‘serverification’ protocol for use by Rosetta developers, and the deployment of the first nine ROSIE applications by six separate developer teams: Docking, RNA <italic>de novo</italic>, ERRASER, Antibody, Sequence Tolerance, Supercharge, Beta peptide design, NCBB design, and VIP redesign. As illustrated by the number and diversity of these applications, ROSIE offers a general and speedy paradigm for serverification of Rosetta applications that incurs negligible cost to developers and lowers barriers to Rosetta use for the broader biological community. ROSIE is available at <ext-link xmlns:xlink="http://www.w3.org/1999/xlink" ext-link-type="uri" xlink:href="http://rosie.rosettacommons.org" xlink:type="simple">http://rosie.rosettacommons.org</ext-link>.</p>
JF  - PLoS ONE
JA  - PLoS ONE
VL  - 8
IS  - 5
UR  - http://dx.doi.org/10.1371%2Fjournal.pone.0063906
SP  - e63906
EP  -
PB  - Public Library of Science
M3  - doi:10.1371/journal.pone.0063906
ER  -
TY  - JOUR
T1  - Design of a Phosphorylatable PDZ Domain with Peptide-Specific Affinity Changes
JO  - Structure
VL  - 21
IS  - 1
SP  - 54
EP  - 64
PY  - 2013/1/8/
T2  -
AU  - Smith, Colin A.
AU  - Shi, Catherine A.
AU  - Chroust, Matthew K.
AU  - Bliska, Thomas E.
AU  - Kelly, Mark J. S.
AU  - Jacobson, Matthew P.
AU  - Kortemme, Tanja
SN  - 0969-2126
DO  - http://dx.doi.org/10.1016/j.str.2012.10.007
M3  - doi: 10.1016/j.str.2012.10.007
UR  - http://www.sciencedirect.com/science/article/pii/S0969212612003814
ER  -
TY  - CHAP
AU  - Ollikainen, Noah
AU  - Smith, Colin A.
AU  - Fraser, James S.
AU  - Kortemme, Tanja
T1  - Chapter Four - Flexible Backbone Sampling Methods to Model and Design Protein Alternative Conformations
A2  - Amy E. Keating
BT  - Methods in Enzymology
PB  - Academic Press
PY  - 2013///
VL  - Volume 523
SP  - 61
EP  - 85
T2  - Methods in Protein Design
SN  - 0076-6879
DO  - http://dx.doi.org/10.1016/B978-0-12-394292-0.00004-7
M3  - doi: 10.1016/B978-0-12-394292-0.00004-7
UR  - http://www.sciencedirect.com/science/article/pii/B9780123942920000047
KW  - Protein design
KW  - Protein dynamics
KW  - Conformational heterogeneity
KW  - Conformational sampling
KW  - Alternative conformations
KW  - Rosetta
KW  - Ringer
KW  - Backrub
ER  -
TY  - CHAP
AU  - Leaver-Fay, Andrew
AU  - O'Meara, Matthew J.
AU  - Tyka, Mike
AU  - Jacak, Ron
AU  - Song, Yifan
AU  - Kellogg, Elizabeth H.
AU  - Thompson, James
AU  - Davis, Ian W.
AU  - Pache, Roland A.
AU  - Lyskov, Sergey
AU  - Gray, Jeffrey J.
AU  - Kortemme, Tanja
AU  - Richardson, Jane S.
AU  - Havranek, James J.
AU  - Snoeyink, Jack
AU  - Baker, David
AU  - Kuhlman, Brian
T1  - Chapter Six - Scientific Benchmarks for Guiding Macromolecular Energy Function Improvement
A2  - Amy E. Keating
BT  - Methods in Enzymology
PB  - Academic Press
PY  - 2013///
VL  - Volume 523
SP  - 109
EP  - 143
T2  - Methods in Protein Design
SN  - 0076-6879
DO  - http://dx.doi.org/10.1016/B978-0-12-394292-0.00006-0
M3  - doi: 10.1016/B978-0-12-394292-0.00006-0
UR  - http://www.sciencedirect.com/science/article/pii/B9780123942920000060
KW  - Rosetta
KW  - Energy function
KW  - Scientific benchmarking
KW  - Parameter estimation
KW  - Decoy discrimination
ER  -
TY  - JOUR
T1  - Prediction of Mutational Tolerance in HIV-1 Protease and Reverse Transcriptase Using Flexible Backbone Protein Design
A1  - Humphris-Narayanan, Elisabeth L.
A1  - Akiva, Eyal
A1  - Varela, Rocco
A1  - Ó Conchúir, Shane
A1  - Kortemme, Tanja
Y1  - 2012/08/23
N2  - <title>Author Summary</title><p>Many related protein sequences can be consistent with the structure and function of a given protein, suggesting that proteins may be quite robust to mutations. This tolerance to mutations is frequently exploited by pathogens. In particular, pathogens can rapidly evolve mutated proteins that have a new function - resistance against a therapeutic inhibitor - without abandoning other functions essential for the pathogen. This principle may also hold more generally: Proteins tolerant to mutational changes can more easily acquire new functions while maintaining their existing properties. The ability to predict the tolerance of proteins to mutation could thus help both to analyze the emergence of resistance mutations in pathogens and to engineer proteins with new functions. Here we develop a computational model to predict protein mutational tolerance towards point mutations accessible by single nucleotide changes, and validate it using two important pathogenic proteins and therapeutic targets: the protease and reverse transcriptase from HIV-1. The model provides insights into how resistance emerges and makes testable predictions on mutations that have not been seen yet. Similar models of mutational tolerance should be useful for characterizing and reengineering the functions of other proteins for which a three-dimensional structure is available.</p>
JF  - PLoS Computational Biology
JA  - PLoS Computational Biology
VL  - 8
IS  - 8
UR  - http://dx.doi.org/10.1371%2Fjournal.pcbi.1002639
SP  - e1002639
EP  -
PB  - Public Library of Science
M3  - doi: 10.1371/journal.pcbi.1002639
ER  -
TY  - JOUR
A1  - Eames, Matt
A1  - Kortemme, Tanja
T1  - Cost-Benefit Tradeoffs in Engineered lac Operons
Y1  - 2012/05/18
JF  - Science
JO  - Science
SP  - 911
EP  - 915
N1  - doi: 10.1126/science.1219083
VL  - 336
IS  - 6083
UR  - http://www.sciencemag.org/content/336/6083/911.abstract
N2  - Cells must balance the cost and benefit of protein expression to optimize organismal fitness. The lac operon of the bacterium Escherichia coli has been a model for quantifying the physiological impact of costly protein production and for elucidating the resulting regulatory mechanisms. We report quantitative fitness measurements in 27 redesigned operons that suggested that protein production is not the primary origin of fitness costs. Instead, we discovered that the lac permease activity, which relates linearly to cost, is the major physiological burden to the cell. These findings explain control points in the lac operon that minimize the cost of lac permease activity, not protein expression. Characterizing similar relationships in other systems will be important to map the impact of cost/benefit tradeoffs on cell physiology and regulation.
ER  -
TY  - JOUR
A1  - Kapp, Gregory T.
A1  - Liu, Sen
A1  - Stein, Amelie
A1  - Wong, Derek T.
A1  - Reményi, Attila
A1  - Yeh, Brian J.
A1  - Fraser, James S.
A1  - Taunton, Jack
A1  - Lim, Wendell A.
A1  - Kortemme, Tanja
T1  - Control of protein signaling using a computationally designed GTPase/GEF orthogonal pair
Y1  - 2012/03/07
JF  - Proceedings of the National Academy of Sciences
JO  - Proceedings of the National Academy of Sciences
SP  - 5277
EP  - 5282
N1  - doi: 10.1073/pnas.1114487109
UR  - http://www.pnas.org/content/early/2012/03/01/1114487109.abstract
N2  - Signaling pathways depend on regulatory protein-protein interactions; controlling these interactions in cells has important applications for reengineering biological functions. As many regulatory proteins are modular, considerable progress in engineering signaling circuits has been made by recombining commonly occurring domains. Our ability to predictably engineer cellular functions, however, is constrained by complex crosstalk observed in naturally occurring domains. Here we demonstrate a strategy for improving and simplifying protein network engineering: using computational design to create orthogonal (non-crossreacting) protein-protein interfaces. We validated the design of the interface between a key signaling protein, the GTPase Cdc42, and its activator, Intersectin, biochemically and by solving the crystal structure of the engineered complex. The designed GTPase (orthoCdc42) is activated exclusively by its engineered cognate partner (orthoIntersectin), but maintains the ability to interface with other GTPase signaling circuit components in vitro. In mammalian cells, orthoCdc42 activity can be regulated by orthoIntersectin, but not wild-type Intersectin, showing that the designed interaction can trigger complex processes. Computational design of protein interfaces thus promises to provide specific components that facilitate the predictable engineering of cellular functions.
ER  -
TY  - JOUR
AU  - Jager, Stefanie
AU  - Cimermancic, Peter
AU  - Gulbahce, Natali
AU  - Johnson, Jeffrey R.
AU  - McGovern, Kathryn E.
AU  - Clarke, Starlynn C.
AU  - Shales, Michael
AU  - Mercenne, Gaelle
AU  - Pache, Lars
AU  - Li, Kathy
AU  - Hernandez, Hilda
AU  - Jang, Gwendolyn M.
AU  - Roth, Shoshannah L.
AU  - Akiva, Eyal
AU  - Marlett, John
AU  - Stephens, Melanie
AU  - D/'Orso, Ivan
AU  - Fernandes, Jason
AU  - Fahey, Marie
AU  - Mahon, Cathal
AU  - O/'Donoghue, Anthony J.
AU  - Todorovic, Aleksandar
AU  - Morris, John H.
AU  - Maltby, David A.
AU  - Alber, Tom
AU  - Cagney, Gerard
AU  - Bushman, Frederic D.
AU  - Young, John A.
AU  - Chanda, Sumit K.
AU  - Sundquist, Wesley I.
AU  - Kortemme, Tanja
AU  - Hernandez, Ryan D.
AU  - Craik, Charles S.
AU  - Burlingame, Alma L.
AU  - Sali, Andrej
AU  - Frankel, Alan D.
AU  - Krogan, Nevan J.
TI  - Global landscape of HIV-human protein complexes
JA  - Nature
PY  - 2011/12/21/online
VL  - 481
IS  - 7381
SP  - 365
EP  - 370
PB  - Nature Publishing Group, a division of Macmillan Publishers Limited. All Rights Reserved.
SN  - 1476-4687
UR  - http://dx.doi.org/10.1038/nature10719
M3  - doi: 10.1038/nature10719
N1  - doi: 10.1038/nature10719
L3  - http://www.nature.com/nature/journal/vaop/ncurrent/abs/nature10719.html#supplementary-information
ER  -
TY  - JOUR
T1  - A Mechanism for Tunable Autoinhibition in the Structure of a Human Ca2+/Calmodulin- Dependent Kinase II Holoenzyme
JO  - Cell
VL  - 146
IS  - 5
SP  - 732
EP  - 745
PY  - 2011/9/2/
T2  -
AU  - Chao, Luke H.
AU  - Stratton, Margaret M.
AU  - Lee, Il-Hyung
AU  - Rosenberg, Oren S.
AU  - Levitz, Joshua
AU  - Mandell, Daniel J.
AU  - Kortemme, Tanja
AU  - Groves, Jay T.
AU  - Schulman, Howard
AU  - Kuriyan, John
SN  - 0092-8674
M3  - doi: 10.1016/j.cell.2011.07.038
UR  - http://www.sciencedirect.com/science/article/pii/S0092867411008762
ER  -
TY  - JOUR
T1  - Predicting the Tolerated Sequences for Proteins and Protein Interfaces Using RosettaBackrub Flexible Backbone Design
A1  - Smith, Colin A.
A1  - Kortemme, Tanja
Y1  - 2011/07/18
N2  - <p>Predicting the set of sequences that are tolerated by a protein or protein interface, while maintaining a desired function, is useful for characterizing protein interaction specificity and for computationally designing sequence libraries to engineer proteins with new functions. Here we provide a general method, a detailed set of protocols, and several benchmarks and analyses for estimating tolerated sequences using flexible backbone protein design implemented in the Rosetta molecular modeling software suite. The input to the method is at least one experimentally determined three-dimensional protein structure or high-quality model. The starting structure(s) are expanded or refined into a conformational ensemble using Monte Carlo simulations consisting of backrub backbone and side chain moves in Rosetta. The method then uses a combination of simulated annealing and genetic algorithm optimization methods to enrich for low-energy sequences for the individual members of the ensemble. To emphasize certain functional requirements (e.g. forming a binding interface), interactions between and within parts of the structure (e.g. domains) can be reweighted in the scoring function. Results from each backbone structure are merged together to create a single estimate for the tolerated sequence space. We provide an extensive description of the protocol and its parameters, all source code, example analysis scripts and three tests applying this method to finding sequences predicted to stabilize proteins or protein interfaces. The generality of this method makes many other applications possible, for example stabilizing interactions with small molecules, DNA, or RNA. Through the use of within-domain reweighting and/or multistate design, it may also be possible to use this method to find sequences that stabilize particular protein conformations or binding interactions over others.</p>
JF  - PLoS ONE
JA  - PLoS ONE
VL  - 6
IS  - 7
UR  - http://dx.doi.org/10.1371%2Fjournal.pone.0020451
SP  - e20451
EP  -
PB  - Public Library of Science
M3  - doi: 10.1371/journal.pone.0020451
ER  -
TY  - JOUR
A1  - Babor, Mariana
A1  - Mandell, Daniel J.
A1  - Kortemme, Tanja
T1  - Assessment of flexible backbone protein design methods for sequence library prediction in the therapeutic antibody Herceptin–HER2 interface
JF  - Protein Science
JA  - Protein Science
VL  - 20
IS  - 6
PB  - Wiley Subscription Services, Inc., A Wiley Company
SN  - 1469-896X
UR  - http://dx.doi.org/10.1002/pro.632
M3  - doi: 10.1002/pro.632
SP  - 1082
EP  - 1089
KW  - protein design
KW  - sequence space
KW  - library design
KW  - antibody
KW  - phage display
KW  - flexible backbone
KW  - conformational ensemble
KW  - kinematic closure
KW  - backrub
KW  - molecular dynamics
Y1  - 2011
ER  -
TY  - CHAP
AU  - Leaver-Fay, Andrew
AU  - Tyka, Michael
AU  - Lewis, Steven M.
AU  - Lange, Oliver F.
AU  - Thompson, James
AU  - Jacak, Ron
AU  - Kaufman, Kristian W.
AU  - Renfrew, P. Douglas
AU  - Smith, Colin A.
AU  - Sheffler, Will
AU  - Davis, Ian W.
AU  - Cooper, Seth
AU  - Treuille, Adrien
AU  - Mandell, Daniel J.
AU  - Richter, Florian
AU  - Ban, Yih-En Andrew
AU  - Fleishman, Sarel J.
AU  - Corn, Jacob E.
AU  - Kim, David E.
AU  - Lyskov, Sergey
AU  - Berrondo, Monica
AU  - Mentzer, Stuart
AU  - Popović, Zoran
AU  - Havranek, James J.
AU  - Karanicolas, John
AU  - Das, Rhiju
AU  - Meiler, Jens
AU  - Kortemme, Tanja
AU  - Gray, Jeffrey J.
AU  - Kuhlman, Brian
AU  - Baker, David
AU  - Bradley, Philip
T1  - Chapter nineteen - Rosetta3: An Object-Oriented Software Suite for the Simulation and Design of Macromolecules
A2  - Johnson, Michael L.
A2  - Brand, Ludwig
BT  - Methods in Enzymology
PB  - Academic Press
PY  - 2011
VL  - Volume 487
SP  - 545
EP  - 574
T2  - Computer Methods, Part C
SN  - 0076-6879
M3  - doi: 10.1016/B978-0-12-381270-4.00019-6
UR  - http://www.sciencedirect.com/science/article/pii/B9780123812704000196
ER  -
TY  - JOUR
T1  - Construction of a Genetic Multiplexer to Toggle between Chemosensory Pathways in Escherichia coli
JO  - Journal of Molecular Biology
VL  - 406
IS  - 2
SP  - 215
EP  - 227
PY  - 2011/2/18/
T2  -
AU  - Moon, Tae Seok
AU  - Clarke, Elizabeth J.
AU  - Groban, Eli S.
AU  - Tamsir, Alvin
AU  - Clark, Ryan M.
AU  - Eames, Matt
AU  - Kortemme, Tanja
AU  - Voigt, Christopher A.
SN  - 0022-2836
M3  - doi: 10.1016/j.jmb.2010.12.019
UR  - http://www.sciencedirect.com/science/article/pii/S0022283610013264
KW  - genetic memory
KW  - recombinase
KW  - stochastic switching
KW  - synthetic biology
KW  - systems biology
ER  -
TY  - JOUR
T1  - Structure-Based Prediction of the Peptide Sequence Space Recognized by Natural and Synthetic PDZ Domains
JO  - Journal of Molecular Biology
VL  - 402
IS  - 2
SP  - 460
EP  - 474
PY  - 2010/9/17/
T2  -
AU  - Smith, Colin A.
AU  - Kortemme, Tanja
SN  - 0022-2836
M3  - doi: 10.1016/j.jmb.2010.07.032
UR  - http://www.sciencedirect.com/science/article/pii/S0022283610007850
KW  - PDZ domain
KW  - specificity prediction
KW  - tolerated sequence space
KW  - protein design
KW  - backrub backbone flexibility
ER  -
TY  - JOUR
A1  - Lauffer, Benjamin E. L.
A1  - Melero, Cristina
A1  - Temkin, Paul
A1  - Lei, Cai
A1  - Hong, Wanjin
A1  - Kortemme, Tanja
A1  - von Zastrow, Mark
T1  - SNX27 mediates PDZ-directed sorting from endosomes to the plasma membrane
Y1  - 2010/08/23
JF  - The Journal of Cell Biology
JO  - The Journal of Cell Biology
SP  - 565
EP  - 574
M3  - doi: 10.1083/jcb.201004060
VL  - 190
IS  - 4
UR  - http://jcb.rupress.org/content/190/4/565.abstract
N2  - Postsynaptic density 95/discs large/zonus occludens-1 (PDZ) domain–interacting motifs, in addition to their well-established roles in protein scaffolding at the cell surface, are proposed to act as cis-acting determinants directing the molecular sorting of transmembrane cargo from endosomes to the plasma membrane. This hypothesis requires the existence of a specific trans-acting PDZ protein that mediates the proposed sorting operation in the endosome membrane. Here, we show that sorting nexin 27 (SNX27) is required for efficient PDZ-directed recycling of the β2-adrenoreceptor (β2AR) from early endosomes. SNX27 mediates this sorting function when expressed at endogenous levels, and its recycling activity requires both PDZ domain–dependent recognition of the β2AR cytoplasmic tail and Phox homology (PX) domain–dependent association with the endosome membrane. These results identify a discrete role of SNX27 in PDZ-directed recycling of a physiologically important signaling receptor, and extend the concept of cargo-specific molecular sorting in the recycling pathway.
ER  -
TY  - JOUR
A1  - Lauck, Florian
A1  - Smith, Colin A.
A1  - Friedland, Gregory D.
A1  - Humphris, Elisabeth L.
A1  - Kortemme, Tanja
T1  - RosettaBackrub—a web server for flexible backbone protein structure modeling and design
Y1  - 2010/07/01
JF  - Nucleic Acids Research
JO  - Nucleic Acids Research
SP  - W569
EP  - W575
M3  - doi: 10.1093/nar/gkq369
VL  - 38
IS  - suppl 2
UR  - http://nar.oxfordjournals.org/content/38/suppl_2/W569.abstract
N2  - The RosettaBackrub server (http://kortemmelab.ucsf.edu/backrub) implements the Backrub method, derived from observations of alternative conformations in high-resolution protein crystal structures, for flexible backbone protein modeling. Backrub modeling is applied to three related applications using the Rosetta program for structure prediction and design: (I) modeling of structures of point mutations, (II) generating protein conformational ensembles and designing sequences consistent with these conformations and (III) predicting tolerated sequences at protein–protein interfaces. The three protocols have been validated on experimental data. Starting from a user-provided single input protein structure in PDB format, the server generates near-native conformational ensembles. The predicted conformations and sequences can be used for different applications, such as to guide mutagenesis experiments, for ensemble-docking approaches or to generate sequence libraries for protein design.
ER  -
TY  - JOUR
T1  - Designing ensembles in conformational and sequence space to characterize and engineer proteins
JO  - Current Opinion in Structural Biology
VL  - 20
IS  - 3
SP  - 377
EP  - 384
PY  - 2010/6//
T2  - Nucleic acids / Sequences and topology
AU  - Friedland, Gregory D.
AU  - Kortemme, Tanja
SN  - 0959-440X
M3  - doi: 10.1016/j.sbi.2010.02.004
UR  - http://www.sciencedirect.com/science/article/pii/S0959440X10000370
ER  -
TY  - CONF
JO  - Proceedings of the 2009 IEEE/ACM International Conference on Computer-Aided Design (ICCAD 2009)
TI  - SAT-based protein design
T2  - Computer-Aided Design - Digest of Technical Papers, 2009. ICCAD 2009. IEEE/ACM International Conference on
IS  -
SN  - 1092-3152
VO  -
SP  - 128
EP  - 135
AU  - Ollikainen, Noah
AU  - Sentovich, Ellen
AU  - Coelho, Carlos
AU  - Kuehlmann, Andreas
AU  - Kortemme, Tanja
Y1  - 2009/11/02/2nd-5th November 2009
PY  - 2009
KW  - Boolean functions
KW  - bioinformatics
KW  - biological techniques
KW  - computability
KW  - molecular biophysics
KW  - molecular configurations
KW  - optimisation
KW  - proteins
KW  - tree searching
KW  - Boolean function
KW  - Boolean satisfiability solver
KW  - DEE based method
KW  - SAT based protein design
KW  - SAT based search space encoding
KW  - amino acid sequence
KW  - branch-and-bound algorithm
KW  - computational protein design
KW  - dead-end-elimination
KW  - optimisation problem
KW  - protein core design problems
KW  - protein structure energy minimisation
KW  - search based approach
VL  -
JA  - Computer-Aided Design - Digest of Technical Papers, 2009. ICCAD 2009. IEEE/ACM International Conference on
UR  - http://ieeexplore.ieee.org/xpls/abs_all.jsp?arnumber=5361301
ER  -
TY  - JOUR
AU  - Mandell, Daniel J.
AU  - Kortemme, Tanja
TI  - Computer-aided design of functional protein interactions
JA  - Nature Chemical Biology
PY  - 2009/11//print
VL  - 5
IS  - 11
SP  - 797
EP  - 807
PB  - Nature Publishing Group
SN  - 1552-4450
UR  - http://dx.doi.org/10.1038/nchembio.251
M3  - doi: 10.1038/nchembio.251
N1  - 10.1038/nchembio.251
ER  -
TY  - JOUR
T1  - Backbone flexibility in computational protein design
JO  - Current Opinion in Biotechnology
VL  - 20
IS  - 4
SP  - 420
EP  - 428
PY  - 2009/8//
T2  - Protein technologies / Systems and synthetic biology
AU  - Mandell, Daniel J.
AU  - Kortemme, Tanja
SN  - 0958-1669
M3  - doi: 10.1016/j.copbio.2009.07.006
UR  - http://www.sciencedirect.com/science/article/pii/S0958166909000913
ER  -

TY  - JOUR
AU  - Mandell, Daniel J.
AU  - Coutsias, Evangelos A.
AU  - Kortemme, Tanja
TI  - Sub-angstrom accuracy in protein loop reconstruction by robotics-inspired conformational sampling
JA  - Nature Methods
PY  - 2009/08//print
VL  - 6
IS  - 8
SP  - 551
EP  - 552
PB  - Nature Publishing Group
SN  - 1548-7091
UR  - http://dx.doi.org/10.1038/nmeth0809-551
M3  - doi: 10.1038/nmeth0809-551
N1  - 10.1038/nmeth0809-551
L3  - http://www.nature.com/nmeth/journal/v6/n8/suppinfo/nmeth0809-551_S1.html
ER  -
TY  - JOUR
T1  - A Correspondence Between Solution-State Dynamics of an Individual Protein and the Sequence and Conformational Diversity of its Family
A1  - Friedland, Gregory D.
A1  - Lakomek, Nils-Alexander
A1  - Griesinger, Christian
A1  - Meiler, Jens
A1  - Kortemme, Tanja
Y1  - 2009/05/29
N2  - <title>Author Summary</title><p>Knowledge of protein properties is essential for enhancing the understanding and engineering of biological functions. One key property of proteins is their flexibility—their intrinsic ability to adopt different conformations. This flexibility can be measured experimentally but the measurements are indirect and computational models are required to interpret them. Here we develop a new computational method for interpreting these measurements of flexibility and use it to create a model of flexibility of the protein ubiquitin. We apply our results to show relationships between the flexibility of one protein and the diversity of structures and amino acid sequences of the protein's evolutionary family. Thus, our results show that more accurate computational modeling of protein flexibility is useful for improving prediction of a broader range of amino acid sequences compatible with a given protein. Our method will be helpful for advancing methods to rationally engineer protein functions by enabling sampling of conformational and sequence diversity similar to that of a protein's evolutionary family.</p>
JF  - PLoS Computational Biology
JA  - PLoS Computational Biology
VL  - 5
IS  - 5
UR  - http://dx.doi.org/10.1371%2Fjournal.pcbi.1000393
SP  - e1000393
EP  -
PB  - Public Library of Science
M3  - doi: 10.1371/journal.pcbi.1000393
ER  -
TY  - JOUR
AU  - Oberdorf, Richard
AU  - Kortemme, Tanja
TI  - Complex topology rather than complex membership is a determinant of protein dosage sensitivity
JA  - Molecular Systems Biology
PY  - 2009/03/17/print
VL  - 5
IS  - 253
PB  - EMBO and Nature Publishing Group
UR  - http://dx.doi.org/10.1038/msb.2009.9
M3  - doi: 10.1038/msb.2009.9
N1  - 10.1038/msb.2009.9
L3  - http://www.nature.com/msb/journal/v5/n1/suppinfo/msb20099_S1.html
ER  -
TY  - JOUR
T1  - Outcome of a Workshop on Applications of Protein Models in Biomedical Research
JO  - Structure
VL  - 17
IS  - 2
SP  - 151
EP  - 159
PY  - 2009/2/13/
T2  -
AU  - Schwede, Torsten
AU  - Sali, Andrej
AU  - Honig, Barry
AU  - Levitt, Michael
AU  - Berman, Helen M.
AU  - Jones, David
AU  - Brenner, Steven E.
AU  - Burley, Stephen K.
AU  - Das, Rhiju
AU  - Dokholyan, Nikolay V.
AU  - Dunbrack Jr., Roland L.
AU  - Fidelis, Krzysztof
AU  - Fiser, Andras
AU  - Godzik, Adam
AU  - Huang, Yuanpeng Janet
AU  - Humblet, Christine
AU  - Jacobson, Matthew P.
AU  - Joachimiak, Andrzej
AU  - Krystek Jr., Stanley R.
AU  - Kortemme, Tanja
AU  - Kryshtafovych, Andriy
AU  - Montelione, Gaetano T.
AU  - Moult, John
AU  - Murray, Diana
AU  - Sanchez, Roberto
AU  - Sosnick, Tobin R.
AU  - Standley, Daron M.
AU  - Stouch, Terry
AU  - Vajda, Sandor
AU  - Vasquez, Max
AU  - Westbrook, John D.
AU  - Wilson, Ian A.
SN  - 0969-2126
M3  - doi: 10.1016/j.str.2008.12.014
UR  - http://www.sciencedirect.com/science/article/pii/S0969212609000318
KW  - PROTEINS
ER  -
TY  - JOUR
A1  - Babor, Mariana
A1  - Kortemme, Tanja
T1  - Multi-constraint computational design suggests that native sequences of germline antibody H3 loops are nearly optimal for conformational flexibility
JF  - Proteins: Structure, Function, and Bioinformatics
JA  - Proteins
VL  - 75
IS  - 4
PB  - Wiley Subscription Services, Inc., A Wiley Company
SN  - 1097-0134
UR  - http://dx.doi.org/10.1002/prot.22293
M3  - doi: 10.1002/prot.22293
SP  - 846
EP  - 858
KW  - antibody flexibility
KW  - computational structural biology
KW  - computational design
KW  - multi-constraint design
KW  - affinity maturation
Y1  - 2009
ER  -
TY  - JOUR
T1  - Differences in Flexibility Underlie Functional Differences in the Ras Activators Son of Sevenless and Ras Guanine Nucleotide Releasing Factor 1
JO  - Structure
VL  - 17
IS  - 1
SP  - 41
EP  - 53
PY  - 2009/1/14/
T2  -
AU  - Freedman, Tanya S.
AU  - Sondermann, Holger
AU  - Kuchment, Olga
AU  - Friedland, Gregory D.
AU  - Kortemme, Tanja
AU  - Kuriyan, John
SN  - 0969-2126
M3  - doi: 10.1016/j.str.2008.11.004
UR  - http://www.sciencedirect.com/science/article/pii/S0969212608004280
KW  - PROTEINS
KW  - SIGNALING
ER  -
TY  - JOUR
T1  - Prediction of Protein-Protein Interface Sequence Diversity Using Flexible Backbone Computational Protein Design
JO  - Structure
VL  - 16
IS  - 12
SP  - 1777
EP  - 1788
PY  - 2008/12/12/
T2  -
AU  - Humphris, Elisabeth L.
AU  - Kortemme, Tanja
SN  - 0969-2126
M3  - doi: 10.1016/j.str.2008.09.012
UR  - http://www.sciencedirect.com/science/article/pii/S0969212608003869
KW  - PROTEINS
ER  -
TY  - JOUR
A1  - Lauffer, Benjamin E. L.
A1  - Chen, Stanford
A1  - Melero, Cristina
A1  - Kortemme, Tanja
A1  - von Zastrow, Mark
A1  - Vargas, Gabriel A.
T1  - Engineered Protein Connectivity to Actin Mimics PDZ-dependent Recycling of G Protein-coupled Receptors but Not Its Regulation by Hrs
Y1  - 2009/01/23
JF  - Journal of Biological Chemistry
JO  - Journal of Biological Chemistry
SP  - 2448
EP  - 2458
N1  - doi: 10.1074/jbc.M806370200
VL  - 284
IS  - 4
UR  - http://www.jbc.org/content/284/4/2448.abstract
N2  - Many G protein-coupled receptors (GPCRs) recycle after agonist-induced endocytosis by a sequence-dependent mechanism, which is distinct from default membrane flow and remains poorly understood. Efficient recycling of the β2-adrenergic receptor (β2AR) requires a C-terminal PDZ (PSD-95/Discs Large/ZO-1) protein-binding determinant (PDZbd), an intact actin cytoskeleton, and is regulated by the endosomal protein Hrs (hepatocyte growth factor-regulated substrate). The PDZbd is thought to link receptors to actin through a series of protein interaction modules present in NHERF/EBP50 (Na+/H+ exchanger 3 regulatory factor/ezrin-binding phosphoprotein of 50 kDa) family and ERM (ezrin/radixin/moesin) family proteins. It is not known, however, if such actin connectivity is sufficient to recapitulate the natural features of sequence-dependent recycling. We addressed this question using a receptor fusion approach based on the sufficiency of the PDZbd to promote recycling when fused to a distinct GPCR, the δ-opioid receptor, which normally recycles inefficiently in HEK293 cells. Modular domains mediating actin connectivity promoted receptor recycling with similarly high efficiency as the PDZbd itself, and recycling promoted by all of the domains was actin-dependent. Regulation of receptor recycling by Hrs, however, was conferred only by the PDZbd and not by downstream interaction modules. These results suggest that actin connectivity is sufficient to mimic the core recycling activity of a GPCR-linked PDZbd but not its cellular regulation.
ER  -
TY  - JOUR
T1  - A Simple Model of Backbone Flexibility Improves Modeling of Side-chain Conformational Variability
JO  - Journal of Molecular Biology
VL  - 380
IS  - 4
SP  - 757
EP  - 774
PY  - 2008/7/18/
T2  -
AU  - Friedland, Gregory D.
AU  - Linares, Anthony J.
AU  - Smith, Colin A.
AU  - Kortemme, Tanja
SN  - 0022-2836
M3  - doi: 10.1016/j.jmb.2008.05.006
UR  - http://www.sciencedirect.com/science/article/pii/S0022283608005597
KW  - protein dynamics
KW  - side-chain dynamics
KW  - NMR order parameters
KW  - protein design
KW  - flexible backbone
ER  -
TY  - JOUR
T1  - Backrub-Like Backbone Simulation Recapitulates Natural Protein Conformational Variability and Improves Mutant Side-Chain Prediction
JO  - Journal of Molecular Biology
VL  - 380
IS  - 4
SP  - 742
EP  - 756
PY  - 2008/7/18/
T2  -
AU  - Smith, Colin A.
AU  - Kortemme, Tanja
SN  - 0022-2836
M3  - doi: 10.1016/j.jmb.2008.05.023
UR  - http://www.sciencedirect.com/science/article/pii/S0022283608005779
KW  - flexible backbone sampling
KW  - backrub motion
KW  - point mutation
KW  - Monte Carlo
KW  - triosephosphate isomerase loop 6
ER  -
TY  - JOUR
T1  - A New Twist in TCR Diversity Revealed by a Forbidden αβ TCR
JO  - Journal of Molecular Biology
VL  - 375
IS  - 5
SP  - 1306
EP  - 1319
PY  - 2008/2/1/
T2  -
AU  - McBeth, Christine
AU  - Seamons, Audrey
AU  - Pizarro, Juan C.
AU  - Fleishman, Sarel J.
AU  - Baker, David
AU  - Kortemme, Tanja
AU  - Goverman, Joan M.
AU  - Strong, Roland K.
SN  - 0022-2836
M3  - doi: 10.1016/j.jmb.2007.11.020
UR  - http://www.sciencedirect.com/science/article/pii/S0022283607014805
ER  -
TY  - JOUR
T1  - Design of Multi-Specificity in Protein Interfaces
A1  - Humphris, Elisabeth L.
A1  - Kortemme, Tanja
Y1  - 2007/08/24
N2  - <title>Author Summary</title><sec id="st1"><title/><p>Computational methods have recently led to remarkable successes in the design of molecules with novel functions. These approaches offer great promise for creating highly selective molecules to accurately control biological processes. However, to reach these goals modeling procedures are needed that are able to define the optimal â€œfitnessâ€ of a protein to function correctly within complex biological networks and in the context of many possible interaction partners. To make progress toward these goals, we describe a computational design procedure that predicts protein sequences optimized to bind not only to a single protein but also to a set of target interaction partners. Application of the method to characterize â€œhubâ€ proteins in cellular interaction networks gives insights into the mechanisms nature has used to tune protein surfaces to recognize multiple correct partner proteins. Our study also provides a starting point to engineer designer molecules that could modulate or replace naturally occurring protein interaction networks to combat misregulation in disease or to build new sets of protein interactions for synthetic biology.</p></sec>.SP  - e164
JF  - PLoS Computational Biology
JA  - PLoS Computational Biology
VL  - 3
IS  - 8
UR  - http://dx.plos.org/10.1371%2Fjournal.pcbi.0030164
SP  - 1591
EP  - 1604
PB  - Public Library of Science
M3  - doi: 10.1371/journal.pcbi.0030164
ER  -
TY  - JOUR
A1  - Lengyel, Candice S. E.
A1  - Willis, Lindsey J.
A1  - Mann, Patrick
A1  - Baker, David
A1  - Kortemme, Tanja
A1  - Strong, Roland K.
A1  - McFarland, Benjamin J.
T1  - Mutations Designed to Destabilize the Receptor-Bound Conformation Increase MICA-NKG2D Association Rate and Affinity
Y1  - 2007/10/19
JF  - Journal of Biological Chemistry
JO  - Journal of Biological Chemistry
SP  - 30658
EP  - 30666
N1  - doi: 10.1074/jbc.M704513200
VL  - 282
IS  - 42
UR  - http://www.jbc.org/content/282/42/30658.abstract
N2  - MICA is a major histocompatibility complex-like protein that undergoes a structural transition from disorder to order upon binding its immunoreceptor, NKG2D. We redesigned the disordered region of MICA with RosettaDesign to increase NKG2D binding. Mutations that stabilize this region were expected to increase association kinetics without changing dissociation kinetics, increase affinity of interaction, and reduce entropy loss upon binding. MICA mutants were stable in solution, and they were amenable to surface plasmon resonance evaluation of NKG2D binding kinetics and thermodynamics. Several MICA mutants bound NKG2D with enhanced affinity, kinetic changes were primarily observed during association, and thermodynamic changes in entropy were as expected. However, none of the 15 combinations of mutations predicted to stabilize the receptor-bound MICA conformation enhanced NKG2D affinity, whereas all 10 mutants predicted to be destabilized bound NKG2D with increased on-rates. Five of these had affinities enhanced by 0.9–1.8 kcal/mol over wild type by one to three non-contacting substitutions. Therefore, in this case, mutations designed to mildly destabilize a protein enhanced association and affinity.
ER  -
TY  - JOUR
T1  - Structural Mapping of Protein Interactions Reveals Differences in Evolutionary Pressures Correlated to mRNA Level and Protein Abundance
JO  - Structure
VL  - 15
IS  - 11
SP  - 1442
EP  - 1451
PY  - 2007/11/13/
T2  -
AU  - Eames, Matt
AU  - Kortemme, Tanja
SN  - 0969-2126
M3  - doi: 10.1016/j.str.2007.09.010
UR  - http://www.sciencedirect.com/science/article/pii/S0969212607003358
KW  - PROTEINS
KW  - SIGNALING
ER  -
TY  - JOUR
T1  - Computational Design of a New Hydrogen Bond Network and at Least a 300-fold Specificity Switch at a Protein−Protein Interface
JO  - Journal of Molecular Biology
VL  - 361
IS  - 1
SP  - 195
EP  - 208
PY  - 2006/8/4/
T2  -
AU  - Joachimiak, Lukasz A.
AU  - Kortemme, Tanja
AU  - Stoddard, Barry L.
AU  - Baker, David
SN  - 0022-2836
M3  - doi: 10.1016/j.jmb.2006.05.022
UR  - http://www.sciencedirect.com/science/article/pii/S0022283606006048
KW  - computational design
KW  - hydrogen bond network
KW  - DNAse
KW  - immunity protein
KW  - protein–protein interactions
ER  -
TY  - JOUR
T1  - Ca2+ Indicators Based on Computationally Redesigned Calmodulin-Peptide Pairs
JO  - Chemistry & Biology
VL  - 13
IS  - 5
SP  - 521
EP  - 530
PY  - 2006/5//
T2  -
AU  - Palmer, Amy E.
AU  - Giacomello, Marta
AU  - Kortemme, Tanja
AU  - Hires, S. Andrew
AU  - Lev-Ram, Varda
AU  - Baker, David
AU  - Tsien, Roger Y.
SN  - 1074-5521
M3  - doi: 10.1016/j.chembiol.2006.03.007
UR  - http://www.sciencedirect.com/science/article/pii/S1074552106001177
KW  - MOLNEURO
KW  - CHEMBIO
ER  -
TY  - JOUR
A1  - Song, Gang
A1  - Lazar, Greg A.
A1  - Kortemme, Tanja
A1  - Shimaoka, Motomu
A1  - Desjarlais, John R.
A1  - Baker, David
A1  - Springer, Timothy A.
T1  - Rational Design of Intercellular Adhesion Molecule-1 (ICAM-1) Variants for Antagonizing Integrin Lymphocyte Function-associated Antigen-1-dependent Adhesion
Y1  - 2006/02/24
JF  - Journal of Biological Chemistry
JO  - Journal of Biological Chemistry
SP  - 5042
EP  - 5049
N1  - doi: 10.1074/jbc.M510454200
VL  - 281
IS  - 8
UR  - http://www.jbc.org/content/281/8/5042.abstract
N2  - The interaction between integrin lymphocyte function-associated antigen-1 (LFA-1) and its ligand intercellular adhesion molecule-1 (ICAM-1) is critical in immunological and inflammatory reactions but, like other adhesive interactions, is of low affinity. Here, multiple rational design methods were used to engineer ICAM-1 mutants with enhanced affinity for LFA-1. Five amino acid substitutions 1) enhance the hydrophobicity and packing of residues surrounding Glu-34 of ICAM-1, which coordinates to a Mg2+ in the LFA-1 I domain, and 2) alter associations at the edges of the binding interface. The affinity of the most improved ICAM-1 mutant for intermediate- and high-affinity LFA-1 I domains was increased by 19-fold and 22-fold, respectively, relative to wild type. Moreover, potency was similarly enhanced for inhibition of LFA-1-dependent ligand binding and cell adhesion. Thus, rational design can be used to engineer novel adhesion molecules with high monomeric affinity; furthermore, the ICAM-1 mutant holds promise for targeting LFA-1-ICAM-1 interaction for biological studies and therapeutic purposes.
ER  -
TY  - JOUR
A1  - Freedman, Tanya S.
A1  - Sondermann, Holger
A1  - Friedland, Gregory D.
A1  - Kortemme, Tanja
A1  - Bar-Sagi, Dafna
A1  - Marqusee, Susan
A1  - Kuriyan, John
T1  - A Ras-induced conformational switch in the Ras activator Son of sevenless
Y1  - 2006/11/07
JF  - Proceedings of the National Academy of Sciences
JO  - Proceedings of the National Academy of Sciences
SP  - 16692
EP  - 16697
N1  - doi: 10.1073/pnas.0608127103
VL  - 103
IS  - 45
UR  - http://www.pnas.org/content/103/45/16692.abstract
N2  - The Ras-specific guanine nucleotide-exchange factors Son of sevenless (Sos) and Ras guanine nucleotide-releasing factor 1 (RasGRF1) transduce extracellular stimuli into Ras activation by catalyzing the exchange of Ras-bound GDP for GTP. A truncated form of RasGRF1 containing only the core catalytic Cdc25 domain is sufficient for stimulating Ras nucleotide exchange, whereas the isolated Cdc25 domain of Sos is inactive. At a site distal to the catalytic site, nucleotide-bound Ras binds to Sos, making contacts with the Cdc25 domain and with a Ras exchanger motif (Rem) domain. This allosteric Ras binding stimulates nucleotide exchange by Sos, but the mechanism by which this stimulation occurs has not been defined. We present a crystal structure of the Rem and Cdc25 domains of Sos determined at 2.0-Å resolution in the absence of Ras. Differences between this structure and that of Sos bound to two Ras molecules show that allosteric activation of Sos by Ras occurs through a rotation of the Rem domain that is coupled to a rotation of a helical hairpin at the Sos catalytic site. This motion relieves steric occlusion of the catalytic site, allowing substrate Ras binding and nucleotide exchange. A structure of the isolated RasGRF1 Cdc25 domain determined at 2.2-Å resolution, combined with computational analyses, suggests that the Cdc25 domain of RasGRF1 is able to maintain an active conformation in isolation because the helical hairpin has strengthened interactions with the Cdc25 domain core. These results indicate that RasGRF1 lacks the allosteric activation switch that is crucial for Sos activity.
ER  -
TY  - JOUR
A1  - Wang, Stephanie X.
A1  - Pandey, Kailash C.
A1  - Somoza, John R.
A1  - Sijwali, Puran S.
A1  - Kortemme, Tanja
A1  - Brinen, Linda S.
A1  - Fletterick, Robert J.
A1  - Rosenthal, Philip J.
A1  - McKerrow, James H.
T1  - Structural basis for unique mechanisms of folding and hemoglobin binding by a malarial protease
Y1  - 2006/08/01
JF  - Proceedings of the National Academy of Sciences
JO  - Proceedings of the National Academy of Sciences
SP  - 11503
EP  - 11508
N1  - doi: 10.1073/pnas.0600489103
VL  - 103
IS  - 31
UR  - http://www.pnas.org/content/103/31/11503.abstract
N2  - Falcipain-2 (FP2), the major cysteine protease of the human malaria parasite Plasmodium falciparum, is a hemoglobinase and promising drug target. Here we report the crystal structure of FP2 in complex with a protease inhibitor, cystatin. The FP2 structure reveals two previously undescribed cysteine protease structural motifs, designated FP2nose and FP2arm, in addition to details of the active site that will help focus inhibitor design. Unlike most cysteine proteases, FP2 does not require a prodomain but only the short FP2nose motif to correctly fold and gain catalytic activity. Our structure and mutagenesis data suggest a molecular basis for this unique mechanism by highlighting the functional role of two Tyr within FP2nose and a conserved Glu outside this motif. The FP2arm motif is required for hemoglobinase activity. The structure reveals topographic features and a negative charge cluster surrounding FP2arm that suggest it may serve as an exo-site for hemoglobin binding. Motifs similar to FP2nose and FP2arm are found only in related plasmodial proteases, suggesting that they confer malaria-specific functions.
ER  -
TY  - CHAP
AU  - Morozov, Alexandre V.
AU  - Kortemme, Tanja
T1  - Potential Functions for Hydrogen Bonds in Protein Structure Prediction and Design
A2  - Baldwin, Robert L.
A2  - Baker, David
BT  - Advances in Protein Chemistry
PB  - Academic Press
PY  - 2005
VL  - Volume 72
SP  - 1
EP  - 38
T2  - Peptide Solvation and H‐Bonds
SN  - 0065-3233
M3  - doi: 10.1016/S0065-3233(05)72001-5
UR  - http://www.sciencedirect.com/science/article/pii/S0065323305720015
ER  -
TY  - JOUR
A1  - Kortemme, Tanja
A1  - Baker, David
T1  - A simple physical model for binding energy hot spots in protein–protein complexes
Y1  - 2002/10/29
JF  - Proceedings of the National Academy of Sciences
JO  - Proceedings of the National Academy of Sciences
SP  - 14116
EP  - 14121
N1  - doi: 10.1073/pnas.202485799
VL  - 99
IS  - 22
UR  - http://www.pnas.org/content/99/22/14116.abstract
N2  - Protein–protein recognition plays a central role in most biological processes. Although the structures of many protein–protein complexes have been solved in molecular detail, general rules describing affinity and selectivity of protein–protein interactions do not accurately account for the extremely diverse nature of the interfaces. We investigate the extent to which a simple physical model can account for the wide range of experimentally measured free energy changes brought about by alanine mutation at protein–protein interfaces. The model successfully predicts the results of alanine scanning experiments on globular proteins (743 mutations) and 19 protein–protein interfaces (233 mutations) with average unsigned errors of 0.81 kcal/mol and 1.06 kcal/mol, respectively. The results test our understanding of the dominant contributions to the free energy of protein–protein interactions, can guide experiments aimed at the design of protein interaction inhibitors, and provide a stepping-stone to important applications such as interface redesign.
ER  -
TY  - JOUR
T1  - Design, Activity, and Structure of a Highly Specific Artificial Endonuclease
JO  - Molecular Cell
VL  - 10
IS  - 4
SP  - 895
EP  - 905
PY  - 2002/10//
T2  -
AU  - Chevalier, Brett S.
AU  - Kortemme, Tanja
AU  - Chadsey, Meggen S.
AU  - Baker, David
AU  - Monnat Jr., Raymond J.
AU  - Stoddard, Barry L.
SN  - 1097-2765
M3  - doi: 10.1016/S1097-2765(02)00690-1
UR  - http://www.sciencedirect.com/science/article/pii/S1097276502006901
ER  -
TY  - JOUR
A1  - Gray, Jeffrey J.
A1  - Moughon, Stewart E.
A1  - Kortemme, Tanja
A1  - Schueler-Furman, Ora
A1  - Misura, Kira M. S.
A1  - Morozov, Alexandre V.
A1  - Baker, David
T1  - Protein–protein docking predictions for the CAPRI experiment
JF  - Proteins: Structure, Function, and Bioinformatics
JA  - Proteins
VL  - 52
IS  - 1
PB  - Wiley Subscription Services, Inc., A Wiley Company
SN  - 1097-0134
UR  - http://dx.doi.org/10.1002/prot.10384
M3  - doi: 10.1002/prot.10384
SP  - 118
EP  - 122
KW  - protein binding
KW  - protein interactions
KW  - biomolecular free energy function
KW  - high-resolution refinement
KW  - flexible side chains
Y1  - 2003
ER  -
TY  - JOUR
AU  - Kortemme, Tanja
AU  - Joachimiak, Lukasz A.
AU  - Bullock, Alex N.
AU  - Schuler, Aaron D.
AU  - Stoddard, Barry L.
AU  - Baker, David
TI  - Computational redesign of protein-protein interaction specificity
JA  - Nature Structural & Molecular Biology
PY  - 2004/04//print
VL  - 11
IS  - 4
SP  - 371
EP  - 379
SN  - 1545-9993
UR  - http://dx.doi.org/10.1038/nsmb749
M3  - doi: 10.1038/nsmb749
N1  - 10.1038/nsmb749
L3  - http://www.nature.com/nsmb/journal/v11/n4/suppinfo/nsmb749_S1.html
ER  -
TY  - JOUR
T1  - Computational design of protein–protein interactions
JO  - Current Opinion in Chemical Biology
VL  - 8
IS  - 1
SP  - 91
EP  - 97
PY  - 2004/2//
T2  -
AU  - Kortemme, Tanja
AU  - Baker, David
SN  - 1367-5931
M3  - doi: 10.1016/j.cbpa.2003.12.008
UR  - http://www.sciencedirect.com/science/article/pii/S1367593103001777
ER  -
TY  - JOUR
T1  - An Orientation-dependent Hydrogen Bonding Potential Improves Prediction of Specificity and Structure for Proteins and Protein–Protein Complexes
JO  - Journal of Molecular Biology
VL  - 326
IS  - 4
SP  - 1239
EP  - 1259
PY  - 2003/2/28/
T2  -
AU  - Kortemme, Tanja
AU  - Morozov, Alexandre V.
AU  - Baker, David
SN  - 0022-2836
M3  - doi: 10.1016/S0022-2836(03)00021-4
UR  - http://www.sciencedirect.com/science/article/pii/S0022283603000214
KW  - hydrogen bond
KW  - electrostatics
KW  - protein docking
KW  - protein design
KW  - free energy function
ER  -
TY  - JOUR
T1  - Evaluation of Models of Electrostatic Interactions in Proteins
AU  - Morozov, Alexandre V.
AU  - Kortemme, Tanja
AU  - Baker, David
Y1  - 2003/02/07
PY  - 2003
DA  - 2003/03/01
N1  - doi: 10.1021/jp0267555
DO  - 10.1021/jp0267555
T2  - The Journal of Physical Chemistry B
JF  - The Journal of Physical Chemistry B
JO  - The Journal of Physical Chemistry B
SP  - 2075
EP  - 2090
VL  - 107
IS  - 9
PB  - American Chemical Society
SN  - 1520-6106
M3  - doi: 10.1021/jp0267555
UR  - http://dx.doi.org/10.1021/jp0267555
Y2  - 2011/12/13
ER  -
TY  - JOUR
A1  - Kortemme, Tanja
A1  - Kim, David E.
A1  - Baker, David
T1  - Computational Alanine Scanning of Protein-Protein Interfaces
Y1  - 2004/2/10
JF  - Science Signaling
JO  - Sci. STKE
SP  - pl2
EP  -
VL  - 2004
IS  - 219
UR  - http://stke.sciencemag.org/cgi/content/abstract/sigtrans;2004/219/pl2
N2  - Protein-protein interactions are key components of all signal transduction processes, so methods to alter these interactions promise to become important tools in dissecting function of connectivities in these networks. We have developed a fast computational approach for the prediction of energetically important amino acid residues in protein-protein interfaces (available at http://robetta.bakerlab.org/alaninescan), which we, following Peter Kollman, have termed "computational alanine scanning." The input consists of a three-dimensional structure of a protein-protein complex; output is a list of "hot spots," or amino acid side chains that are predicted to significantly destabilize the interface when mutated to alanine, analogous to the results of experimental alanine-scanning mutagenesis. 79% of hot spots and 68% of neutral residues were correctly predicted in a test of 233 mutations in 19 protein-protein complexes. A single interface can be analyzed in minutes. The computational methodology has been validated by the successful design of protein interfaces with new specificity and activity, and has yielded new insights into the mechanisms of receptor specificity and promiscuity in biological systems.
N1  - doi: 10.1126/stke.2192004pl2
ER  -
TY  - JOUR
A1  - Morozov, Alexandre V.
A1  - Kortemme, Tanja
A1  - Tsemekhman, Kiril
A1  - Baker, David
T1  - Close agreement between the orientation dependence of hydrogen bonds observed in protein structures and quantum mechanical calculations
Y1  - 2004/05/04
JF  - Proceedings of the National Academy of Sciences
JO  - Proceedings of the National Academy of Sciences
SP  - 6946
EP  - 6951
N1  - doi: 10.1073/pnas.0307578101
VL  - 101
IS  - 18
UR  - http://www.pnas.org/content/101/18/6946.abstract
N2  - Hydrogen bonding is a key contributor to the exquisite specificity of the interactions within and between biological macromolecules, and hence accurate modeling of such interactions requires an accurate description of hydrogen bonding energetics. Here we investigate the orientation and distance dependence of hydrogen bonding energetics by combining two quite disparate but complementary approaches: quantum mechanical electronic structure calculations and protein structural analysis. We find a remarkable agreement between the energy landscapes obtained from the electronic structure calculations and the distributions of hydrogen bond geometries observed in protein structures. In contrast, molecular mechanics force fields commonly used for biomolecular simulations do not consistently exhibit close correspondence to either quantum mechanical calculations or experimentally observed hydrogen bonding geometries. These results suggest a route to improved energy functions for biological macromolecules that combines the generality of quantum mechanical electronic structure calculations with the accurate context dependence implicit in protein structural analysis.
ER  -
TY  - JOUR
A1  - Chen, Yu
A1  - Kortemme, Tanja
A1  - Robertson, Tim
A1  - Baker, David
A1  - Varani, Gabriele
T1  - A new hydrogen-bonding potential for the design of protein–RNA interactions predicts specific contacts and discriminates decoys
Y1  - 2004/01/01
JF  - Nucleic Acids Research
JO  - Nucleic Acids Research
SP  - 5147
EP  - 5162
N1  - doi: 10.1093/nar/gkh785
VL  - 32
IS  - 17
UR  - http://nar.oxfordjournals.org/content/32/17/5147.abstract
N2  - RNA-binding proteins play many essential roles in the regulation of gene expression in the cell. Despite the significant increase in the number of structures for RNA–protein complexes in the last few years, the molecular basis of specificity remains unclear even for the best-studied protein families. We have developed a distance and orientation-dependent hydrogen-bonding potential based on the statistical analysis of hydrogen-bonding geometries that are observed in high-resolution crystal structures of protein–DNA and protein–RNA complexes. We observe very strong geometrical preferences that reflect significant energetic constraints on the relative placement of hydrogen-bonding atom pairs at protein–nucleic acid interfaces. A scoring function based on the hydrogen-bonding potential discriminates native protein–RNA structures from incorrectly docked decoys with remarkable predictive power. By incorporating the new hydrogen-bonding potential into a physical model of protein–RNA interfaces with full atom representation, we were able to recover native amino acids at protein–RNA interfaces.
ER  -
TY  - JOUR
A1  - Jiang, Lin
A1  - Kuhlman, Brian
A1  - Kortemme, Tanja
A1  - Baker, David
T1  - A “solvated rotamer” approach to modeling water-mediated hydrogen bonds at protein–protein interfaces
JF  - Proteins: Structure, Function, and Bioinformatics
JA  - Proteins
VL  - 58
IS  - 4
PB  - Wiley Subscription Services, Inc., A Wiley Company
SN  - 1097-0134
UR  - http://dx.doi.org/10.1002/prot.20347
M3  - doi: 10.1002/prot.20347
SP  - 893
EP  - 904
KW  - hydration
KW  - solvent modeling
KW  - water-mediated hydrogen bonds
KW  - free-energy function
KW  - protein design
KW  - protein–protein interactions
Y1  - 2005
ER  -
TY  - JOUR
T1  - Symmetry Recognizing Asymmetry: Analysis of the Interactions between the C-Type Lectin-like Immunoreceptor NKG2D and MHC Class I-like Ligands
JO  - Structure
VL  - 11
IS  - 4
SP  - 411
EP  - 422
PY  - 2003/4//
T2  -
AU  - McFarland, Benjamin J.
AU  - Kortemme, Tanja
AU  - Yu, Shuyuarn F.
AU  - Baker, David
AU  - Strong, Roland K.
SN  - 0969-2126
M3  - doi: 10.1016/S0969-2126(03)00047-9
UR  - http://www.sciencedirect.com/science/article/pii/S0969212603000479
KW  - immunoreceptors
KW  - MHC class I homologs
KW  - structural immunology
KW  - molecular recognition
KW  - computational alanine scanning
KW  - interface plasticity
ER  -
TY  - JOUR
T1  - Convergent Mechanisms for Recognition of Divergent Cytokines by the Shared Signaling Receptor gp130
JO  - Molecular Cell
VL  - 12
IS  - 3
SP  - 577
EP  - 589
PY  - 2003/9//
T2  -
AU  - Boulanger, Martin J.
AU  - Bankovich, Alexander J.
AU  - Kortemme, Tanja
AU  - Baker, David
AU  - Garcia, K. Christopher
SN  - 1097-2765
M3  - doi: 10.1016/S1097-2765(03)00365-4
UR  - http://www.sciencedirect.com/science/article/pii/S1097276503003654
ER  -
TY  - JOUR
T1  - Contributions of Amino Acid Side Chains to the Kinetics and Thermodynamics of the Bivalent Binding of Protein L to Ig κ Light Chain
AU  - Svensson, Henrik G.
AU  - Wedemeyer, William J.
AU  - Ekstrom, Jennifer L.
AU  - Callender, David R.
AU  - Kortemme, Tanja
AU  - Kim, David E.
AU  - Sjöbring, Ulf
AU  - Baker, David
Y1  - 2004/02/13
PY  - 2004
DA  - 2004/03/01
N1  - doi: 10.1021/bi034873s
DO  - 10.1021/bi034873s
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 2445
EP  - 2457
VL  - 43
IS  - 9
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi034873s
UR  - http://dx.doi.org/10.1021/bi034873s
Y2  - 2011/12/13
ER  -
TY  - JOUR
T1  - Aromatic side-chain contribution to far-ultraviolet circular dichroism of helical peptides and its effect on measurement of helix propensities
AU  - Chakrabartty, Avijit
AU  - Kortemme, Tanja
AU  - Padmanabhan, S.
AU  - Baldwin, Robert L.
Y1  - 1993/06/01
PY  - 1993
DA  - 1993/06/01
N1  - doi: 10.1021/bi00072a010
DO  - 10.1021/bi00072a010
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 5560
EP  - 5565
VL  - 32
IS  - 21
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi00072a010
UR  - http://dx.doi.org/10.1021/bi00072a010
Y2  - 2011/12/13
ER  -
TY  - JOUR
A1  - Chakrabartty, Avijit
A1  - Kortemme, Tanja
A1  - Baldwin, Robert L.
T1  - Helix propensities of the amino acids measured in alanine-based peptides without helix-stabilizing side-chain interactions
JF  - Protein Science
JA  - Protein Science
VL  - 3
IS  - 5
PB  - Cold Spring Harbor Laboratory Press
SN  - 1469-896X
UR  - http://dx.doi.org/10.1002/pro.5560030514
M3  - doi: 10.1002/pro.5560030514
SP  - 843
EP  - 852
KW  - alanine-based peptides
KW  - helix capping
KW  - helix propensities
KW  - helix stability
KW  - modified Lifson-Roig theory
KW  - peptide helices
KW  - protein folding
Y1  - 1994
ER  -
TY  - JOUR
A1  - Kortemme, Tanja
A1  - Ramı́rez-Alvarado, Marina
A1  - Serrano, Luis
T1  - Design of a 20-Amino Acid, Three-Stranded β-Sheet Protein
Y1  - 1998/07/10
JF  - Science
JO  - Science
SP  - 253
EP  - 256
N1  - doi: 10.1126/science.281.5374.253
VL  - 281
IS  - 5374
UR  - http://www.sciencemag.org/content/281/5374/253.abstract
N2  - A 20-residue protein (named Betanova) forming a monomeric, three-stranded, antiparallel β sheet was designed using a structural backbone template and an iterative hierarchical approach. Structural and physicochemical characterization show that the β-sheet conformation is stabilized by specific tertiary interactions and that the protein exhibits a cooperative two-state folding-unfolding transition, which is a hallmark of natural proteins. The Betanova molecule constitutes a tractable model system to aid in the understanding of β-sheet formation, including β-sheet aggregation and amyloid fibril formation.
ER  -
TY  - JOUR
T1  - β-Hairpin and β-sheet formation in designed linear peptides
JO  - Bioorganic & Medicinal Chemistry
VL  - 7
IS  - 1
SP  - 93
EP  - 103
PY  - 1999/1//
T2  -
AU  - Ramı́rez-Alvarado, Marina
AU  - Kortemme, Tanja
AU  - Blanco, Francisco J.
AU  - Serrano, Luis
SN  - 0968-0896
M3  - doi: 10.1016/S0968-0896(98)00215-6
UR  - http://www.sciencedirect.com/science/article/pii/S0968089698002156
KW  - β-hairpin
KW  - β-sheet
KW  - peptides
KW  - protein folding
KW  - NMR
ER  -
TY  - JOUR
T1  - The design of linear peptides that fold as monomeric β-sheet structures
JO  - Current Opinion in Structural Biology
VL  - 9
IS  - 4
SP  - 487
EP  - 493
PY  - 1999/8//
T2  -
AU  - Lacroix, Emmanuel
AU  - Kortemme, Tanja
AU  - de la Paz, Manuela Lopez
AU  - Serrano, Luis
SN  - 0959-440X
M3  - doi: 10.1016/S0959-440X(99)80069-4
UR  - http://www.sciencedirect.com/science/article/pii/S0959440X99800694
ER  -
TY  - JOUR
T1  - Comparison of the (30-51, 14-38) Two-disulphide Folding Intermediates of the Homologous Proteins Dendrotoxin K and Bovine Pancreatic Trypsin Inhibitor by Two-dimensional1H Nuclear Magnetic Resonance
JO  - Journal of Molecular Biology
VL  - 257
IS  - 1
SP  - 188
EP  - 198
PY  - 1996/3/22/
T2  -
AU  - Kortemme, Tanja
AU  - Hollecker, Michelle
AU  - Kemmink, Johan
AU  - Creighton, Thomas E.
SN  - 0022-2836
M3  - doi: 10.1006/jmbi.1996.0155
UR  - http://www.sciencedirect.com/science/article/pii/S0022283696901552
KW  - BPTI
KW  - protein folding
KW  - disulphide bonds
KW  - NMR
KW  - dendrotoxin
ER  -
TY  - JOUR
T1  - Similarities between the spectrin SH3 domain denatured state and its folding transition state
JO  - Journal of Molecular Biology
VL  - 297
IS  - 5
SP  - 1217
EP  - 1229
PY  - 2000/4/14/
T2  -
AU  - Kortemme, Tanja
AU  - Kelly, Mark J. S.
AU  - Kay, Lewis E.
AU  - Forman-Kay, Julie
AU  - Serrano, Luis
SN  - 0022-2836
M3  - doi: 10.1006/jmbi.2000.3618
UR  - http://www.sciencedirect.com/science/article/pii/S0022283600936180
KW  - denatured state ensemble
KW  - transition state
KW  - protein folding
KW  - NMR
KW  - deuteration
ER  -
TY  - JOUR
T1  - Simple Physical Models Connect Theory and Experiment in Protein Folding Kinetics
JO  - Journal of Molecular Biology
VL  - 322
IS  - 2
SP  - 463
EP  - 476
PY  - 2002/9/13/
T2  -
AU  - Alm, Eric
AU  - Morozov, Alexandre V.
AU  - Kortemme, Tanja
AU  - Baker, David
SN  - 0022-2836
M3  - doi: 10.1016/S0022-2836(02)00706-4
UR  - http://www.sciencedirect.com/science/article/pii/S0022283602007064
KW  - protein folding
KW  - transition state
KW  - kinetics
KW  - φ-values
KW  - master equation
ER  -
TY  - JOUR
T1  - Ionisation of Cysteine Residues at the Termini of Model α-Helical Peptides. Relevance to Unusual Thiol pKa Values in Proteins of the Thioredoxin Family
JO  - Journal of Molecular Biology
VL  - 253
IS  - 5
SP  - 799
EP  - 812
PY  - 1995/11/10/
T2  -
AU  - Kortemme, Tanja
AU  - Creighton, Thomas E.
SN  - 0022-2836
M3  - doi: 10.1006/jmbi.1995.0592
UR  - http://www.sciencedirect.com/science/article/pii/S002228368570592X
KW  - α-helix dipole
KW  - electrostatic interactions
KW  - cysteine residues
KW  - thioredoxin
KW  - DsbA
ER  -
TY  - JOUR
T1  - Electrostatic Interactions in the Active Site of the N-Terminal Thioredoxin-like Domain of Protein Disulfide Isomerase
AU  - Kortemme, Tanja
AU  - Darby, Nigel J.
AU  - Creighton, Thomas E.
Y1  - 1996/01/01
PY  - 1996
DA  - 1996/01/01
N1  - doi: 10.1021/bi9617724
DO  - 10.1021/bi9617724
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 14503
EP  - 14511
VL  - 35
IS  - 46
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi9617724
UR  - http://dx.doi.org/10.1021/bi9617724
Y2  - 2011/12/13
ER  -
TY  - JOUR
T1  - Ionization−Reactivity Relationships for Cysteine Thiols in Polypeptides
AU  - Bulaj, Grzegorz
AU  - Kortemme, Tanja
AU  - Goldenberg, David P.
Y1  - 1998/06/01
PY  - 1998
DA  - 1998/06/01
N1  - doi: 10.1021/bi973101r
DO  - 10.1021/bi973101r
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 8965
EP  - 8972
VL  - 37
IS  - 25
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi973101r
UR  - http://dx.doi.org/10.1021/bi973101r
Y2  - 2011/12/13
ER  -
TY  - JOUR
A1  - Zwiers, Antonie
A1  - Kraal, Laurens
A1  - van de Pouw Kraan, Tineke C. T. M.
A1  - Wurdinger, Thomas
A1  - Bouma, Gerd
A1  - Kraal, Georg
T1  - Cutting Edge: A Variant of the IL-23R Gene Associated with Inflammatory Bowel Disease Induces Loss of MicroRNA Regulation and Enhanced Protein Production
Y1  - 2012/02/15
JF  - The Journal of Immunology
JO  - The Journal of Immunology
SP  - 1573
EP  - 1577
N1  - doi: 10.4049/jimmunol.1101494
VL  - 188
IS  - 4
UR  - http://jimmunol.org/content/188/4/1573.abstract
N2  - IL-23R gene variants have been identified as risk factors for two major inflammatory bowel diseases (IBDs), Crohn’s disease and ulcerative colitis, but how they contribute to disease is poorly understood. In this study, we show that the rs10889677 variant in the 3′-untranslated region of the IL-23R gene displays enhanced levels of both mRNA and protein production of IL-23R. This can be attributed to a loss of binding capacity for the microRNAs (miRNAs) Let-7e and Let-7f by the variant allele. Indeed, inhibition and overexpression of these miRNAs influenced the expression of the wild type but not the variant allele. Our data clearly demonstrate a role for miRNA-mediated dysregulation of IL-23R signaling, correlated with a single nucleotide polymorphism in the IL-23R strongly associated with IBD susceptibility. This implies that this mutation, in combination with other genetic risk factors, can lead to disease through sustained IL-23R signaling, contributing to the chronicity of IBD.
ER  -
TY  - JOUR
A1  - Isaacs, Farren J.
A1  - Carr, Peter A.
A1  - Wang, Harris H.
A1  - Lajoie, Marc J.
A1  - Sterling, Bram
A1  - Kraal, Laurens
A1  - Tolonen, Andrew C.
A1  - Gianoulis, Tara A.
A1  - Goodman, Daniel B.
A1  - Reppas, Nikos B.
A1  - Emig, Christopher J.
A1  - Bang, Duhee
A1  - Hwang, Samuel J.
A1  - Jewett, Michael C.
A1  - Jacobson, Joseph M.
A1  - Church, George M.
T1  - Precise Manipulation of Chromosomes in Vivo Enables Genome-Wide Codon Replacement
Y1  - 2011/07/15
JF  - Science
JO  - Science
SP  - 348
EP  - 353
N1  - doi: 10.1126/science.1205822
VL  - 333
IS  - 6040
UR  - http://www.sciencemag.org/content/333/6040/348.abstract
N2  - We present genome engineering technologies that are capable of fundamentally reengineering genomes from the nucleotide to the megabase scale. We used multiplex automated genome engineering (MAGE) to site-specifically replace all 314 TAG stop codons with synonymous TAA codons in parallel across 32 Escherichia coli strains. This approach allowed us to measure individual recombination frequencies, confirm viability for each modification, and identify associated phenotypes. We developed hierarchical conjugative assembly genome engineering (CAGE) to merge these sets of codon modifications into genomes with 80 precise changes, which demonstrate that these synonymous codon substitutions can be combined into higher-order strains without synthetic lethal effects. Our methods treat the chromosome as both an editable and an evolvable template, permitting the exploration of vast genetic landscapes.
ER  -
TY  - JOUR
T1  - A Test on Peptide Stability of AMBER Force Fields with Implicit Solvation
AU  - Shell, M. Scott
AU  - Ritterson, Ryan S.
AU  - Dill, Ken A.
Y1  - 2008/05/10
PY  - 2008
DA  - 2008/06/01
N1  - doi: 10.1021/jp800282x
DO  - 10.1021/jp800282x
T2  - The Journal of Physical Chemistry B
JF  - The Journal of Physical Chemistry B
JO  - The Journal of Physical Chemistry B
SP  - 6878
EP  - 6886
VL  - 112
IS  - 22
PB  - American Chemical Society
SN  - 1520-6106
M3  - doi: 10.1021/jp800282x
UR  - http://dx.doi.org/10.1021/jp800282x
Y2  - 2011/12/16
ER  -
TY  - JOUR
T1  - Widespread Protein Aggregation as an Inherent Part of Aging in <italic>C. elegans</italic>
A1  - David, Della C.
A1  - Ollikainen, Noah
A1  - Trinidad, Jonathan C.
A1  - Cary, Michael P.
A1  - Burlingame, Alma L.
A1  - Kenyon, Cynthia
Y1  - 2010/08/10
N2  - <p>Several hundred proteins become insoluble and aggregation-prone as a consequence of aging in <italic>Caenorhabditis elegans</italic>. The data indicate that these proteins influence disease-related protein aggregation and toxicity.</p>
JF  - PLoS Biology
JA  - PLoS Biology
VL  - 8
IS  - 8
UR  - http://dx.doi.org/10.1371%2Fjournal.pbio.1000450
SP  - e1000450
EP  -
PB  - Public Library of Science
M3  - doi: 10.1371/journal.pbio.1000450
ER  -
TY  - JOUR
A1  - Gupta, Nitin
A1  - Benhamida, Jamal
A1  - Bhargava, Vipul
A1  - Goodman, Daniel B.
A1  - Kain, Elisabeth
A1  - Kerman, Ian
A1  - Nguyen, Ngan
A1  - Ollikainen, Noah
A1  - Rodriguez, Jesse
A1  - Wang, Jian
A1  - Lipton, Mary S.
A1  - Romine, Margaret
A1  - Bafna, Vineet
A1  - Smith, Richard D.
A1  - Pevzner, Pavel A.
T1  - Comparative proteogenomics: Combining mass spectrometry and comparative genomics to analyze multiple genomes
Y1  - 2008/07/01
JF  - Genome Research
JO  - Genome Research
SP  - 1133
EP  - 1142
N1  - doi: 10.1101/gr.074344.107
VL  - 18
IS  - 7
UR  - http://genome.cshlp.org/content/18/7/1133.abstract
N2  - Recent proliferation of low-cost DNA sequencing techniques will soon lead to an explosive growth in the number of sequenced genomes and will turn manual annotations into a luxury. Mass spectrometry recently emerged as a valuable technique for proteogenomic annotations that improves on the state-of-the-art in predicting genes and other features. However, previous proteogenomic approaches were limited to a single genome and did not take advantage of analyzing mass spectrometry data from multiple genomes at once. We show that such a comparative proteogenomics approach (like comparative genomics) allows one to address the problems that remained beyond the reach of the traditional “single proteome” approach in mass spectrometry. In particular, we show how comparative proteogenomics addresses the notoriously difficult problem of “one-hit-wonders” in proteomics, improves on the existing gene prediction tools in genomics, and allows identification of rare post-translational modifications. We therefore argue that complementing DNA sequencing projects by comparative proteogenomics projects can be a viable approach to improve both genomic and proteomic annotations.
ER  -
TY  - JOUR
AU  - Baker, Michael E.
AU  - Chandsawangbhuwana, Charlie
AU  - Ollikainen, Noah
PY  - 2007
IS  - 1
M3  - doi: 10.1186/1471-2148-7-24
SP  - 24
T1  - Structural analysis of the evolution of steroid specificity in the mineralocorticoid and glucocorticoid receptors
JO  - BMC Evolutionary Biology
UR  - http://www.biomedcentral.com/1471-2148/7/24
VL  - 7
SN  - 1471-2148
N2  - BACKGROUND:The glucocorticoid receptor (GR) and mineralocorticoid receptor (MR) evolved from a common ancestor. Still not completely understood is how specificity for glucocorticoids (e.g. cortisol) and mineralocorticoids (e.g. aldosterone) evolved in these receptors.RESULTS:Our analysis of several vertebrate GRs and MRs in the context of 3D structures of human GR and MR indicates that with the exception of skate GR, a cartilaginous fish, there is a deletion in all GRs, at the position corresponding to Ser-949 in human MR. This deletion occurs in a loop before helix 12, which contains the activation function 2 (AF2) domain, which binds coactivator proteins and influences transcriptional activity of steroids. Unexpectedly, we find that His-950 in human MR, which is conserved in the MR in chimpanzee, orangutan and macaque, is glutamine in all teleost and land vertebrate MRs, including New World monkeys and prosimians.CONCLUSION:Evolution of differences in the responses of the GR and MR to corticosteroids involved deletion in the GR of a residue corresponding to Ser-949 in human MR. A mutation corresponding to His-950 in human MR may have been important in physiological changes associated with emergence of Old World monkeys from prosimians.
ER  -
TY  - JOUR
A1  - Ollikainen, Noah
A1  - Chandsawangbhuwana, Charlie
A1  - Baker, Michael E.
T1  - Evolution of the thyroid hormone, retinoic acid, ecdysone and liver X receptors
Y1  - 2006/08/30
JF  - Integrative and Comparative Biology
JO  - Integrative and Comparative Biology
SP  - 815
EP  - 826
N1  - doi: 10.1093/icb/icl035
VL  - 46
IS  - 6
UR  - http://icb.oxfordjournals.org/content/46/6/815.abstract
N2  - Ecdysone and thyroid hormone are 2 ligands that have important roles in regulating metamorphosis in animals. Ecdysone is a steroid that regulates molting in insects. Thyroid hormone regulates differentiation and development in fish and amphibia. Although ecdysone and thyroid hormone have different chemical structures, both hormones act by binding to transcription factors that belong to the nuclear receptor family. We investigated the evolution of structure and function in the ecdysone receptor (EcR) and thyroid hormone receptor (TR), and liver X receptor (LXR) and retinoic acid receptor (RAR), which cluster with EcR and TR, respectively (Bertrand S, Brunet FG, Escriva H, Parmentier G, Laudet V, Robinson-Rechavi M. 2004. Mol Biol Evol 21:1923–37), by constructing a multiple alignment of their sequences and calculating ancestral sequences for TR, RAR, EcR, and LXR. These alignments were mapped onto the 3D structures of TR, RAR, EcR, and LXR in the Protein Data Bank to examine the evolution of amino acids involved in the binding of ligands to TR, RAR, EcR, and LXR.
ER  -
TY  - JOUR
PB  - American Physical Society
ID  - doi: 10.1103/PhysRevE.74.051801
TI  - Secondary structures in long compact polymers
JF  - Physical Review E
JA  - Physical Review E
J1  - PRE
VL  - 74
IS  - 5
SP  - 051801
EP  -
PY  - 2006/11/01/
UR  - http://link.aps.org/doi/10.1103/PhysRevE.74.051801
A1  - Oberdorf, Richard
AU  - Ferguson, Allison
AU  - Jacobsen, Jesper L.
AU  - Kondev, Jané
ER  -




TY  - JOUR
T1  - Dynamics of Light-Induced Activation in the PAS Domain Proteins LOV2 and PYP Probed by Time-Resolved Tryptophan Fluorescence
AU  - Hoersch, Daniel
AU  - Bolourchian, Farzin
AU  - Otto, Harald
AU  - Heyn, Maarten P.
AU  - Bogomolni, Roberto A.
Y1  - 2010/11/22
PY  - 2010
DA  - 2010/12/28
N1  - doi: 10.1021/bi101413v
DO  - 10.1021/bi101413v
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 10811
EP  - 10817
VL  - 49
IS  - 51
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi101413v
UR  - http://dx.doi.org/10.1021/bi101413v
Y2  - 2011/12/16
ER  -
TY  - JOUR
T1  - Strong Hydrogen Bond between Glutamic Acid 46 and Chromophore Leads to the Intermediate Spectral Form and Excited State Proton Transfer in the Y42F Mutant of the Photoreceptor Photoactive Yellow Protein
AU  - Joshi, Chandra P.
AU  - Otto, Harald
AU  - Hoersch, Daniel
AU  - Meyer, Terry E.
AU  - Cusanovich, Michael A.
AU  - Heyn, Maarten P.
Y1  - 2009/09/20
PY  - 2009
DA  - 2009/10/27
N1  - doi: 10.1021/bi9012897
DO  - 10.1021/bi9012897
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 9980
EP  - 9993
VL  - 48
IS  - 42
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi9012897
UR  - http://dx.doi.org/10.1021/bi9012897
Y2  - 2011/12/16
ER  -
TY  - JOUR
T1  - Time-resolved spectroscopy of dye-labeled photoactive yellow protein suggests a pathway of light-induced structural changes in the N-terminal cap
A1  - Hoersch, Daniel
A1  - Otto, Harald
A1  - Cusanovich, Michael A.
A1  - Heyn, Maarten P.
Y1  - 2009
SP  - 5437
EP  - 5444
JF  - Physical Chemistry Chemical Physics
JO  - Physical Chemistry Chemical Physics
VL  - 11
IS  - 26
PB  - The Royal Society of Chemistry
SN  - 1463-9076
M3  - doi: 10.1039/B821345C
UR  - http://dx.doi.org/10.1039/B821345C
N2  - The photoreceptor PYP responds to light activation with global conformational changes. These changes are mainly located in the N-terminal cap of the protein, which is [similar]20 A away from the chromophore binding pocket and separated from it by the central [small beta]-sheet. The question of the propagation of the structural change across the central [small beta]-sheet is of general interest for the superfamily of PAS domain proteins, for which PYP is the structural prototype. Here we measured the kinetics of the structural changes in the N-terminal cap by transient absorption spectroscopy on the ns to second timescale. For this purpose the cysteine mutants A5C and N13C were prepared and labeled with thiol reactive 5-iodoacetamidofluorescein (IAF). A5 is located close to the N-terminus, while N13 is part of helix [small alpha]1 near the functionally important salt bridge E12-K110 between the N-terminal cap and the central anti-parallel [small beta]-sheet. The absorption spectrum of the dye is sensitive to its environment, and serves as a sensor for conformational changes near the labeling site. In both labeled mutants light activation results in a transient red-shift of the fluorescein absorption spectrum. To correlate the conformational changes with the photocycle intermediates of the protein, we compared the kinetics of the transient absorption signal of the dye with that of the -hydroxycinnamoyl chromophore. While the structural change near A5 is synchronized with the rise of the I intermediate, which is formed in [similar]200 [small mu ]s, the change near N13 is delayed and rises with the next intermediate I[prime or minute], which forms in [similar]2 ms. This indicates that different parts of the N-terminal cap respond to light activation with different kinetics. For the signaling pathway of photoactive yellow protein we propose a model in which the structural signal propagates from the chromophore binding pocket across the central [small beta]-sheet the N-terminal region to helix [small alpha]1, resulting in a large change in the protein conformation.
ER  -
TY  - JOUR
T1  - Monitoring the Conformational Changes of Photoactivated Rhodopsin from Μicroseconds to Seconds by Transient Fluorescence Spectroscopy†
AU  - Hoersch, Daniel
AU  - Otto, Harald
AU  - Wallat, Ingrid
AU  - Heyn, Maarten P.
Y1  - 2008/10/11
PY  - 2008
DA  - 2008/11/04
N1  - doi: 10.1021/bi801397e
DO  - 10.1021/bi801397e
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 11518
EP  - 11527
VL  - 47
IS  - 44
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi801397e
UR  - http://dx.doi.org/10.1021/bi801397e
Y2  - 2011/12/16
ER  -
TY  - JOUR
T1  - Distinguishing Chromophore Structures of Photocycle Intermediates of the Photoreceptor PYP by Transient Fluorescence and Energy Transfer§
AU  - Hoersch, Daniel
AU  - Otto, Harald
AU  - Cusanovich, Michael A.
AU  - Heyn, Maarten P.
Y1  - 2008/07/01
PY  - 2008
DA  - 2008/07/01
N1  - doi: 10.1021/jp801174z
DO  - 10.1021/jp801174z
T2  - The Journal of Physical Chemistry B
JF  - The Journal of Physical Chemistry B
JO  - The Journal of Physical Chemistry B
SP  - 9118
EP  - 9125
VL  - 112
IS  - 30
PB  - American Chemical Society
SN  - 1520-6106
M3  - doi: 10.1021/jp801174z
UR  - http://dx.doi.org/10.1021/jp801174z
Y2  - 2011/12/16
ER  -
TY  - JOUR
T1  - Role of a Conserved Salt Bridge between the PAS Core and the N-Terminal Domain in the Activation of the Photoreceptor Photoactive Yellow Protein
JO  - Biophysical Journal
VL  - 93
IS  - 5
SP  - 1687
EP  - 1699
PY  - 2007/9/1/
T2  -
AU  - Hoersch, Daniel
AU  - Otto, Harald
AU  - Joshi, Chandra P.
AU  - Borucki, Berthold
AU  - Cusanovich, Michael A.
AU  - Heyn, Maarten P.
SN  - 0006-3495
M3  - doi: 10.1529/biophysj.107.106633
UR  - http://www.sciencedirect.com/science/article/pii/S000634950771425X
ER  -
TY  - JOUR
T1  - Time-Resolved Single Tryptophan Fluorescence in Photoactive Yellow Protein Monitors Changes in the Chromophore Structure during the Photocycle via Energy Transfer†
AU  - Otto, Harald
AU  - Hoersch, Daniel
AU  - Meyer, Terry E.
AU  - Cusanovich, Michael A.
AU  - Heyn, Maarten P.
Y1  - 2005/12/01
PY  - 2005
DA  - 2005/12/01
N1  - doi: 10.1021/bi051448l
DO  - 10.1021/bi051448l
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 16804
EP  - 16816
VL  - 44
IS  - 51
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi051448l
UR  - http://dx.doi.org/10.1021/bi051448l
Y2  - 2011/12/16
ER  -
TY  - JOUR
A1  - Itzhaki, Zohar
A1  - Akiva, Eyal
A1  - Margalit, Hanah
T1  - Preferential use of protein domain pairs as interaction mediators: order and transitivity
Y1  - 2010/10/15
JF  - Bioinformatics
JO  - Bioinformatics
SP  - 2564
EP  - 2570
N1  - doi: 10.1093/bioinformatics/btq495
VL  - 26
IS  - 20
UR  - http://bioinformatics.oxfordjournals.org/content/26/20/2564.abstract
N2  - Motivation: Many protein–protein interactions (PPIs) are mediated by protein domains. The structural data of multi-domain PPIs reveal the domain pair (or pairs) that mediate a PPI, and implicitly also the domain pairs that are not involved in the interaction. By analyzing such data, preference relations between domain pairs as interaction mediators may be revealed.Results: Here, we analyze the differential use of domain pairs as mediators of stable interactions based on structurally solved multi-domain protein complexes. Our analysis revealed domain pairs that are preferentially used as interaction mediators and domain pairs that rarely or never mediate interaction, independent of the proteins' context. Between these extremes, there are domain pairs that mediate protein interaction in some protein contexts, while in other contexts different domain pairs predominate over them. By describing the preference relations between domain pairs as a network, we uncovered partial order and transitivity in these relations, which we further exploited for predicting interaction-mediating domains. The preferred domain pairs and the ones over which they predominate differ in several properties, but these differences cannot yet determine explicitly what underlies the differential use of domain pairs as interaction mediators. One property that stood up was the over-abundance of homotypic interactions among the preferred domain pairs, supporting previous suggestions on the advantages in the use of domain self-interaction for mediating protein interactions. Finally, we show a possible association between the preferred domain pairs and the function of the complex where they reside.Contact: hanahm@ekmd.huji.ac.ilSupplementary information: Supplementary data are available at Bioinformatics online.
ER  -
TY  - JOUR
A1  - Akiva, Eyal
A1  - Itzhaki, Zohar
A1  - Margalit, Hanah
T1  - Built-in loops allow versatility in domain–domain interactions: Lessons from self-interacting domains
Y1  - 2008/09/09
JF  - Proceedings of the National Academy of Sciences
JO  - Proceedings of the National Academy of Sciences
SP  - 13292
EP  - 13297
N1  - doi: 10.1073/pnas.0801207105
VL  - 105
IS  - 36
UR  - http://www.pnas.org/content/105/36/13292.abstract
N2  - Compilations of domain–domain interactions based on solved structures suggest there are distinct domain pairs that are used repeatedly in different protein contexts to mediate protein–protein interactions. However, not all protein pairs with the corresponding domains that can potentially mediate interaction do interact, even when they are colocalized and coexpressed. It is conceivable that there are structural and sequence features, below the domain level, that play a role in determining the potential of domains to mediate protein–protein interactions. Here, we discover such features by comparing domains that, on the one hand, mediate homodimerization of proteins and, on the other, occur in different proteins that are documented as monomers. Intriguingly, this comparison uncovered surface loops that can be considered as determinants of the interactions. There are enabling loops, which mediate the domain interactions, and disabling loops that prevent the interactions. The presence of the enabling/disabling loops is consistent with the fulfillment/prevention of the interaction and is highly preserved in evolution. This suggests that, along with the preservation of structural elements that enable interaction, evolution maintains elements intended to prevent unwanted interactions. The enabling and disabling loops discovered in this study have implications in prediction of protein–protein interactions, by pointing to the protein regions that determine the interaction. Our results extend the hierarchy of attributes that collectively establish the modularity of domain-mediated protein–protein interactions.
ER  -
TY  - JOUR
AU  - Itzhaki, Zohar
AU  - Akiva, Eyal
AU  - Altuvia, Yael
AU  - Margalit, Hanah
PY  - 2006
IS  - 12
M3  - doi: 10.1186/gb-2006-7-12-r125
SP  - R125
T1  - Evolutionary conservation of domain-domain interactions
JO  - Genome Biology
UR  - http://genomebiology.com/2006/7/12/R125
VL  - 7
SN  - 1465-6906
N2  - BACKGROUND:Recently, there has been much interest in relating domain-domain interactions (DDIs) to protein-protein interactions (PPIs) and vice versa, in an attempt to understand the molecular basis of PPIs.RESULTS:Here we map structurally derived DDIs onto the cellular PPI networks of different organisms and demonstrate that there is a catalog of domain pairs that is used to mediate various interactions in the cell. We show that these DDIs occur frequently in protein complexes and that homotypic interactions (of a domain with itself) are abundant. A comparison of the repertoires of DDIs in the networks of Escherichia coli, Saccharomyces cerevisiae, Caenorhabditis elegans, Drosophila melanogaster, and Homo sapiens shows that many DDIs are evolutionarily conserved.CONCLUSION:Our results indicate that different organisms use the same 'building blocks' for PPIs, suggesting that the functionality of many domain pairs in mediating protein interactions is maintained in evolution.
ER  -
TY  - JOUR
T1  - Directed Evolution of the Quorum-Sensing Regulator EsaR for Increased Signal Sensitivity
AU  - Shong, Jasmine
AU  - Huang, Yao-ming
AU  - Bystroff, Christopher
AU  - Collins, Cynthia H.
Y1  - 2013/01/30
PY  - 2013
N1  - doi: 10.1021/cb3006402
DO  - doi: 10.1021/cb3006402
T2  - ACS Chemical Biology
JF  - ACS Chemical Biology
JO  - ACS Chemical Biology
PB  - American Chemical Society
SN  - 1554-8929
M3  - doi: 10.1021/cb3006402
UR  - http://dx.doi.org/10.1021/cb3006402
Y2  - 2013/02/11
ER  -
TY  - CHAP
AU  - Crone, Donna E.
AU  - Huang, Yao-ming
AU  - Pitman, Derek J.
AU  - Schenkelberg, Christian
AU  - Fraser, Keith
AU  - Macari, Stephen
AU  - Bystroff, Christopher
A2  - Toonika Rinken
T1  - GFP-based Biosensors
BT  - State of the Art in Biosensors - General Aspects
VL  - 1
SP  - 669
EP  - 675
SN  - 978-953-51-1004-0
M3  - doi: 10.5772/52250
PY  - 2013
Y1  - 2013/01/01
ER  -
TY  - JOUR
A1  - Huang, Yao-ming
A1  - Nayak, Sasmita
A1  - Bystroff, Christopher
T1  - Quantitative in vivo solubility and reconstitution of truncated circular permutants of green fluorescent protein
JF  - Protein Science
JA  - Protein Science
VL  - 20
IS  - 11
PB  - Wiley Subscription Services, Inc., A Wiley Company
SN  - 1469-896X
UR  - http://dx.doi.org/10.1002/pro.735
M3  - doi: 10.1002/pro.735
SP  - 1775
EP  - 1780
KW  - protein folding
KW  - leave-one-out
KW  - GFP
KW  - reconstitution
KW  - circular permutant
Y1  - 2011
ER  -
TY  - JOUR
T1  - A Rewired Green Fluorescent Protein: Folding and Function in a Nonsequential, Noncircular GFP Permutant
AU  - Reeder, Philippa J.
AU  - Huang, Yao-ming
AU  - Dordick, Jonathan S.
AU  - Bystroff, Christopher
Y1  - 2010/11/23
PY  - 2010
DA  - 2010/12/28
N1  - doi: 10.1021/bi100975z
DO  - 10.1021/bi100975z
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 10773
EP  - 10779
VL  - 49
IS  - 51
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi100975z
UR  - http://dx.doi.org/10.1021/bi100975z
Y2  - 2011/12/16
ER  -
TY  - JOUR
T1  - Complementation and Reconstitution of Fluorescence from Circularly Permuted and Truncated Green Fluorescent Protein†
AU  - Huang, Yao-ming
AU  - Bystroff, Christopher
Y1  - 2009/01/13
PY  - 2009
DA  - 2009/02/10
N1  - doi: 10.1021/bi802027g
DO  - 10.1021/bi802027g
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 929
EP  - 940
VL  - 48
IS  - 5
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi802027g
UR  - http://dx.doi.org/10.1021/bi802027g
Y2  - 2011/12/16
ER  -
TY  - JOUR
A1  - Huang, Yao-ming
A1  - Bystroff, Christopher
T1  - Improved pairwise alignments of proteins in the Twilight Zone using local structure predictions
Y1  - 2006/02/15
JF  - Bioinformatics
JO  - Bioinformatics
SP  - 413
EP  - 422
N1  - doi: 10.1093/bioinformatics/bti828
VL  - 22
IS  - 4
UR  - http://bioinformatics.oxfordjournals.org/content/22/4/413.abstract
N2  - Motivation: In recent years, advances have been made in the ability of computational methods to discriminate between homologous and non-homologous proteins in the ‘twilight zone’ of sequence similarity, where the percent sequence identity is a poor indicator of homology. To make these predictions more valuable to the protein modeler, they must be accompanied by accurate alignments. Pairwise sequence alignments are inferences of orthologous relationships between sequence positions. Evolutionary distance is traditionally modeled using global amino acid substitution matrices. But real differences in the likelihood of substitutions may exist for different structural contexts within proteins, since structural context contributes to the selective pressure.Results: HMMSUM (HMMSTR-based substitution matrices) is a new model for structural context-based amino acid substitution probabilities consisting of a set of 281 matrices, each for a different sequence–structure context. HMMSUM does not require the structure of the protein to be known. Instead, predictions of local structure are made using HMMSTR, a hidden Markov model for local structure. Alignments using the HMMSUM matrices compare favorably to alignments carried out using the BLOSUM matrices or structure-based substitution matrices SDM and HSDM when validated against remote homolog alignments from BAliBASE. HMMSUM has been implemented using local Dynamic Programming and with the Bayesian Adaptive alignment method.Availability: Matrices, source codes and programs are available at http://www.bioinfo.rpi.edu/~bystrc/downloads.html.Contact: bystrc@rpi.edu, huangy2@rpi.edu
ER  -
TY  - JOUR
A1  - Huang, Yao-ming
A1  - Chen, Shee-Uan
A1  - Goodman, Steven D.
A1  - Wu, Shang-Hsin
A1  - Kao, Jau-Tsuen
A1  - Lee, Chun-Nan
A1  - Cheng, Wern-Cherng
A1  - Tsai, Keh-Sung
A1  - Fang, Woei-horng
T1  - Interaction of Nick-directed DNA Mismatch Repair and Loop Repair in Human Cells
Y1  - 2004/07/16
JF  - Journal of Biological Chemistry
JO  - Journal of Biological Chemistry
SP  - 30228
EP  - 30235
N1  - doi: 10.1074/jbc.M401675200
VL  - 279
IS  - 29
UR  - http://www.jbc.org/content/279/29/30228.abstract
N2  - In human cells, large DNA loop heterologies are repaired through a nick-directed pathway independent of mismatch repair. However, a 3′-nick generated by bacteriophage fd gene II protein heterology is not capable of stimulating loop repair. To evaluate the possibility that a mismatch near a loop could induce both repair types in human cell extracts, we constructed and tested a set of DNA heteroduplexes, each of which contains a combination of mismatches and loops. We have demonstrated that a strand break generated by restriction endonucleases 3′ to a large loop is capable of provoking and directing loop repair. The repair of 3′-heteroduplexes in human cell extracts is very similar to that of 5′-heteroduplex repair, being strand-specific and highly biased to the nicked strand. This observation suggests that the loop repair pathway possesses bidirectional repair capability similar to that of the bacterial loop repair system. We also found that a nick 5′ to a coincident mismatch and loop can apparently stimulate the repair of both. In contrast, 3′-nick-directed repair of a G-G mismatch was reduced when in the vicinity of a loop (33 or 46 bp between two sites). Increasing the distance separating the G-G mismatch and loop by 325 bp restored the efficiency of repair to the level of a single base-base mismatch. This observation suggests interference between 3′-nick-directed large loop repair and conventional mismatch repair systems when a mispair is near a loop. We propose a model in which DNA repair systems avoid simultaneous repair at adjacent sites to avoid the creation of double-stranded DNA breaks.
ER  -
TY  - JOUR
A1  - Huang, Yao-ming
A1  - Lee, Chun-Nan
A1  - Liang, W. C.
A1  - Chuang, Y. K.
A1  - Chang, Y. T.
A1  - Fang, Woei-horng
T1  -  DNA Mismatch Repair in Nuclear Extracts of Mouse M12 Cells
Y1  - 2000
JF  - Journal of Biomedical & Laboratory Sciences
JO  - Journal of Biomedical & Laboratory Sciences
SP  - 35
EP  - 45
VL  - 12
IS  - 2
ER  -
TY  - JOUR
T1  - A Systematic Study of the Energetics Involved in Structural Changes upon Association and Connectivity in Protein Interaction Networks
JO  - Structure
VL  - 19
IS  - 6
SP  - 881
EP  - 889
PY  - 2011/6/8/
T2  -
AU  - Stein, Amelie
AU  - Rueda, Manuel
AU  - Panjkovich, Alejandro
AU  - Orozco, Modesto
AU  - Aloy, Patrick
SN  - 0969-2126
M3  - doi: 10.1016/j.str.2011.03.009
UR  - http://www.sciencedirect.com/science/article/pii/S096921261100133X
ER  -
TY  - JOUR
T1  - Three-dimensional modeling of protein interactions and complexes is going ‘omics
JO  - Current Opinion in Structural Biology
VL  - 21
IS  - 2
SP  - 200
EP  - 208
PY  - 2011/4//
T2  -
AU  - Stein, Amelie
AU  - Mosca, Roberto
AU  - Aloy, Patrick
SN  - 0959-440X
M3  - doi: 10.1016/j.sbi.2011.01.005
UR  - http://www.sciencedirect.com/science/article/pii/S0959440X11000078
ER  -
TY  - JOUR
T1  - A Novel Framework for the Comparative Analysis of Biological Networks
A1  - Pache, Roland A.
A1  - Aloy, Patrick
Y1  - 2012/02/21
N2  - <p>Genome sequencing projects provide nearly complete lists of the individual components present in an organism, but reveal little about how they work together. Follow-up initiatives have deciphered thousands of dynamic and context-dependent interrelationships between gene products that need to be analyzed with novel bioinformatics approaches able to capture their complex emerging properties. Here, we present a novel framework for the alignment and comparative analysis of biological networks of arbitrary topology. Our strategy includes the prediction of likely conserved interactions, based on evolutionary distances, to counter the high number of missing interactions in the current interactome networks, and a fast assessment of the statistical significance of individual alignment solutions, which vastly increases its performance with respect to existing tools. Finally, we illustrate the biological significance of the results through the identification of novel complex components and potential cases of cross-talk between pathways and alternative signaling routes.</p>
JF  - PLoS ONE
JA  - PLoS ONE
VL  - 7
IS  - 2
UR  - http://dx.doi.org/10.1371%2Fjournal.pone.0031220
SP  - e31220
EP  -
PB  - Public Library of Science
M3  - doi: 10.1371/journal.pone.0031220
ER  -
TY  - JOUR
A1  - Mosca, Roberto
A1  - Pache, Roland A.
A1  - Aloy, Patrick
T1  - The role of structural disorder in the rewiring of protein interactions through evolution
Y1  - 2012/07/01
JF  - Molecular & Cellular Proteomics
JO  - Molecular & Cellular Proteomics
N1  - doi: 10.1074/mcp.M111.014969
VL  - 11
IS  - 7
SP  - 1
EP  - 8
UR  - http://www.mcponline.org/content/early/2012/03/02/mcp.M111.014969.abstract
N2  - Structurally disordered regions play a key role in protein-protein interaction networks and the evolution of highly connected proteins, enabling the molecular mechanisms for multiple binding. However, the role of protein disorder in the evolution of interaction networks has been only investigated through the analysis of individual proteins, being impossible to distinguish its specific impact in the (re) shaping of their interaction environments. Now, the availability of large interactomes for several model organisms permits to explore the role of disorder in protein interaction networks not only at the level of the interacting proteins, but of the interactions themselves. By comparing the interactomes of human, fly and yeast, we discovered that, despite being much more abundant, disordered interactions are significantly less conserved than their ordered counterparts. Furthermore, our analyses provide evidence that this happens not only because disordered proteins are less conserved, but also because they display a higher capacity to rewire their interaction neighborhood through evolution. Overall, our results support the hypothesis that conservation of disorder gives a clear evolutionary advantage, facilitating the change of interaction partners during evolution. Moreover, this mechanism is not exclusive of a few anecdotal cases but a global feature present in the interactome networks of entire organisms.
ER  -
TY  - JOUR
A1  - Pache, Roland A.
A1  - Céol, Arnaud
A1  - Aloy, Patrick
T1  - NetAligner—a network alignment server to compare complexes, pathways and whole interactomes
Y1  - 2012/07/01
JF  - Nucleic Acids Research
JO  - Nucleic Acids Research
SP  - W157
EP  - W161
N1  - doi: 10.1093/nar/gks446
VL  - 40
IS  - W1
UR  - http://nar.oxfordjournals.org/content/40/W1/W157.abstract
N2  - The many ongoing genome sequencing initiatives are delivering comprehensive lists of the individual molecular components present in an organism, but these reveal little about how they work together. Follow-up initiatives are revealing thousands of interrelationships between gene products that need to be analyzed with novel bioinformatics approaches able to capture their complex emerging properties. Recently, we developed NetAligner, a novel network alignment tool that allows the identification of conserved protein complexes and pathways across organisms, providing valuable hints as to how those interaction networks evolved. NetAligner includes the prediction of likely conserved interactions, based on evolutionary distances, to counter the high number of missing interactions in current interactome networks, and a fast assessment of the statistical significance of individual alignment solutions, which increases its performance with respect to existing tools. The web server implementation of the NetAligner algorithm presented here features complex, pathway and interactome to interactome alignments for seven model organisms, namely Homo sapiens, Mus musculus, Drosophila melanogaster, Caenorhabditis elegans, Arabidopsis thaliana, Saccharomyces cerevisiae and Escherichia coli. The user can query complexes and pathways of arbitrary topology against a target species interactome, or directly compare two complete interactomes to identify conserved complexes and subnetworks. Alignment solutions can be downloaded or directly visualized in the browser. The NetAligner web server is publicly available at http://netaligner.irbbarcelona.org/.
ER  -
TY  - JOUR
AU  - Sardon, Teresa
AU  - Pache, Roland A.
AU  - Stein, Amelie
AU  - Molina, Henrik
AU  - Vernos, Isabelle
AU  - Aloy, Patrick
TI  - Uncovering new substrates for Aurora A kinase
JA  - EMBO Reports
PY  - 2010/12//print
VL  - 11
IS  - 12
SP  - 977
EP  - 984
PB  - European Molecular Biology Organization
SN  - 1469-221X
UR  - http://dx.doi.org/10.1038/embor.2010.171
M3  - doi: 10.1038/embor.2010.171
N1  - doi: 10.1038/embor.2010.171
L3  - http://www.nature.com/embor/journal/v11/n12/suppinfo/embor2010171a_S1.html
ER  -
TY  - JOUR
A1  - Stein, Amelie
A1  - Céol, Arnaud
A1  - Aloy, Patrick
T1  - 3did: identification and classification of domain-based interactions of known three-dimensional structure
Y1  - 2011/01/01
JF  - Nucleic Acids Research
JO  - Nucleic Acids Research
SP  - D718
EP  - D723
N1  - doi: 10.1093/nar/gkq962
VL  - 39
IS  - suppl 1
UR  - http://nar.oxfordjournals.org/content/39/suppl_1/D718.abstract
N2  - The database of three-dimensional interacting domains (3did) is a collection of protein interactions for which high-resolution three-dimensional structures are known. 3did exploits the availability of structural data to provide molecular details on interactions between two globular domains as well as novel domain–peptide interactions, derived using a recently published method from our lab. The interface residues are presented for each interaction type individually, plus global domain interfaces at which one or more partners (domains or peptides) bind. The 3did web server at http://3did.irbbarcelona.org visualizes these interfaces along with atomic details of individual interactions using Jmol. The complete contents are also available for download.
ER  -
TY  - JOUR
T1  - Novel Peptide-Mediated Interactions Derived from High-Resolution 3-Dimensional Structures
A1  - Stein, Amelie
A1  - Aloy, Patrick
Y1  - 2010/05/20
N2  - <title>Author Summary</title><p>Protein-protein interactions are paramount in any aspect of the cellular life. Some proteins form large macromolecular complexes that execute core functionalities of the cell, while others transmit information in signalling networks to co-ordinate these processes. The latter type, of more transient nature, often occurs through the recognition of a small linear sequence motif in one protein by a specialized globular domain in the other. These peptide stretches often contain a consensus pattern complementary to the interaction surface displayed by their binding partners, and adopt a well-defined structure upon binding. Information that is currently available only from high-resolution three-dimensional (3D) structures, and that can be as characteristic as the consensus motif itself. In this manuscript, we present a strategy to identify novel domain-motif interactions (DMIs) among the set of protein complexes of known 3D structures, which provides information on the consensus motif and binding domain and also allows ready identification of the key interacting residues. A detailed knowledge of the interface is critical to plan further functional studies and for the development of interfering elements, be it drug-like compounds or novel engineered binding proteins or peptides. The small interfaces typical for DMIs make them interesting candidates for all these applications.</p>
JF  - PLoS Computational Biology
JA  - PLoS Computational Biology
VL  - 6
IS  - 5
UR  - http://dx.doi.org/10.1371%2Fjournal.pcbi.1000789
SP  - e1000789
EP  -
PB  - Public Library of Science
M3  - doi: 10.1371/journal.pcbi.1000789
ER  -
TY  - JOUR
A1  - Littler, D. R.
A1  - Alvarez-Fernández, M.
A1  - Stein, Amelie
A1  - Hibbert, R. G.
A1  - Heidebrecht, T.
A1  - Aloy, Patrick
A1  - Medema, R. H.
A1  - Perrakis, Anastassis
T1  - Structure of the FoxM1 DNA-recognition domain bound to a promoter sequence
Y1  - 2010/07/01
JF  - Nucleic Acids Research
JO  - Nucleic Acids Research
SP  - 4527
EP  - 4538
N1  - doi: 10.1093/nar/gkq194
VL  - 38
IS  - 13
UR  - http://nar.oxfordjournals.org/content/38/13/4527.abstract
N2  - FoxM1 is a member of the Forkhead family of transcription factors and is implicated in inducing cell proliferation and some forms of tumorigenesis. It binds promoter regions with a preference for tandem repeats of a consensus ‘TAAACA’ recognition sequence. The affinity of the isolated FoxM1 DNA-binding domain for this site is in the micromolar range, lower than observed for other Forkhead proteins. To explain these FoxM1 features, we determined the crystal structure of its DNA-binding domain in complex with a tandem recognition sequence. FoxM1 adopts the winged-helix fold, typical of the Forkhead family. Neither ‘wing’ of the fold however, makes significant contacts with the DNA, while the second, C-terminal, wing adopts an unusual ordered conformation across the back of the molecule. The lack of standard DNA–‘wing’ interactions may be a reason for FoxM1’s relatively low affinity. The role of the ‘wings’ is possibly undertaken by other FoxM1 regions outside the DBD, that could interact with the target DNA directly or mediate interactions with other binding partners. Finally, we were unable to show a clear preference for tandem consensus site recognition in DNA-binding, transcription activation or bioinformatics analysis; FoxM1's moniker, ‘Trident’, is not supported by our data.
ER  -
TY  - JOUR
T1  - Systematic Bioinformatics and Experimental Validation of Yeast Complexes Reduces the Rate of Attrition during Structural Investigations
JO  - Structure
VL  - 18
IS  - 9
SP  - 1075
EP  - 1082
PY  - 2010/9/8/
T2  -
AU  - Brooks, Mark A.
AU  - Gewartowski, Kamil
AU  - Mitsiki, Eirini
AU  - Létoquart, Juliette
AU  - Pache, Roland A.
AU  - Billier, Ysaline
AU  - Bertero, Michela
AU  - Corréa, Margot
AU  - Czarnocki-Cieciura, Mariusz
AU  - Dadlez, Michal
AU  - Henriot, Véronique
AU  - Lazar, Noureddine
AU  - Delbos, Lila
AU  - Lebert, Dorothée
AU  - Piwowarski, Jan
AU  - Rochaix, Pascal
AU  - Böttcher, Bettina
AU  - Serrano, Luis
AU  - Séraphin, Bertrand
AU  - van Tilbeurgh, Herman
AU  - Aloy, Patrick
AU  - Perrakis, Anastassis
AU  - Dziembowski, Andrzej
SN  - 0969-2126
M3  - doi: 10.1016/j.str.2010.08.001
UR  - http://www.sciencedirect.com/science/article/pii/S096921261000273X
ER  -
TY  - JOUR
A1  - Stein, Amelie
A1  - Pache, Roland A.
A1  - Bernadó, Pau
A1  - Pons, Miquel
A1  - Aloy, Patrick
T1  - Dynamic interactions of proteins in complex networks: a more structured view
JF  - FEBS Journal
VL  - 276
IS  - 19
PB  - Blackwell Publishing Ltd
SN  - 1742-4658
UR  - http://dx.doi.org/10.1111/j.1742-4658.2009.07251.x
M3  - doi: 10.1111/j.1742-4658.2009.07251.x
SP  - 5390
EP  - 5405
KW  - interaction specificity
KW  - intrinsically unstructured proteins
KW  - linear motifs
KW  - modular recognition domains
KW  - peptide-mediated interactions
KW  - phosphorylation events
KW  - post-translational modifications
KW  - protein disorder
KW  - protein interaction networks
KW  - signalling networks
Y1  - 2009
ER  -
TY  - JOUR
A1  - Stein, Amelie
A1  - Panjkovich, Alejandro
A1  - Aloy, Patrick
T1  - 3did Update: domain–domain and peptide-mediated interactions of known 3D structure
Y1  - 2009/01/01
JF  - Nucleic Acids Research
JO  - Nucleic Acids Research
SP  - D300
EP  - D304
N1  - doi: 10.1093/nar/gkn690
VL  - 37
IS  - suppl 1
UR  - http://nar.oxfordjournals.org/content/37/suppl_1/D300.abstract
N2  - The database of 3D interacting domains (3did) is a collection of protein interactions for which high-resolution 3D structures are known. 3did exploits structural information to provide the crucial molecular details necessary for understanding how protein interactions occur. Besides interactions between globular domains, the new release of 3did also contains a hand-curated set of transient peptide-mediated interactions. The interactions are grouped in Interaction Types, based on the mode of binding, and the different binding interfaces used in each type are also identified and catalogued. A web-based tool to query 3did is available at http://3did.irbbarcelona.org.
ER  -
TY  - JOUR
T1  - Approved Drug Mimics of Short Peptide Ligands from Protein Interaction Motifs
AU  - Parthasarathi, Laavanya
AU  - Casey, Fergal
AU  - Stein, Amelie
AU  - Aloy, Patrick
AU  - Shields, Denis C.
Y1  - 2008/10/01
PY  - 2008
DA  - 2008/10/27
N1  - doi: 10.1021/ci800174c
DO  - 10.1021/ci800174c
T2  - Journal of Chemical Information and Modeling
JF  - Journal of Chemical Information and Modeling
JO  - Journal of Chemical Information and Modeling
SP  - 1943
EP  - 1948
VL  - 48
IS  - 10
PB  - American Chemical Society
SN  - 1549-9596
M3  - doi: 10.1021/ci800174c
UR  - http://dx.doi.org/10.1021/ci800174c
Y2  - 2011/12/16
ER  -
TY  - JOUR
T1  - Contextual Specificity in Peptide-Mediated Protein Interactions
A1  - Stein, Amelie
A1  - Aloy, Patrick
Y1  - 2008/07/02
N2  - <p>Most biological processes are regulated through complex networks of transient protein interactions where a globular domain in one protein recognizes a linear peptide from another, creating a relatively small contact interface. Although sufficient to ensure binding, these linear motifs alone are usually too short to achieve the high specificity observed, and additional contacts are often encoded in the residues surrounding the motif (i.e. the context). Here, we systematically identified all instances of peptide-mediated protein interactions of known three-dimensional structure and used them to investigate the individual contribution of motif and context to the global binding energy. We found that, on average, the context is responsible for roughly 20% of the binding and plays a crucial role in determining interaction specificity, by either improving the affinity with the native partner or impeding non-native interactions. We also studied and quantified the topological and energetic variability of interaction interfaces, finding a much higher heterogeneity in the context residues than in the consensus binding motifs. Our analysis partially reveals the molecular mechanisms responsible for the dynamic nature of peptide-mediated interactions, and suggests a global evolutionary mechanism to maximise the binding specificity. Finally, we investigated the viability of non-native interactions and highlight cases of potential cross-reaction that might compensate for individual protein failure and establish backup circuits to increase the robustness of cell networks.</p>
JF  - PLoS ONE
JA  - PLoS ONE
VL  - 3
IS  - 7
UR  - http://dx.plos.org/10.1371%2Fjournal.pone.0002524
SP  - e2524
EP  -
PB  - Public Library of Science
M3  - doi: 10.1371/journal.pone.0002524
ER  -
TY  - JOUR
T1  - A molecular interpretation of genetic interactions in yeast
JO  - FEBS Letters
VL  - 582
IS  - 8
SP  - 1245
EP  - 1250
PY  - 2008/4/9/
T2  - (1) The Digital, Democratic Age of Scientific Abstracts (2) Targeting and Tinkering with Interaction Networks
AU  - Stein, Amelie
AU  - Aloy, Patrick
SN  - 0014-5793
M3  - doi: 10.1016/j.febslet.2008.02.020
UR  - http://www.sciencedirect.com/science/article/pii/S0014579308001257
KW  - Genetic interaction
KW  - Synthetic lethal
KW  - Network robustness
KW  - Gene duplicate
KW  - Pathway redundancy
ER  -
TY  - JOUR
A1  - Stein, Amelie
A1  - Russell, Robert B.
A1  - Aloy, Patrick
T1  - 3did: interacting protein domains of known three-dimensional structure
Y1  - 2005/01/01
JF  - Nucleic Acids Research
JO  - Nucleic Acids Research
SP  - D413
EP  - D417
N1  - doi: 10.1093/nar/gki037
VL  - 33
IS  - suppl 1
UR  - http://nar.oxfordjournals.org/content/33/suppl_1/D413.abstract
N2  - The database of 3D Interacting Domains (3did) is a collection of domain–domain interactions in proteins for which high-resolution three-dimensional structures are known. 3did exploits structural information to provide critical molecular details necessary for understanding how interactions occur. It also offers an overview of how similar in structure are interactions between different members of the same protein family. The database also contains Gene Ontology-based functional annotations and interactions between yeast proteins from large-scale interaction discovery studies. A web-based tool to query 3did is available at http://3did.embl.de.
ER  -
TY  - JOUR
AU  - Pache, Roland A.
AU  - Babu, M Madan
AU  - Aloy, Patrick
PY  - 2009
IS  - 1
M3  - doi: 10.1186/1752-0509-3-74
SP  - 74
T1  - Exploiting gene deletion fitness effects in yeast to understand the modular architecture of protein complexes under different growth conditions
JO  - BMC Systems Biology
UR  - http://www.biomedcentral.com/1752-0509/3/74
VL  - 3
SN  - 1752-0509
N2  - BACKGROUND:Understanding how individual genes contribute towards the fitness of an organism is a fundamental problem in biology. Although recent genome-wide screens have generated abundant data on quantitative fitness for single gene knockouts, very few studies have systematically integrated other types of biological information to understand how and why deletion of specific genes give rise to a particular fitness effect. In this study, we combine quantitative fitness data for single gene knock-outs in yeast with large-scale interaction discovery experiments to understand the effect of gene deletion on the modular architecture of protein complexes, under different growth conditions.RESULTS:Our analysis reveals that genes in complexes show more severe fitness effects upon deletion than other genes but, in contrast to what has been observed in binary protein-protein interaction networks, we find that this is not related to the number of complexes in which they are present. We also find that, in general, the core and attachment components of protein complexes are equally important for the complex machinery to function. However, when quantifying the importance of core and attachments in single complex variations, or isoforms, we observe that this global trend originates from either the core or the attachment components being more important for strain fitness, both being equally important or both being dispensable. Finally, our study reveals that different isoforms of a complex can exhibit distinct fitness patterns across growth conditions.CONCLUSION:This study presents a powerful approach to unveil the molecular basis for various complex phenotypic profiles observed in gene deletion experiments. It also highlights some interesting cases of potential functional compensation between protein paralogues and suggests a new piece to fit into the histone-code puzzle.
ER  -
TY  - JOUR
A1  - Pache, Roland A.
A1  - Aloy, Patrick
T1  - Incorporating high-throughput proteomics experiments into structural biology pipelines: Identification of the low-hanging fruits
JF  - Proteomics
JA  - Proteomics
VL  - 8
IS  - 10
PB  - WILEY-VCH Verlag
SN  - 1615-9861
UR  - http://dx.doi.org/10.1002/pmic.200700966
M3  - doi: 10.1002/pmic.200700966
SP  - 1959
EP  - 1964
KW  - High-throughput proteomics
KW  - Macromolecular complexes
KW  - Structural biology
KW  - Structural genomics
KW  - Target selection
Y1  - 2008
ER  -
TY  - JOUR
T1  - Towards a molecular characterisation of pathological pathways
JO  - FEBS Letters
VL  - 582
IS  - 8
SP  - 1259
EP  - 1265
PY  - 2008/4/9/
T2  - (1) The Digital, Democratic Age of Scientific Abstracts (2) Targeting and Tinkering with Interaction Networks
AU  - Pache, Roland A.
AU  - Zanzoni, Andreas
AU  - Naval, Jordi
AU  - Mas, José Manuel
AU  - Aloy, Patrick
SN  - 0014-5793
M3  - doi: 10.1016/j.febslet.2008.02.014
UR  - http://www.sciencedirect.com/science/article/pii/S0014579308001191
KW  - Systems pathology
KW  - Protein–protein interaction
KW  - Network modelling
KW  - Biological pathway
KW  - Drug discovery
ER  -
TY  - JOUR
T1  - New Method for the Assessment of All Drug-Like Pockets Across a Structural Genome
AU  - Nicola, George
AU  - Smith, Colin A.
AU  - Abagyan, Ruben
Y1  - 2008/03/11
PY  - 2008
DA  - 2008/04/01
N1  - doi: 10.1089/cmb.2007.0178
DO  - 10.1089/cmb.2007.0178
T2  - Journal of Computational Biology
JF  - Journal of Computational Biology
JO  - Journal of Computational Biology
SP  - 231
EP  - 240
VL  - 15
IS  - 3
PB  - Mary Ann Liebert, Inc., publishers
SN  - 1066-5277
M3  - doi: 10.1089/cmb.2007.0178
UR  - http://dx.doi.org/10.1089/cmb.2007.0178
Y2  - 2011/12/16
ER  -
TY  - JOUR
N2  - Comprehensive detection and quantitation of metabolites from a biological source constitute the major challenges of current metabolomics research. Two chemical derivatization methodologies, butylation and amination, were applied to human serum for ionization enhancement of a broad spectrum of metabolite classes, including steroids and amino acids. LC-ESI-MS analysis of the derivatized serum samples provided a significant signal elevation across the total ion chromatogram to over a 100-fold increase in ionization efficiency. It was also demonstrated that derivatization combined with isotopically labeled reagents facilitated the relative quantitation of derivatized metabolites from individual as well as pooled samples.
AD  - Nieuwe Hemweg 6B, Amsterdam, The Netherlands
AU  - O'Maille, Grace
AU  - Go, Eden P.
AU  - Hoang, Linh
AU  - Want, Elizabeth J.
AU  - Smith, Colin A.
AU  - O'Maille, Paul
AU  - Nordstrom, Anders
AU  - Morita, Hirotoshi
AU  - Qin, Chuan
AU  - Uritboonthai, Wilasinee
AU  - Apon, Junefredo
AU  - Moore, Richard
AU  - Garrett, James
AU  - Siuzdak, Gary
JO  - Spectroscopy: An International Journal
PB  - IOS PRESS
T1  - Metabolomics relative quantitation with mass spectrometry using chemical derivatization and isotope labeling
VL  - 22
IS  - 5
SP  - 327
EP  - 343
PY  - 2008
N1  - doi: 10.3233/SPE-2008-0361
UR  - http://iospress.metapress.com/index/358838254R930073.pdf
ER  -
TY  - JOUR
T1  - Discovery of novel inhibitors targeting enoyl–acyl carrier protein reductase in Plasmodium falciparum by structure-based virtual screening
JO  - Biochemical and Biophysical Research Communications
VL  - 358
IS  - 3
SP  - 686
EP  - 691
PY  - 2007/7/6/
T2  -
AU  - Nicola, George
AU  - Smith, Colin A.
AU  - Lucumi, Edinson
AU  - Kuo, Mack R.
AU  - Karagyozov, Luchezar
AU  - Fidock, David A.
AU  - Sacchettini, James C.
AU  - Abagyan, Ruben
SN  - 0006-291X
M3  - doi: 10.1016/j.bbrc.2007.04.113
UR  - http://www.sciencedirect.com/science/article/pii/S0006291X0700825X
KW  - Virtual screening
KW  - VLS
KW  - Structure-based drug design
KW  - Plasmodium
KW  - Enoyl–acyl carrier protein reductase
KW  - ENR
KW  - Triclosan
KW  - ICM
KW  - Inhibitor
KW  - Malaria
KW  - Molecular modeling
ER  -
TY  - JOUR
N2  - Serum analysis with LC/MS can yield thousands of potential metabolites. However, in metabolomics, biomarkers of interest will often be of low abundance, and ionization suppression from high abundance endogenous metabolites such as phospholipids may prevent the detection of these metabolites. Here a cerium-modified column and methyl-tert-butyl-ether (MTBE) liquid-liquid extraction were employed to remove phospholipids from serum in order to obtain a more comprehensive metabolite profile. XCMS, an in-house developed data analysis software platform, showed that the intensity of existing endogenous metabolites increased, and that new metabolites were observed. This application of phospholipid capture in combination with XCMS non-linear data processing has enormous potential in metabolite profiling, for biomarker detection and quantitation.
AD  - 233 Spring St, New York, NY 10013 USA
AU  - Want, Elizabeth J.
AU  - Smith, Colin A.
AU  - Qin, Chuan
AU  - VanHorne, K. C.
AU  - Siuzdak, Gary
JO  - Metabolomics
PB  - Springer
T1  - Phospholipid capture combined with non-linear chromatographic correction for improved serum metabolite profiling
PY  - 2006
Y2  - SEP
VL  - 2
IS  - 3
SP  - 145
EP  - 154
N1  - doi: 10.1007/s11306-006-0028-0
ER  -
TY  - JOUR
T1  - XCMS:  Processing Mass Spectrometry Data for Metabolite Profiling Using Nonlinear Peak Alignment, Matching, and Identification
AU  - Smith, Colin A.
AU  - Want, Elizabeth J.
AU  - O'Maille, Grace
AU  - Abagyan, Ruben
AU  - Siuzdak, Gary
Y1  - 2006/01/07
PY  - 2006
DA  - 2006/02/01
N1  - doi: 10.1021/ac051437y
DO  - 10.1021/ac051437y
T2  - Analytical Chemistry
JF  - Analytical Chemistry
JO  - Analytical Chemistry
SP  - 779
EP  - 787
VL  - 78
IS  - 3
PB  - American Chemical Society
SN  - 0003-2700
M3  - doi: 10.1021/ac051437y
UR  - http://dx.doi.org/10.1021/ac051437y
Y2  - 2011/12/16
ER  -
TY  - JOUR
T1  - Solvent-Dependent Metabolite Distribution, Clustering, and Protein Extraction for Serum Profiling with Mass Spectrometry
AU  - Want, Elizabeth J.
AU  - O'Maille, Grace
AU  - Smith, Colin A.
AU  - Brandon, Theodore R.
AU  - Uritboonthai, Wilasinee
AU  - Qin, Chuan
AU  - Trauger, Sunia A.
AU  - Siuzdak, Gary
Y1  - 2005/12/16
PY  - 2005
DA  - 2006/02/01
N1  - doi: 10.1021/ac051312t
DO  - 10.1021/ac051312t
T2  - Analytical Chemistry
JF  - Analytical Chemistry
JO  - Analytical Chemistry
SP  - 743
EP  - 752
VL  - 78
IS  - 3
PB  - American Chemical Society
SN  - 0003-2700
M3  - doi: 10.1021/ac051312t
UR  - http://dx.doi.org/10.1021/ac051312t
Y2  - 2011/12/16
ER  -
TY  - CONF
T1  - METLIN: A Metabolite Mass Spectral Database
AU  - Smith, Colin A.
AU  - O'Maille, Grace
AU  - Want, Elizabeth J.
AU  - Qin, Chuan
AU  - Trauger, Sunia A.
AU  - Brandon, Theodore R.
AU  - Custodio, Darlene E.
AU  - Abagyan, Ruben
AU  - Siuzdak, Gary
Y1  - 2005/04/23/April 23-28
UR  - http://meta.wkhealth.com/pt/pt-core/template-journal/lwwgateway/media/landingpage.htm?issn=0163-4356&volume=27&issue=6&spage=747
T2  - Therapeutic Drug Monitoring
JO  - Proceedings of the 9th International Congress of Therapeutic Drug Monitoring & Clinical Toxicology
SP  - 747
EP  - 751
VL  - 27
IS  - 6
ER  -
TY  - JOUR
T1  - Domain Swapping Proceeds via Complete Unfolding: A 19F- and 1H-NMR Study of the Cyanovirin-N Protein
AU  - Liu, Lin
AU  - Byeon, In-Ja L.
AU  - Bahar, Ivet
AU  - Gronenborn, Angela M.
Y1  - 2012/02/01
PY  - 2012
DA  - 2012/03/07
N1  - doi: 10.1021/ja210118w
DO  - 10.1021/ja210118w
T2  - Journal of the American Chemical Society
JF  - Journal of the American Chemical Society
JO  - Journal of the American Chemical Society
SP  - 4229
EP  - 4235
VL  - 134
IS  - 9
PB  - American Chemical Society
SN  - 0002-7863
M3  - doi: 10.1021/ja210118w
UR  - http://dx.doi.org/10.1021/ja210118w
Y2  - 2012/06/08
ER  -
TY  - JOUR
A1  - Liu, Lin
A1  - Gronenborn, Angela M.
A1  - Bahar, Ivet
T1  - Longer simulations sample larger subspaces of conformations while maintaining robust mechanisms of motion
JF  - Proteins: Structure, Function, and Bioinformatics
JA  - Proteins
VL  - 80
IS  - 2
PB  - Wiley Subscription Services, Inc., A Wiley Company
SN  - 1097-0134
UR  - http://dx.doi.org/10.1002/prot.23225
M3  - doi: 10.1002/prot.23225
SP  - 616
EP  - 625
KW  - structure-encoded dynamics
KW  - molecular dynamics simulations
KW  - power law
KW  - global motions
KW  - equilibrium fluctuations of cyanovirin-N
Y1  - 2012
ER  -
TY  - CHAP
AU  - Liu, Lin
AU  - Gronenborn, Angela M.
T1  - Protein and Nucleic Acid Folding: Domain Swapping in Proteins
VL  - 3
SP  - 148
EP  - 169
T2  - The Folding of Proteins and Nucleic Acids
A2  - Egelman, Edward
BT  - Comprehensive Biophysics
PB  - Elsevier
PY  - 2012
Y1  - 2012/05/17
UR  - http://www.elsevierdirect.com/ISBN/9780123749208/
ER  -
TY  - JOUR
A1  - Liu, Lin
A1  - Koharudin, Leonardus M. I.
A1  - Gronenborn, Angela M.
A1  - Bahar, Ivet
T1  - A comparative analysis of the equilibrium dynamics of a designed protein inferred from NMR, X-ray, and computations
JF  - Proteins: Structure, Function, and Bioinformatics
JA  - Proteins
VL  - 77
IS  - 4
PB  - Wiley Subscription Services, Inc., A Wiley Company
SN  - 1097-0134
UR  - http://dx.doi.org/10.1002/prot.22518
M3  - doi: 10.1002/prot.22518
SP  - 927
EP  - 939
KW  - equilibrium dynamics
KW  - ensemble of conformations
KW  - inter-residue contact topology
KW  - crystal contacts
KW  - elastic network model
KW  - sugar-binding protein
Y1  - 2009
ER  -
TY  - JOUR
A1  - Iwatani, Yasumasa
A1  - Chan, Denise S. B.
A1  - Liu, Lin
A1  - Yoshii, Hiroaki
A1  - Shibata, Junko
A1  - Yamamoto, Naoki
A1  - Levin, Judith G.
A1  - Gronenborn, Angela M.
A1  - Sugiura, Wataru
T1  - HIV-1 Vif-mediated ubiquitination/degradation of APOBEC3G involves four critical lysine residues in its C-terminal domain
Y1  - 2009/11/17
JF  - Proceedings of the National Academy of Sciences
JO  - Proceedings of the National Academy of Sciences
SP  - 19539
EP  - 19544
N1  - doi: 10.1073/pnas.0906652106
VL  - 106
IS  - 46
UR  - http://www.pnas.org/content/106/46/19539.abstract
N2  - During coevolution with the host, HIV-1 developed the ability to hijack the cellular ubiquitin/proteasome degradation pathway to counteract the antiviral activity of APOBEC3G (A3G), a host cytidine deaminase that can block HIV-1 replication. Abrogation of A3G function involves the HIV-1 Vif protein, which binds A3G and serves as an adapter molecule to recruit A3G to a Cullin5-based E3 ubiquitin ligase complex. Structure-guided mutagenesis of A3G focused on the 14 most surface-exposed Lys residues allowed us to identify four Lys residues (Lys-297, 301, 303, and 334) that are required for Vif-mediated A3G ubiquitination and degradation. Substitution of Arg for these residues confers Vif resistance and restores A3G's antiviral activity in the presence of Vif. In our model, the critical four Lys residues cluster at the C terminus, opposite to the known N-terminal Vif-interaction region in the protein. Thus, spatial constraints imposed by the E3 ligase complex may be an important determinant in Vif-dependent A3G ubiquitination.
ER  -
TY  - JOUR
N2  - CD59 is a 77-amino acid membrane glycoprotein that plays an important role in regulating the terminal pathway of complement by inhibiting formation of the cytolytic membrane attack complex ( MAC or C5b-9). The MAC is formed by the self assembly of C5b, C6, C7, C8, and multiple C9 molecules, with CD59 functioning by binding C5b-8 and C5b-9 in the assembling complex. We performed a scanning alanine mutagenesis screen of residues 16 - 57, a region previously identified to contain the C8/C9 binding interface. We have also created an improved NMR model from previously published data for structural understanding of CD59. Based on the scanning mutagenesis data, refined models, and additional site-specific mutations, we identified a binding interface that is much broader than previously thought. In addition to identifying substitutions that decreased CD59 activity, a surprising number of substitutions significantly enhanced CD59 activity. Because CD59 has significant therapeutic potential for the treatment of various inflammatory conditions, we investigated further the ability to enhance CD59 activity by additional mutagenesis studies. Based on the enhanced activity of membrane-bound mutant CD59 molecules, clinically relevant soluble mutant CD59-based proteins were prepared and shown to have up to a 3-fold increase in complement inhibitory activity.
AD  - 9650 Rockville Pike Bethesda, MD 20814-3996 USA
AU  - Huang, YX
AU  - Smith, Colin A.
AU  - Song, HB
AU  - Morgan, BP
AU  - Abagyan, Ruben
AU  - Tomlinson, S
JO  - Journal of Biological Chemistry
IS  - 40
SP  - 34073
EP  - 34079
PB  - The American Society for Biochemistry and Molecular Biology Inc.
T1  - Insights into the human CD59 complement binding interface toward engineering new therapeutics
VL  - 280
PY  - 2005
Y1  - 2005/10/07
Y2  - OCT 7
N1  - doi: 10.1074/jbc.M504922200
ER  -
TY  - JOUR
N2  - The Bioconductor project is an initiative for the collaborative creation of extensible software for computational biology and bioinformatics. The goals of the project include: fostering collaborative development and widespread use of innovative software, reducing barriers to entry into interdisciplinary scientific research, and promoting the achievement of remote reproducibility of research results. We describe details of our aims and methods, identify current challenges, compare Bioconductor to other open bioinformatics projects, and provide working examples.
AD  - Middlesex House, 34-42 Cleveland Street, London W1T 4LB, UK
AU  - Gentleman, R. C.
AU  - Carey, V. J.
AU  - Bates, D. M.
AU  - Bolstad, B.
AU  - Dettling, M.
AU  - Dudoit, S.
AU  - Ellis, B.
AU  - Gautier, L.
AU  - Ge, Y. C.
AU  - Gentry, J.
AU  - Hornik, K.
AU  - Hothorn, T.
AU  - Huber, W.
AU  - Iacus, S.
AU  - Irizarry, R.
AU  - Leisch, F.
AU  - Li, C.
AU  - Maechler, M.
AU  - Rossini, A. J.
AU  - Sawitzki, G.
AU  - Smith, Colin A.
AU  - Smyth, G.
AU  - Tierney, L.
AU  - Yang, J. Y. H.
AU  - Zhang, J. H.
JO  - Genome Biology
PB  - BioMed Central Ltd.
T1  - Bioconductor: open software development for computational biology and bioinformatics
VL  - 5
IS  - 10
SP  - R80
PY  - 2004
N1  - doi: 10.1186/gb-2004-5-10-r80
SN  - 1465-6906
UR  - http://genomebiology.com/2004/5/10/R80
Y1  - 2004/09/15
ER  -
TY  - JOUR
AU  - Titov, Denis V.
AU  - Gilman, Benjamin
AU  - He, Qing-Li
AU  - Bhat, Shridhar
AU  - Low, Woon-Kai
AU  - Dang, Yongjun
AU  - Smeaton, Michael B.
AU  - Demain, Arnold L.
AU  - Miller, Paul S.
AU  - Kugel, Jennifer F.
AU  - Goodrich, James A.
AU  - Liu, Jun O.
TI  - XPB, a subunit of TFIIH, is a target of the natural product triptolide
JA  - Nature Chemical Biology
PY  - 2011/03//print
VL  - 7
IS  - 3
SP  - 182
EP  - 188
PB  - Nature Publishing Group, a division of Macmillan Publishers Limited. All Rights Reserved.
SN  - 1552-4450
UR  - http://dx.doi.org/10.1038/nchembio.522
M3  - doi: 10.1038/nchembio.522
N1  - doi: 10.1038/nchembio.522
L3  - http://www.nature.com/nchembio/journal/v7/n3/abs/nchembio.522.html#supplementary-information
ER  -
TY  - JOUR
AU  - Hlavin, Erica M.
AU  - Smeaton, Michael B.
AU  - Miller, Paul S.
TI  - Initiation of DNA interstrand cross-link repair in mammalian cells
JO  - Environmental and Molecular Mutagenesis
JA  - Environmental and Molecular Mutagenesis
VL  - 51
IS  - 6
PY  - 2010/07//print
PB  - Wiley Subscription Services, Inc., A Wiley Company
SN  - 1098-2280
UR  - http://dx.doi.org/10.1002/em.20559
DO  - doi: 10.1002/em.20559
SP  - 604
EP  - 624
KW  - cross-link structure
KW  - transcription-coupled repair
KW  - replication-coupled repair
KW  - global genome repair
KW  - cross-link unhooking
PY  - 2010
ER  -
TY  - JOUR
T1  - Cross-Link Structure Affects Replication-Independent DNA Interstrand Cross-Link Repair in Mammalian Cells
AU  - Hlavin, Erica M.
AU  - Smeaton, Michael B.
AU  - Noronha, Anne M.
AU  - Wilds, Christopher J.
AU  - Miller, Paul S.
Y1  - 2010/04/07
PY  - 2010
DA  - 2010/05/11
N1  - doi: 10.1021/bi902169q
DO  - doi: 10.1021/bi902169q
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 3977
EP  - 3988
VL  - 49
IS  - 18
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi902169q
UR  - http://dx.doi.org/10.1021/bi902169q
Y2  - 2012/04/09
ER  -
TY  - JOUR
T1  - Effect of Cross-Link Structure on DNA Interstrand Cross-Link Repair Synthesis
AU  - Smeaton, Michael B.
AU  - Hlavin, Erica M.
AU  - Noronha, Anne M.
AU  - Murphy, Sebastian P.
AU  - Wilds, Christopher J.
AU  - Miller, Paul S.
Y1  - 2009/07/06
PY  - 2009
DA  - 2009/07/20
N1  - doi: 10.1021/tx9000896
DO  - doi: 10.1021/tx9000896
T2  - Chemical Research in Toxicology
JF  - Chemical Research in Toxicology
JO  - Chemical Research in Toxicology
SP  - 1285
EP  - 1297
VL  - 22
IS  - 7
PB  - American Chemical Society
SN  - 0893-228X
M3  - doi: 10.1021/tx9000896
UR  - http://dx.doi.org/10.1021/tx9000896
Y2  - 2012/04/09
ER  -
TY  - JOUR
T1  - Distortion-Dependent Unhooking of Interstrand Cross-Links in Mammalian Cell Extracts
AU  - Smeaton, Michael B.
AU  - Hlavin, Erica M.
AU  - McGregor Mason, Tracey
AU  - Noronha, Anne M.
AU  - Wilds, Christopher J.
AU  - Miller, Paul S.
Y1  - 2008/08/15
PY  - 2008
DA  - 2008/09/16
N1  - doi: 10.1021/bi800925e
DO  - doi: 10.1021/bi800925e
T2  - Biochemistry
JF  - Biochemistry
JO  - Biochemistry
SP  - 9920
EP  - 9930
VL  - 47
IS  - 37
PB  - American Chemical Society
SN  - 0006-2960
M3  - doi: 10.1021/bi800925e
UR  - http://dx.doi.org/10.1021/bi800925e
Y2  - 2012/04/09
ER  -
TY  - JOUR
T1  - End Modification of a Linear DNA Duplex Enhances NER-Mediated Excision of an Internal Pt(II)-Lesion
AU  - Mason, Tracey McGregor
AU  - Smeaton, Michael B.
AU  - Cheung, Joyce C. Y.
AU  - Hanakahi, Les A.
AU  - Miller, Paul S.
Y1  - 2008/05/01
PY  - 2008
DA  - 2008/05/01
N1  - doi: 10.1021/bc7004363
DO  - doi: 10.1021/bc7004363
T2  - Bioconjugate Chemistry
JF  - Bioconjugate Chemistry
JO  - Bioconjugate Chemistry
SP  - 1064
EP  - 1070
VL  - 19
IS  - 5
PB  - American Chemical Society
SN  - 1043-1802
M3  - doi: 10.1021/bc7004363
UR  - http://dx.doi.org/10.1021/bc7004363
Y2  - 2012/04/09
ER  -
TY  - JOUR
A1  - Smeaton, Michael B.
A1  - Miller, Paul S.
A1  - Ketner, Gary
A1  - Hanakahi, Les A.
T1  - Small-scale extracts for the study of nucleotide excision repair and non-homologous end joining
Y1  - 2007/12/01
JF  - Nucleic Acids Research
JO  - Nucleic Acids Research
SP  - e152
EP  - e152
N1  - doi: 10.1093/nar/gkm974
VL  - 35
IS  - 22
UR  - http://nar.oxfordjournals.org/content/35/22/e152.abstract
N2  - The repair of DNA by nucleotide excision repair (NER) and non-homologous end joining (NHEJ) is essential for maintenance of genomic integrity and cell viability. Examination of NHEJ and NER in vitro using cell-free extracts has led to a deeper understanding of the biochemical mechanisms that underlie these processes. Current methods for production of whole-cell extracts (WCEs) to investigate NER and NHEJ start with one or more liters of culture containing 1–5 × 109 cells. Here, we describe a small-scale method for production of WCE that can be used to study NER. We also describe a rapid, small-scale method for the preparation of WCE that can be used in the study of NHEJ. These methods require less time, 20- to 1000-fold fewer cells than large-scale extracts, facilitate examination of numerous samples and are ideal for such applications as the study of host–virus interactions and analysis of mutant cell lines.
ER  -
TY  - JOUR
T1  - The Vitamin E analog Trolox reduces copper toxicity in the annelid Lumbriculus variegatus but is also toxic on its own
JO  - NeuroToxicology
VL  - 27
IS  - 4
SP  - 604
EP  - 614
PY  - 2006/7//
T2  -
AU  - O’Gara, Bruce A.
AU  - Murray, Phillip M.
AU  - Hoyt, Erik M.
AU  - Leigh-Logan, Tifany
AU  - Smeaton, Michael B.
SN  - 0161-813X
M3  - doi: 10.1016/j.neuro.2006.03.023
UR  - http://www.sciencedirect.com/science/article/pii/S0161813X06000982
KW  - Metals
KW  - Reactive oxygen species
KW  - Antioxidant
KW  - Behavior
KW  - Neurophysiology
ER  -
TY  - JOUR
T1  - Copper-induced changes in locomotor behaviors and neuronal physiology of the freshwater oligochaete, Lumbriculus variegatus
JO  - Aquatic Toxicology
VL  - 69
IS  - 1
SP  - 51
EP  - 66
PY  - 2004/7/30/
T2  -
AU  - O’Gara, Bruce A.
AU  - Bohannon, V.Kim
AU  - Teague, Matthew W.
AU  - Smeaton, Michael B.
SN  - 0166-445X
M3  - doi: 10.1016/j.aquatox.2004.04.006
UR  - http://www.sciencedirect.com/science/article/pii/S0166445X04001341
KW  - Copper
KW  - Metals
KW  - Oligochaete
KW  - Sublethal
KW  - Behavior
KW  - Electrophysiology
ER  -
TY  - JOUR
AU  - Miller, Jeffrey C.
AU  - Tan, Siyuan
AU  - Qiao, Guijuan
AU  - Barlow, Kyle A.
AU  - Wang, Jianbin
AU  - Xia, Danny F.
AU  - Meng, Xiangdong
AU  - Paschon, David E.
AU  - Leung, Elo
AU  - Hinkley, Sarah J.
AU  - Dulay, Gladys P.
AU  - Hua, Kevin L.
AU  - Ankoudinova, Irina
AU  - Cost, Gregory J.
AU  - Urnov, Fyodor D.
AU  - Zhang, H. Steve
AU  - Holmes, Michael C.
AU  - Zhang, Lei
AU  - Gregory, Philip D.
AU  - Rebar, Edward J.
TI  - A TALE nuclease architecture for efficient genome editing
JA  - Nature Biotechnology
PY  - 2011/02/01/print
VL  - 29
IS  - 2
SP  - 143
EP  - 148
PB  - Nature Publishing Group, a division of Macmillan Publishers Limited. All Rights Reserved.
SN  - 1087-0156
UR  - http://dx.doi.org/10.1038/nbt.1755
M3  - doi: 10.1038/nbt.1755
N1  - doi: 10.1038/nbt.1755
L3  - http://www.nature.com/nbt/journal/v29/n2/abs/nbt.1755.html#supplementary-information
ER  -
TY  - JOUR
A1  - Roller, Maša
A1  - Lucić, Vedran
A1  - Nagy, István
A1  - Perica, Tina
A1  - Vlahoviček, Kristian
T1  - Environmental shaping of codon usage and functional adaptation across microbial communities
Y1  - 2013/10/01
JF  - Nucleic Acids Research
JO  - Nucleic Acids Research
SP  - 8842
EP  - 8852
N1  - doi: 10.1093/nar/gkt673
VL  - 41
IS  - 19
UR  - http://nar.oxfordjournals.org/content/41/19/8842.abstract
N2  - Microbial communities represent the largest portion of the Earth’s biomass. Metagenomics projects use high-throughput sequencing to survey these communities and shed light on genetic capabilities that enable microbes to inhabit every corner of the biosphere. Metagenome studies are generally based on (i) classifying and ranking functions of identified genes; and (ii) estimating the phyletic distribution of constituent microbial species. To understand microbial communities at the systems level, it is necessary to extend these studies beyond the species’ boundaries and capture higher levels of metabolic complexity. We evaluated 11 metagenome samples and demonstrated that microbes inhabiting the same ecological niche share common preferences for synonymous codons, regardless of their phylogeny. By exploring concepts of translational optimization through codon usage adaptation, we demonstrated that community-wide bias in codon usage can be used as a prediction tool for lifestyle-specific genes across the entire microbial community, effectively considering microbial communities as meta-genomes. These findings set up a ‘functional metagenomics’ platform for the identification of genes relevant for adaptations of entire microbial communities to environments. Our results provide valuable arguments in defining the concept of microbial species through the context of their interactions within the community.
ER  -
TY  - JOUR
T1  - Evolution of protein structures and interactions from the perspective of residue contact networks
JO  - Current Opinion in Structural Biology
VL  -
IS  - 0
SP  -
EP  -
T2  -
Y1  - 2013/07/25/
AU  - Zhang, Xiuwei
AU  - Perica, Tina
AU  - Teichmann, Sarah A.
SN  - 0959-440X
DO  - doi: 10.1016/j.sbi.2013.07.004
UR  - http://www.sciencedirect.com/science/article/pii/S0959440X13001255
ER  -
TY  - JOUR
T1  - Protein Complexes Are under Evolutionary Selection to Assemble via Ordered Pathways
JO  - Cell
VL  - 153
IS  - 2
SP  - 461
EP  - 470
PY  - 2013/4/11/
T2  -
AU  - Marsh, Joseph A.
AU  - Hernández, Helena
AU  - Hall, Zoe
AU  - Ahnert, Sebastian E.
AU  - Perica, Tina
AU  - Robinson, Carol V.
AU  - Teichmann, Sarah A.
SN  - 0092-8674
DO  - doi: 10.1016/j.cell.2013.02.044
UR  - http://www.sciencedirect.com/science/article/pii/S009286741300278X
ER  -
TY  - JOUR
T1  - The emergence of protein complexes: quaternary structure, dynamics and allostery
JO  - Biochemical Society Transactions
VL  - 40
IS  - 3
SP  - 475
EP  - 491
PY  - 2012/3/1/
T2  -
AU  - Perica, Tina
AU  - Marsh, Joseph A.
AU  - Sousa, Filipa L.
AU  - Natan, Eviatar
AU  - Colwell, Lucy J.
AU  - Ahnert, Sebastian E.
AU  - Teichmann, Sarah A.
DO  - doi: 10.1042/BST20120056
UR  - http://www.biochemsoctrans.org/bst/040/0475/bst0400475.htm
ER  -
TY  - JOUR
A1  - Liberles, David A.
A1  - Teichmann, Sarah A.
A1  - Bahar, Ivet
A1  - Bastolla, Ugo
A1  - Bloom, Jesse
A1  - Bornberg-Bauer, Erich
A1  - Colwell, Lucy J.
A1  - de Koning, A. P. Jason
A1  - Dokholyan, Nikolay V.
A1  - Echave, Julian
A1  - Elofsson, Arne
A1  - Gerloff, Dietlind L.
A1  - Goldstein, Richard A.
A1  - Grahnen, Johan A.
A1  - Holder, Mark T.
A1  - Lakner, Clemens
A1  - Lartillot, Nicholas
A1  - Lovell, Simon C.
A1  - Naylor, Gavin
A1  - Perica, Tina
A1  - Pollock, David D.
A1  - Pupko, Tal
A1  - Regan, Lynne
A1  - Roger, Andrew
A1  - Rubinstein, Nimrod
A1  - Shakhnovich, Eugene
A1  - Sjölander, Kimmen
A1  - Sunyaev, Shamil
A1  - Teufel, Ashley I.
A1  - Thorne, Jeffrey L.
A1  - Thornton, Joseph W.
A1  - Weinreich, Daniel M.
A1  - Whelan, Simon
T1  - The interface of protein structure, protein biophysics, and molecular evolution
JF  - Protein Science
JA  - Protein Science
VL  - 21
IS  - 6
PB  - Wiley Subscription Services, Inc., A Wiley Company
SN  - 1469-896X
UR  - http://dx.doi.org/10.1002/pro.2071
DO  - doi: 10.1002/pro.2071
SP  - 769
EP  - 785
KW  - evolutionary modeling
KW  - domain evolution
KW  - sequence-structure-function relationships
KW  - protein dynamics
KW  - protein thermodynamics
KW  - gene duplication
KW  - protein expression
KW  - ancestral sequence reconstruction
PY  - 2012
Y1  - 2012/06/01
ER  -
TY  - JOUR
A1  - Perica, Tina
A1  - Chothia, Cyrus
A1  - Teichmann, Sarah A.
T1  - Evolution of oligomeric state through geometric coupling of protein interfaces
Y1  - 2012/05/22
JF  - Proceedings of the National Academy of Sciences
JO  - Proceedings of the National Academy of Sciences
SP  - 8127
EP  - 8132
N1  - doi: 10.1073/pnas.1120028109
VL  - 109
IS  - 21
UR  - http://www.pnas.org/content/109/21/8127.abstract
N2  - Oligomerization plays an important role in the function of many proteins. Thus, understanding, predicting, and, ultimately, engineering oligomerization presents a long-standing interest. From the perspective of structural biology, protein–protein interactions have mainly been analyzed in terms of the biophysical nature and evolution of protein interfaces. Here, our aim is to quantify the importance of the larger structural context of protein interfaces in protein interaction evolution. Specifically, we ask to what extent intersubunit geometry affects oligomerization state. We define a set of structural parameters describing the overall geometry and relative positions of interfaces of homomeric complexes with different oligomeric states. This allows us to quantify the contribution of direct sequence changes in interfaces versus indirect changes outside the interface that affect intersubunit geometry. We find that such indirect, or allosteric mutations affecting intersubunit geometry via indirect mechanisms are as important as interface sequence changes for evolution of oligomeric states.
ER  -
TY  - JOUR
T1  - Ubiquitin--molecular mechanisms for recognition of different structures
JO  - Current Opinion in Structural Biology
VL  - 20
IS  - 3
SP  - 367
EP  - 376
PY  - 2010/6//
T2  - Nucleic acids / Sequences and topology
AU  - Perica, Tina
AU  - Chothia, Cyrus
SN  - 0959-440X
DO  - doi:  10.1016/j.sbi.2010.03.007
UR  - http://www.sciencedirect.com/science/article/pii/S0959440X10000606
ER  -
TY  - JOUR
A1  - Crosetto, Nicola
A1  - Bienko, Marzena
A1  - Hibbert, Richard G.
A1  - Perica, Tina
A1  - Ambrogio, Chiara
A1  - Kensche, Tobias
A1  - Hofmann, Kay
A1  - Sixma, Titia K.
A1  - Dikic, Ivan
T1  - Human Wrnip1 Is Localized in Replication Factories in a Ubiquitin-binding Zinc Finger-dependent Manner
Y1  - 2008/12/12
JF  - Journal of Biological Chemistry
JO  - Journal of Biological Chemistry
SP  - 35173
EP  - 35185
N1  - doi: 10.1074/jbc.M803219200
VL  - 283
IS  - 50
UR  - http://www.jbc.org/content/283/50/35173.abstract
N2  - Wrnip1 (Werner helicase-interacting protein 1) has been implicated in the bypass of stalled replication forks in bakers' yeast. However, the function(s) of human Wrnip1 has remained elusive so far. Here we report that Wrnip1 is distributed inside heterogeneous structures detectable in nondamaged cells throughout the cell cycle. In an attempt to characterize these structures, we found that Wrnip1 resides in DNA replication factories. Upon treatments that stall replication forks, such as UVC light, the amount of chromatin-bound Wrnip1 and the number of foci significantly increase, further implicating Wrnip1 in DNA replication. Interestingly, the nuclear pattern of Wrnip1 appears to extend to a broader landscape, as it can be detected in promyelocytic leukemia nuclear bodies. The presence of Wrnip1 into these heterogeneous subnuclear structures requires its ubiquitin-binding zinc finger (UBZ) domain, which is able to interact with different ubiquitin (Ub) signals, including mono-Ub and chains linked via lysine 48 and 63. Moreover, the oligomerization of Wrnip1 mediated by its C terminus is also important for proper subnuclear localization. Our study is the first to reveal the composite and regulated topography of Wrnip1 in the human nucleus, highlighting its potential role in replication and other nuclear transactions.
ER  -
'''

test_journal_DOIs = [
    # Journals
    '10.1371/journal.pone.0097279',
    '10.1002/pro.2421', # The title has embedded HTML and bad white-spacing
    '10.1093/bioinformatics/btt735',
    '10.1109/TCBB.2013.113', # the title is contained inside a CDATA block
    '10.1038/nnano.2013.242',
    '10.1021/ja404992r',
    '10.1371/journal.pone.0063090',
    '10.1073/pnas.1300327110',
    '10.1371/journal.pone.0063906',
    '10.1016/j.str.2012.10.007',
    '10.1371/journal.pcbi.1002639',
    '10.1126/science.1219083',
    '10.1073/pnas.1114487109',
    '10.1038/nature10719',
    '10.1016/j.cell.2011.07.038',
    '10.1371/journal.pone.0020451',
    '10.1002/pro.632',
    '10.1016/j.jmb.2010.12.019',
    '10.1016/j.jmb.2010.07.032',
    '10.1083/jcb.201004060',
    '10.1093/nar/gkq369',
    '10.1016/j.sbi.2010.02.004',
    '10.1038/nchembio.251',
    '10.1016/j.copbio.2009.07.006',
    '10.1038/nmeth0809-551',
    '10.1371/journal.pcbi.1000393',
    '10.1038/msb.2009.9',
    '10.1016/j.str.2008.12.014',
    '10.1002/prot.22293',
    '10.1016/j.str.2008.11.004',
    '10.1016/j.str.2008.09.012',
    '10.1074/jbc.M806370200',
    '10.1016/j.jmb.2008.05.006',
    '10.1016/j.jmb.2008.05.023',
    '10.1016/j.jmb.2007.11.020',
    '10.1371/journal.pcbi.0030164',
    '10.1074/jbc.M704513200',
    '10.1016/j.str.2007.09.010',
    '10.1016/j.jmb.2006.05.022',
    '10.1016/j.chembiol.2006.03.007',
    '10.1074/jbc.M510454200',
    '10.1073/pnas.0608127103',
    '10.1073/pnas.0600489103',
    '10.1073/pnas.202485799',
    '10.1016/S1097-2765(02)00690-1',
    '10.1002/prot.10384',
    '10.1038/nsmb749',
    '10.1016/j.cbpa.2003.12.008',
    '10.1016/S0022-2836(03)00021-4',
    '10.1021/jp0267555',
    '10.1126/stke.2192004pl2',
    '10.1073/pnas.0307578101',
    '10.1093/nar/gkh785',
    '10.1002/prot.20347',
    '10.1016/S0969-2126(03)00047-9',
    '10.1016/S1097-2765(03)00365-4',
    '10.1021/bi034873s',
    '10.1021/bi00072a010',
    '10.1002/pro.5560030514',
    '10.1126/science.281.5374.253',
    '10.1016/S0968-0896(98)00215-6',
    '10.1016/S0959-440X(99)80069-4',
    '10.1006/jmbi.1996.0155',
    '10.1006/jmbi.2000.3618',
    '10.1016/S0022-2836(02)00706-4',
    '10.1006/jmbi.1995.0592',
    '10.1021/bi9617724',
    '10.1021/bi973101r',
    '10.4049/jimmunol.1101494',
    '10.1126/science.1205822',
    '10.1021/jp800282x',
    '10.1371/journal.pbio.1000450',
    '10.1101/gr.074344.107',
    '10.1186/1471-2148-7-24',
    '10.1093/icb/icl035',
    '10.1103/PhysRevE.74.051801',
    '10.1021/bi101413v',
    '10.1021/bi9012897',
    '10.1039/B821345C',
    '10.1021/bi801397e',
    '10.1021/jp801174z',
    '10.1529/biophysj.107.106633',
    '10.1021/bi051448l',
    '10.1093/bioinformatics/btq495',
    '10.1073/pnas.0801207105',
    '10.1186/gb-2006-7-12-r125',
    '10.1021/cb3006402',
    '10.1002/pro.735',
    '10.1021/bi100975z',
    '10.1021/bi802027g',
    '10.1093/bioinformatics/bti828',
    '10.1074/jbc.M401675200',
    '10.1016/j.str.2011.03.009',
    '10.1016/j.sbi.2011.01.005',
    '10.1371/journal.pone.0031220',
    '10.1074/mcp.M111.014969',
    '10.1093/nar/gks446',
    '10.1038/embor.2010.171',
    '10.1093/nar/gkq962',
    '10.1371/journal.pcbi.1000789',
    '10.1093/nar/gkq194',
    '10.1016/j.str.2010.08.001',
    '10.1111/j.1742-4658.2009.07251.x',
    '10.1093/nar/gkn690',
    '10.1021/ci800174c',
    '10.1371/journal.pone.0002524',
    '10.1016/j.febslet.2008.02.020',
    '10.1093/nar/gki037',
    '10.1186/1752-0509-3-74',
    '10.1002/pmic.200700966',
    '10.1016/j.febslet.2008.02.014',
    '10.1089/cmb.2007.0178',
    '10.3233/SPE-2008-0361', # No DOI record in CrossRef (the DOI is valid)
    '10.1016/j.bbrc.2007.04.113',
    '10.1007/s11306-006-0028-0',
    '10.1021/ac051437y',
    '10.1021/ac051312t',
    '10.1021/ja210118w',
    '10.1002/prot.23225',
    '10.1002/prot.22518',
    '10.1073/pnas.0906652106',
    '10.1074/jbc.M504922200',
    '10.1186/gb-2004-5-10-r80',
    '10.1038/nchembio.522',
    '10.1002/em.20559',
    '10.1021/bi902169q',
    '10.1021/tx9000896',
    '10.1021/bi800925e',
    '10.1021/bc7004363',
    '10.1093/nar/gkm974',
    '10.1016/j.neuro.2006.03.023', # the authors' names are all in uppercase
    '10.1016/j.aquatox.2004.04.006',
    '10.1038/nbt.1755',
    '10.1093/nar/gkt673',
    '10.1016/j.sbi.2013.07.004',
    '10.1016/j.cell.2013.02.044',
    '10.1042/BST20120056',
    '10.1002/pro.2071',
    '10.1073/pnas.1120028109',
    '10.1016/j.sbi.2010.03.007',
    '10.1074/jbc.M803219200',
    '10.1371/journal.ppat.1004204',
    '10.1016/j.cell.2014.04.034',
    '10.1038/nchembio.1554',
    '10.1042/BST20130055',
    '10.1038/nature13404',
    '10.1073/pnas.1321126111',
    '10.1038/nchembio.1498',
    '10.1093/protein/gzt061', # has both online and print dates so it is a good one to test our code to choose the earliest date
    '10.1038/nature12966',
    '10.1515/hsz-2013-0230',
    '10.1016/j.str.2013.08.009',
    '10.1073/pnas.1314045110',
    '10.1016/j.jmb.2013.06.035',
    '10.1038/nature12443',
    '10.1021/ja403503m',
    '10.1007/s10858-013-9762-6',
    '10.1016/j.str.2013.08.005',
    '10.1002/prot.24463',
    '10.1002/pro.2389',
    '10.1016/j.jmb.2013.10.012',
    '10.1007/s10858-013-9772-4',
    '10.1021/cb4004892',
    '10.1002/prot.24356',
    '10.1038/nmeth.2648',
    '10.1002/anie.201204077',
    '10.1126/science.1234150',
    '10.1371/journal.ppat.1003245',
    '10.1002/pro.2267',
    '10.1002/prot.24374',
    '10.1021/sb300061x',
    '10.1038/ncomms3974',
    '10.1038/nchembio.1276',
    '10.1021/cb3006227',
    '10.1038/nature12007',
    '10.1371/journal.ppat.1003307',
    '10.1371/journal.pone.0059004',
    '10.1021/ja3037367',
    '10.1038/nature11600',
    '10.1038/nbt.2214',
    '10.1002/pro.2059',
    '10.1007/s10969-012-9129-3',
    '10.1038/nchembio.777',
    '10.1002/jcc.23069',
    '10.1021/ja3094795',
    '10.1038/nbt.2109',
    '10.1126/science.1219364',
    '10.1038/nature11079',
    '10.1038/nature10349',
    '10.1038/nsmb.2119',
    '10.1002/prot.22921',
    '10.1038/nature10154',
    '10.1002/prot.23046',
    '10.1002/pro.604',
    '10.1002/pro.462',
    '10.1021/jp037711e',
]

test_book_DOIs = [
    # I do not currently have a parser for these cases
    '10.1016/B978-0-12-394292-0.00004-7',
    '10.1016/B978-0-12-394292-0.00006-0',
    '10.1016/B978-0-12-381270-4.00019-6',
    '10.1016/S0065-3233(05)72001-5',
    '10.5772/52250',
    '10.1007/978-1-62703-968-0_17',
    '10.1016/B978-0-12-394292-0.00001-1',
    '10.1016/B978-0-12-394292-0.00006-0',
]

if __name__ == '__main__':
    import sys
    import string
    import traceback
    sys.path.insert(0, '../..')

    from klab import colortext
    from doi import DOI, RecordTypeParsingNotImplementedException, CrossRefException
    from ris import RISEntry

    targets = set(map(string.lower,(sys.argv[1:])))

    if 'ris' in targets:
        cases = [c.strip() for c in RIS_test.split('ER  -') if c.strip()]
        count = 0
        for c in cases:
            try:
                r = RISEntry(c, lenient_on_tag_order = True)
                d = r.to_dict()
                if count % 2 == 0:
                    colortext.message(r.to_string())
                else:
                    colortext.warning(r.to_string())
                count += 1
            except Exception, e:
                colortext.message(c)
                colortext.warning(str(e))
                colortext.error(traceback.format_exc())
                sys.exit(1)


    if 'doi' in targets:
        try_count = 0
        print(len(test_journal_DOIs))
        for d in test_journal_DOIs:
            try_count += 1
            #if try_count > 7:
            #    break
            try:
                print('')
                colortext.message(d)
                doi = DOI(d)
                #colortext.warning(doi)
                #print(doi.data)
                #colortext.message('print_string')
                print(colortext.make(doi.to_string(html=False), 'cyan'))
                #print(colortext.make(str(doi), 'orange'))
                colortext.warning(doi.issue.get('__issue_date') or doi.article.get('__issue_date'))
                colortext.warning(doi.get_earliest_date())
                url_string = 'www.crossref.org/guestquery?queryType=doi&restype=unixref&doi=%s&doi_search=Search' % d
                print(url_string)
                if not (doi.issue.get('__issue_date') or doi.article.get('__issue_date')):
                    break
                j = doi.to_json()
                r = doi.convert_to_ris()
                print('')
            except RecordTypeParsingNotImplementedException, e:
                colortext.error('Unhandled type: %s' % str(e))
                print('')
                continue
            except CrossRefException, e:
                colortext.error('CrossRef exception: %s' % str(e))
                print('')
                continue
        print('\n\n\n')
