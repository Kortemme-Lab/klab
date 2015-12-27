klab - The Kortemme Lab Tools Repository
========================
A collection of utilities used by our lab for computational biophysics, including PDB parsing, SGE cluster submission scripts, and interfaces with the Rosetta macromolecular software suite.

Since this is a shared repository and the consensus in the lab is to use spaces rather than tabs for code, all code herein should use spaces. Feel free to remove tabs at will.

This package can be installed via:
::
  pip install klab

To install via pip and allow git push/pulling, use:

In a virtualenv:
::
  pip install -e git+ssh://git@github.com/Kortemme-Lab/klab.git#egg=Package

In your user-directory:
::
  pip install --user -e git+ssh://git@github.com/Kortemme-Lab/klab.git#egg=Package

In your user-directory, without using SSH:
::
  pip install --user -e git+https://github.com/Kortemme-Lab/klab.git#egg=Package
  
