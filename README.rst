klab - The Kortemme Lab Tools Repository
========================
A collection of utilities used by our lab for computational biophysics, including PDB parsing, SGE cluster submission scripts, and interfaces with the Rosetta macromolecular software suite.

Coding convention
=================

Besides the whitespace convention (spaces, not tabs), contributors can / generally do use their own preferences. However, code within a module should follow a consistent convention. Finally, please do not reformat modules created by other developers to your preferences.

Here are some semi-standard guidelines: 

- General rules      : The PEP 8 conventions (https://www.python.org/dev/peps/pep-0008/) are mostly sensible.
- Blank lines        : See "Blank Lines" in PEP 8. Particularly, surround top-level function and class definitions with two blank lines.
- Line length        : Up to the module creator programmer.
- Whitespace         : Use spaces instead of tabs, with indents set to 4 spaces. Feel free to nuke any tabbed indents with prejudice.
- Import order       : Import standard Python packages first (sys, os) then higher-level/add-on packages (sqlalchemy, numpy), then our other packages (klab), then this package (kddg). Put a line break between each section of imports.
- Natural language   : Please do not introduce contractions into alien modules unless that is the usual for that module.

Installation
============

This package can be installed via:
::
  pip install klab

To install via pip and allow git push/pulling, use:

In a virtualenv:
::
  pip install -e git+ssh://git@github.com/Kortemme-Lab/klab.git#egg=klab

In your user-directory:
::
  pip install --user -e git+ssh://git@github.com/Kortemme-Lab/klab.git#egg=klab

In your user-directory, without using SSH:
::
  pip install --user -e git+https://github.com/Kortemme-Lab/klab.git#egg=klab
