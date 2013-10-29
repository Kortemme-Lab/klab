#!/bin/bash

# Script to compile and run all tests for two specified Rosetta revisions
# This script expects to live in your "Rosetta" directory, at the same level
#   as main, tools, demos, etc.
# Symlink this version controlled version into your Rosetta directory to
#  keep it always up to date
# Two arguments:
#  1 - SHA1 of new revision to be tested
#  2 - SHA1 of parent revision to be compared against

NUMPROC=$(nproc)
TESTING_DIR="testing"
REPO_DIR=$1
output_file=testing_results
dev_branch_name=testing_branch

echo "Starting time: `date`"

if [ -d $TESTING_DIR ]; then
    if [ -d $TESTING_DIR/$REPO_DIR ]; then
	echo "Testing directory '$TESTING_DIR/$REPO_DIR' already exists"
	echo "You must remove it before rerunning this script"
	exit
    fi
else
    mkdir $TESTING_DIR
fi

cd $TESTING_DIR

echo "Cloning repository"
git clone -n -l ../main $REPO_DIR
cd $REPO_DIR
echo "Starting time: `date`" > $output_file
echo "  Testing new revision $1" >> $output_file
echo "   against parent revision $2" >> $output_file

git remote rename origin local
git remote add origin git@github.com:RosettaCommons/main.git
git fetch origin

git checkout -b parent $2
git checkout -b $dev_branch_name $1
git checkout parent
cd ..

echo "Compiling parent_release..."
cd $REPO_DIR/source
nice -n 15 ./scons.py bin mode=release -j $NUMPROC &>> parent_release.compilation.out
echo "Compilation done"
echo "Finished compiling parent_release at: `date`" >> ../$output_file
echo "  output at: source/parent_release.compilation.out" >> ../$output_file
cd ../..

# echo "Running initial score to build dunbrack binary..."
# cd $REPO_DIR/source/bin
# ./score.linuxgccrelease -s ../../tests/integration/tests/score_jd2/1l2y.pdb &>> ../run_initial_score
# rm -f S_0001.pdb
# rm -f score.sc
# echo "Finished running inital score at: `date`" >> ../../$output_file
# cd ../../..

echo "Running parent integration tests"
cd $REPO_DIR/tests/integration
nice -n 15 ./integration.py -j $NUMPROC -d ../../database &>> parent_integration.out
cd ../../..
echo "Finished running parent integration tests at: `date`" >> $REPO_DIR/$output_file
echo "  output at: tests/integration/parent_integration.out" >> $REPO_DIR/$output_file

echo "Running parent integration tests again..."
# We have to do this until the problems with Dunbrack binaries are fixed
cd $REPO_DIR/tests/integration
nice -n 15 ./integration.py -j $NUMPROC -d ../../database &>> parent_integration.out
rm -rf ref
mv new ref
cd ../../..
echo "Finished running parent integration tests again at: `date`" >> $REPO_DIR/$output_file
echo "  output at: tests/integration/parent_integration.out" >> $REPO_DIR/$output_file

echo "Compiling new_release..."
cd $REPO_DIR/source
git checkout $dev_branch_name
nice -n 15 ./scons.py bin mode=release -j $NUMPROC &>> new_release.compilation.out
echo "Compilation done"
echo "Finished compiling new_release at: `date`" >> ../$output_file
cd ../..

echo "Running new integration tests"
cd $REPO_DIR/tests/integration
nice -n 15 ./integration.py -j $NUMPROC -d ../../database &>> new_integration.out
cd ../../..
echo "Finished running new integration tests at: `date`" >> $REPO_DIR/$output_file
echo "  output at: tests/integration/new_integration.out" >> $REPO_DIR/$output_file


echo "Compiling new_debug..."
cd $REPO_DIR/source
nice -n 15 ./scons.py -j $NUMPROC &>> new_debug.compilation.out
nice -n 15 ./scons.py -j $NUMPROC cat=test &>> new_debug.compilation.out
echo "Compilation done"
echo "Finished compiling new_debug at: `date`" >> ../$output_file
echo "  output at: source/new_debug.compilation.out" >> ../$output_file

cd ../..

echo "Running unit tests"
cd $REPO_DIR/source
nice -n 15 python test/run.py -j $NUMPROC -d ../database --mute all &>> unit_tests.out
echo "Finished running unit tests at: `date`" >> ../$output_file
echo "  output at: source/unit_tests.out" >> ../$output_file
echo "Finishing time: `date`" >> ../$output_file
cd ../..

echo "Finishing time: `date`"