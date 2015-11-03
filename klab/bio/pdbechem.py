# #!/usr/bin/python
# encoding: utf-8
"""
pdbechem.py
An XML parser for the PDBeChem XML file for the wwPDB ligand dictionary. See ftp://ftp.ebi.ac.uk/pub/databases/msd/pdbechem/readme.htm.

Created by Shane O'Connor 2013
"""

if __name__ == '__main__':
    import sys
    sys.path.insert(0, "../..")
from klab.fs.fsio import read_file
from klab.comms.ftp import get_insecure_resource, FTPException550
from klab import colortext
from xml.dom.minidom import parseString

def pdbechem_parse(download = False, filename = '/kortemmelab/shared/mirror/PDBeChem/chem_comp.xml'):
    '''This is slower than using SAX but much easier to write/read. If you need this to perform well, rewrite with SAX.'''

    xml_data = None
    if download:
        # this URL will go out of date
        try:
            resource = ['ftp.ebi.ac.uk', '/pub/databases/msd/pdbechem/chem_comp.xml']
            xml_data = get_insecure_resource(resource[0], resource[1])
        except FTPException550, e:
            colortext.error("This resource ftp://%s appears to be missing. The link may need to be updated in the script." % "".join(resource))
            raise
        except Exception, e:
            colortext.error("An error occurred downloading ftp://%s:\n%s" % ("".join(resource), str(e)))
            raise
    else:
        xml_data = read_file(filename)

    _dom = parseString(xml_data)

    main_tag = _dom.getElementsByTagName("chemCompList")
    assert(len(main_tag) == 1)
    main_tag = main_tag[0]
    entries = main_tag.getElementsByTagName("chemComp")

    parsed_dict = {}
    properties = ["id", "name", "formula", "systematicName", "stereoSmiles", "nonStereoSmiles", "InChi"]
    for e in entries:
        d = {}
        for p in properties:
            t = e.getElementsByTagName(p)
            assert(len(t) <= 1)
            if p == "id":
                assert(len(t) == 1 and t[0].childNodes)
            if len(t):
                if t[0].childNodes:
                    d[p] = t[0].firstChild.nodeValue
                else:
                    d[p] = None
            else:
                d[p] = None
        parsed_dict[d['id']] = d
    return parsed_dict

if __name__ == '__main__':
    pdbechem_parse()