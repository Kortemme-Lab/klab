#!/bin/bash

# This scripts runs all the calcs for the 11 non-mutated proteins 
echo "Processing 1A8G"
./calc_Ca-Ca_distances.pl ../1A8G_ensemble 1A8G > 1A8G-sims.txt
./calc_Ca-Ca_distances.pl ../1A8G_ensemble_1.2 1A8G >> 1A8G-sims.txt

echo "Processing 1EBY"
./calc_Ca-Ca_distances.pl ../1EBY_ensemble 1EBY > 1EBY-sims.txt
./calc_Ca-Ca_distances.pl ../1EBY_ensemble_1.2 1EBY >> 1EBY-sims.txt

echo "Processing 1HXW"
./calc_Ca-Ca_distances.pl ../1HXW_ensemble 1HXW > 1HXW-sims.txt
./calc_Ca-Ca_distances.pl ../1HXW_ensemble_1.2 1HXW >> 1HXW-sims.txt

echo "Processing 1IZH"
./calc_Ca-Ca_distances.pl ../1IZH_ensemble 1IZH > 1IZH-sims.txt
./calc_Ca-Ca_distances.pl ../1IZH_ensemble_1.2 1IZH >> 1IZH-sims.txt

echo "Processing 1PRO"
./calc_Ca-Ca_distances.pl ../1PRO_ensemble 1PRO > 1PRO-sims.txt
./calc_Ca-Ca_distances.pl ../1PRO_ensemble_1.2 1PRO >> 1PRO-sims.txt

echo "Processing 1SBG"
./calc_Ca-Ca_distances.pl ../1SBG_ensemble 1SBG > 1SBG-sims.txt
./calc_Ca-Ca_distances.pl ../1SBG_ensemble_1.2 1SBG >> 1SBG-sims.txt

echo "Processing 1VIJ"
./calc_Ca-Ca_distances.pl ../1VIJ_ensemble 1VIJ > 1VIJ-sims.txt
./calc_Ca-Ca_distances.pl ../1VIJ_ensemble_1.2 1VIJ >> 1VIJ-sims.txt

echo "Processing 1VIK"
./calc_Ca-Ca_distances.pl ../1VIK_ensemble 1VIK > 1VIK-sims.txt
./calc_Ca-Ca_distances.pl ../1VIK_ensemble_1.2 1VIK >> 1VIK-sims.txt

echo "Processing 4PHV"
./calc_Ca-Ca_distances.pl ../4PHV_ensemble 4PHV > 4PHV-sims.txt
./calc_Ca-Ca_distances.pl ../4PHV_ensemble_1.2 4PHV >> 4PHV-sims.txt

echo "Processing 5HVP"
./calc_Ca-Ca_distances.pl ../5HVP_ensemble 5HVP > 5HVP-sims.txt
./calc_Ca-Ca_distances.pl ../5HVP_ensemble_1.2 5HVP >> 5HVP-sims.txt

echo "Processing 9HVP"
./calc_Ca-Ca_distances.pl ../9HVP_ensemble 9HVP > 9HVP-sims.txt
./calc_Ca-Ca_distances.pl ../9HVP_ensemble_1.2 9HVP >> 9HVP-sims.txt

