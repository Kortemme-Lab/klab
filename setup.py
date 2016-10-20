#!/usr/bin/env python2

from setuptools import setup, find_packages

# Uploading to PyPI
# =================
# The first time only:
# $ python setup.py register -r pypi
#
# Every version bump:
# $ git tag <version>; git push --tags
# $ python setup.py sdist upload -r pypi

version = '0.3.0'
setup(
    name='klab',
    version=version,
    author='Kortemme Lab, UCSF',
    author_email='support@kortemmelab.ucsf.edu',
    url='https://github.com/Kortemme-Lab/klab',
    download_url='https://github.com/Kortemme-Lab/klab/tarball/'+version,
    license='MIT',
    description="A collection of utilities used by our lab for computational biophysics",
    long_description=open('README.rst').read(),
    keywords=['utilities', 'library', 'biophysics'],
    classifiers=[
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Development Status :: 3 - Alpha",
        'Programming Language :: Python :: 2',
    ],
    packages=find_packages(),
    package_data={
        'klab.bio.fragments': [
            'make_fragments_RAP_cluster.pl',

        ],
    },
    install_requires=[],
    entry_points={
        'console_scripts': [
            'klab_generate_fragments=klab.bio.fragments.generate_fragments:main',
        ],
    },
)
