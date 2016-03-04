#!/usr/bin/python
# encoding: utf-8
"""
colors.py
A list of predefined PyMOL colors.

Created by Shane O'Connor 2014.
"""

import traceback
import colorsys

import matplotlib.colors as mpl_colors

from klab.gfx.colors import ggplot_color_wheel

# How to update this list:
#
# Go to http://pymolwiki.org/index.php/Color_Values and copy the color lines from there. Then run this in a Python terminal:
#
# a = '''[paste the lines]'''
# colors = {}
# lines = a.split('\n')
# for l in lines:
#     tokens = [t.strip() for t in l.split() if t.strip()]
#     if len(tokens) > 3:
#         try:
#             r, g, b = float(tokens[1]), float(tokens[2]), float(tokens[3])
#             colors[tokens[0]] = (r, g, b, tokens[4:])
#         except: pass
# print('predefined = {')
# for k, v in sorted(colors.iteritems()):
#     if v[3]:
#         print('\t# %s' % str(v[3:]))
#     print("\t'%s' : %s," % (k, str(v[:3])))
# print('}')

predefined = {
    'actinium' : (0.439215686, 0.670588235, 0.980392157),
    'aluminum' : (0.749019608, 0.650980392, 0.650980392),
    'americium' : (0.329411765, 0.360784314, 0.949019608),
    'antimony' : (0.619607843, 0.388235294, 0.709803922),
    'aquamarine' : (0.5, 1.0, 1.0),
    'argon' : (0.501960784, 0.819607843, 0.890196078),
    'arsenic' : (0.741176471, 0.501960784, 0.890196078),
    'astatine' : (0.458823529, 0.309803922, 0.270588235),
    'barium' : (0.0, 0.788235294, 0.0),
    'berkelium' : (0.541176471, 0.309803922, 0.890196078),
    'beryllium' : (0.760784314, 1.0, 0.0),
    'bismuth' : (0.619607843, 0.309803922, 0.709803922),
    'black' : (0.0, 0.0, 0.0),
    'blue' : (0.0, 0.0, 1.0),
    'bluewhite' : (0.85, 0.85, 1.0),
    'bohrium' : (0.878431373, 0.0, 0.219607843),
    'boron' : (1.0, 0.709803922, 0.709803922),
    'br0' : (0.1, 0.1, 1.0),
    'br1' : (0.2, 0.1, 0.9),
    'br2' : (0.3, 0.1, 0.8),
    'br3' : (0.4, 0.1, 0.7),
    'br4' : (0.5, 0.1, 0.6),
    'br5' : (0.6, 0.1, 0.5),
    'br6' : (0.7, 0.1, 0.4),
    'br7' : (0.8, 0.1, 0.3),
    'br8' : (0.9, 0.1, 0.2),
    'br9' : (1.0, 0.1, 0.1),
    'brightorange' : (1.0, 0.7, 0.2),
    'bromine' : (0.650980392, 0.160784314, 0.160784314),
    'brown' : (0.65, 0.32, 0.17),
    'cadmium' : (1.0, 0.850980392, 0.560784314),
    'calcium' : (0.239215686, 1.0, 0.0),
    'californium' : (0.631372549, 0.211764706, 0.831372549),
    'carbon' : (0.2, 1.0, 0.2),
    'cerium' : (1.0, 1.0, 0.780392157),
    'cesium' : (0.341176471, 0.090196078, 0.560784314),
    'chartreuse' : (0.5, 1.0, 0.0),
    'chlorine' : (0.121568627, 0.941176471, 0.121568627),
    'chocolate' : (0.555, 0.222, 0.111),
    'chromium' : (0.541176471, 0.6, 0.780392157),
    'cobalt' : (0.941176471, 0.564705882, 0.62745098),
    'copper' : (0.784313725, 0.501960784, 0.2),
    'curium' : (0.470588235, 0.360784314, 0.890196078),
    'cyan' : (0.0, 1.0, 1.0),
    'darksalmon' : (0.73, 0.55, 0.52),
    'dash' : (1.0, 1.0, 0.0),
    'deepblue' : (0.25, 0.25, 0.65),
    'deepolive' : (0.6, 0.6, 0.1),
    'deeppurple' : (0.6, 0.1, 0.6),
    'deepsalmon' : (1.0, 0.42, 0.42),
    'deepteal' : (0.1, 0.6, 0.6),
    'density' : (0.1, 0.1, 0.6),
    'deuterium' : (0.9, 0.9, 0.9),
    'dirtyviolet' : (0.7, 0.5, 0.5),
    'dubnium' : (0.819607843, 0.0, 0.309803922),
    'dysprosium' : (0.121568627, 1.0, 0.780392157),
    'einsteinium' : (0.701960784, 0.121568627, 0.831372549),
    'erbium' : (0.0, 0.901960784, 0.458823529),
    'europium' : (0.380392157, 1.0, 0.780392157),
    'fermium' : (0.701960784, 0.121568627, 0.729411765),
    'firebrick' : (0.698, 0.13, 0.13),
    'fluorine' : (0.701960784, 1.0, 1.0),
    'forest' : (0.2, 0.6, 0.0),
    'francium' : (0.258823529, 0.0, 0.4),
    'gadolinium' : (0.270588235, 1.0, 0.780392157),
    'gallium' : (0.760784314, 0.560784314, 0.560784314),
    'germanium' : (0.4, 0.560784314, 0.560784314),
    'gold' : (1.0, 0.819607843, 0.137254902),
    'gray' : (0.5, 0.5, 0.5),
    'green' : (0.0, 1.0, 0.0),
    'greencyan' : (0.25, 1.0, 0.75),
    'grey' : (0.5, 0.5, 0.5),
    'grey10' : (0.1, 0.1, 0.1),
    'grey30' : (0.3, 0.3, 0.3),
    'grey40' : (0.4, 0.4, 0.4),
    'grey60' : (0.6, 0.6, 0.6),
    'grey70' : (0.7, 0.7, 0.7),
    'grey80' : (0.8, 0.8, 0.8),
    'grey90' : (0.9, 0.9, 0.9),
    'hafnium' : (0.301960784, 0.760784314, 1.0),
    'hassium' : (0.901960784, 0.0, 0.180392157),
    'helium' : (0.850980392, 1.0, 1.0),
    'holmium' : (0.0, 1.0, 0.611764706),
    'hotpink' : (1.0, 0.0, 0.5),
    'hydrogen' : (0.9, 0.9, 0.9),
    'indium' : (0.650980392, 0.458823529, 0.450980392),
    'iodine' : (0.580392157, 0.0, 0.580392157),
    'iridium' : (0.090196078, 0.329411765, 0.529411765),
    'iron' : (0.878431373, 0.4, 0.2),
    'krypton' : (0.360784314, 0.721568627, 0.819607843),
    'lanthanum' : (0.439215686, 0.831372549, 1.0),
    'lawrencium' : (0.780392157, 0.0, 0.4),
    'lead' : (0.341176471, 0.349019608, 0.380392157),
    'lightblue' : (0.75, 0.75, 1.0),
    'lightmagenta' : (1.0, 0.2, 0.8),
    'lightorange' : (1.0, 0.8, 0.5),
    'lightpink' : (1.0, 0.75, 0.87),
    'lightteal' : (0.4, 0.7, 0.7),
    'lime' : (0.5, 1.0, 0.0),
    'limegreen' : (0.0, 1.0, 0.5),
    'limon' : (0.75, 1.0, 0.25),
    'lithium' : (0.8, 0.501960784, 1.0),
    'lutetium' : (0.0, 0.670588235, 0.141176471),
    'magenta' : (1.0, 0.0, 1.0),
    'magnesium' : (0.541176471, 1.0, 0.0),
    'manganese' : (0.611764706, 0.478431373, 0.780392157),
    'marine' : (0.0, 0.5, 1.0),
    'meitnerium' : (0.921568627, 0.0, 0.149019608),
    'mendelevium' : (0.701960784, 0.050980392, 0.650980392),
    'mercury' : (0.721568627, 0.721568627, 0.815686275),
    'molybdenum' : (0.329411765, 0.709803922, 0.709803922),
    'neodymium' : (0.780392157, 1.0, 0.780392157),
    'neon' : (0.701960784, 0.890196078, 0.960784314),
    'neptunium' : (0.0, 0.501960784, 1.0),
    'nickel' : (0.31372549, 0.815686275, 0.31372549),
    'niobium' : (0.450980392, 0.760784314, 0.788235294),
    'nitrogen' : (0.2, 0.2, 1.0),
    'nobelium' : (0.741176471, 0.050980392, 0.529411765),
    'olive' : (0.77, 0.7, 0.0),
    'orange' : (1.0, 0.5, 0.0),
    'osmium' : (0.149019608, 0.4, 0.588235294),
    'oxygen' : (1.0, 0.3, 0.3),
    'palecyan' : (0.8, 1.0, 1.0),
    'palegreen' : (0.65, 0.9, 0.65),
    'paleyellow' : (1.0, 1.0, 0.5),
    'palladium' : (0.0, 0.411764706, 0.521568627),
    'phosphorus' : (1.0, 0.501960784, 0.0),
    'pink' : (1.0, 0.65, 0.85),
    'platinum' : (0.815686275, 0.815686275, 0.878431373),
    'plutonium' : (0.0, 0.419607843, 1.0),
    'polonium' : (0.670588235, 0.360784314, 0.0),
    'potassium' : (0.560784314, 0.250980392, 0.831372549),
    'praseodymium' : (0.850980392, 1.0, 0.780392157),
    'promethium' : (0.639215686, 1.0, 0.780392157),
    'protactinium' : (0.0, 0.631372549, 1.0),
    'purple' : (0.75, 0.0, 0.75),
    'purpleblue' : (0.5, 0.0, 1.0),
    'radium' : (0.0, 0.490196078, 0.0),
    'radon' : (0.258823529, 0.509803922, 0.588235294),
    'raspberry' : (0.7, 0.3, 0.4),
    'red' : (1.0, 0.0, 0.0),
    'rhenium' : (0.149019608, 0.490196078, 0.670588235),
    'rhodium' : (0.039215686, 0.490196078, 0.549019608),
    'rubidium' : (0.439215686, 0.180392157, 0.690196078),
    'ruby' : (0.6, 0.2, 0.2),
    'ruthenium' : (0.141176471, 0.560784314, 0.560784314),
    'rutherfordium' : (0.8, 0.0, 0.349019608),
    'salmon' : (1.0, 0.6, 0.6),
    'samarium' : (0.560784314, 1.0, 0.780392157),
    'sand' : (0.72, 0.55, 0.3),
    'scandium' : (0.901960784, 0.901960784, 0.901960784),
    'seaborgium' : (0.850980392, 0.0, 0.270588235),
    'selenium' : (1.0, 0.631372549, 0.0),
    'silicon' : (0.941176471, 0.784313725, 0.62745098),
    'silver' : (0.752941176, 0.752941176, 0.752941176),
    'skyblue' : (0.2, 0.5, 0.0),
    'slate' : (0.5, 0.5, 1.0),
    'smudge' : (0.55, 0.7, 0.4),
    'sodium' : (0.670588235, 0.360784314, 0.949019608),
    'splitpea' : (0.52, 0.75, 0.0),
    'strontium' : (0.0, 1.0, 0.0),
    'sulfur' : (0.9, 0.775, 0.25),
    'tantalum' : (0.301960784, 0.650980392, 1.0),
    'teal' : (0.0, 0.75, 0.75),
    'technetium' : (0.231372549, 0.619607843, 0.619607843),
    'tellurium' : (0.831372549, 0.478431373, 0.0),
    'terbium' : (0.188235294, 1.0, 0.780392157),
    'thallium' : (0.650980392, 0.329411765, 0.301960784),
    'thorium' : (0.0, 0.729411765, 1.0),
    'thulium' : (0.0, 0.831372549, 0.321568627),
    'tin' : (0.4, 0.501960784, 0.501960784),
    'titanium' : (0.749019608, 0.760784314, 0.780392157),
    'tungsten' : (0.129411765, 0.580392157, 0.839215686),
    'tv_blue' : (0.3, 0.3, 1.0),
    'tv_green' : (0.2, 1.0, 0.2),
    'tv_orange' : (1.0, 0.55, 0.15),
    'tv_red' : (1.0, 0.2, 0.2),
    'tv_yellow' : (1.0, 1.0, 0.2),
    'uranium' : (0.0, 0.560784314, 1.0),
    'vanadium' : (0.650980392, 0.650980392, 0.670588235),
    'violet' : (1.0, 0.5, 1.0),
    'violetpurple' : (0.55, 0.25, 0.6),
    'warmpink' : (0.85, 0.2, 0.5),
    'wheat' : (0.99, 0.82, 0.65),
    'white' : (1.0, 1.0, 1.0),
    'xenon' : (0.258823529, 0.619607843, 0.690196078),
    'yellow' : (1.0, 1.0, 0.0),
    'yelloworange' : (1.0, 0.87, 0.37),
    'ytterbium' : (0.0, 0.749019608, 0.219607843),
    'yttrium' : (0.580392157, 1.0, 1.0),
    'zinc' : (0.490196078, 0.501960784, 0.690196078),
    'zirconium' : (0.580392157, 0.878431373, 0.878431373),
}

default_color_scheme = {
    'global' : {
        'background-color' : 'white'
    },
    'Scaffold'  : {
        'bb' : 'grey30',
        'hetatm' : 'grey60',
        'mutations' : 'grey80'
    },
    'RosettaModel'  : {
        'bb' : 'brightorange',
        'hetatm' : 'deepolive',
        'mutations' : 'yellow'
    },
    'ExpStructure'  : {
        'bb' : 'violetpurple',
        'hetatm' : 'warmpink',
        'mutations' : 'magenta'
    },
}


# todo: I now specify protein color and display options in PyMOLStructureBase objects. Rewrite this code so that default_color_scheme
#       specifies global options e.g. view options, background colors. This will probably be easier if the other PSE builders
#       are rewritten to match MultiStructureBuilder.


class PyMOLStructureBase(object):

    '''A simple structure-less class to store parameters used to display a structure. Open to heavy modification as we add more
       customization.'''


    def __init__(self, backbone_color = 'white', backbone_display = 'cartoon',
                       sidechain_color = 'grey80', sidechain_display = 'sticks',
                       hetatm_color = 'grey60', hetatm_display = 'sticks',
                       visible = True):
        self.backbone_color = backbone_color or 'white'
        self.backbone_display = backbone_display or 'cartoon'
        self.sidechain_color = sidechain_color or 'grey80'
        self.sidechain_display = sidechain_display or 'sticks'
        self.hetatm_color = hetatm_color or  'grey60'
        self.hetatm_display = hetatm_display or 'sticks'
        self.visible = visible


class PyMOLStructure(PyMOLStructureBase):

    '''A simple structure-containing class to store parameters used to display a structure. Open to heavy modification as we add more
       customization.'''


    def __init__(self, pdb_object, structure_name, residues_of_interest = [], label_all_residues_of_interest = False, **kwargs):
        '''The chain_seed_color kwarg can be either:
               - a triple of R,G,B values e.g. [0.5, 1.0, 0.75] where each value is between 0.0 and 1.0;
               - a hex string #RRGGBB e.g. #77ffaa;
               - a name defined in the predefined dict above e.g. "aquamarine".
        '''
        self.pdb_object = pdb_object
        self.structure_name = structure_name
        self.add_residues_of_interest(residues_of_interest)
        self.label_all_residues_of_interest = label_all_residues_of_interest
        self.chain_colors = kwargs.get('chain_colors') or {}

        # Set up per-chain colors
        try:
            if not self.chain_colors and kwargs.get('chain_seed_color'):
                chain_seed_color = kwargs.get('chain_seed_color')
                if isinstance(chain_seed_color, str) or isinstance(chain_seed_color, unicode):
                    chain_seed_color = str(chain_seed_color)
                    if chain_seed_color.startswith('#'):
                        if len(chain_seed_color) != 7:
                            chain_seed_color = None
                    else:
                        trpl = predefined.get(chain_seed_color)
                        chain_seed_color = None
                        if trpl:
                            chain_seed_color = mpl_colors.rgb2hex(trpl)
                elif isinstance(chain_seed_color, list) and len(chain_seed_color) == 3:
                    chain_seed_color = mpl_colors.rgb2hex(chain_seed_color)

                if chain_seed_color.startswith('#') and len(chain_seed_color) == 7:

                    # todo: We are moving between color spaces multiple times so are probably introducing artifacts due to rounding. Rewrite this to minimize this movement.
                    chain_seed_color = chain_seed_color[1:]

                    hsl_color = colorsys.rgb_to_hls(int(chain_seed_color[0:2], 16)/255.0, int(chain_seed_color[2:4], 16)/255.0, int(chain_seed_color[4:6], 16)/255.0)
                    chain_seed_hue = int(360.0 * hsl_color[0])
                    chain_seed_saturation = max(0.15, hsl_color[1]) # otherwise some colors e.g. near-black will not yield any alternate colors
                    chain_seed_lightness = max(0.15, hsl_color[2]) # otherwise some colors e.g. near-black will not yield any alternate colors

                    min_colors_in_wheel = 4 # choose at least 4 colors - this usually results in a wider variety of colors and prevents clashes e.g. given 2 chains in both mut and wt, wt seeded with blue, and mut seeded with yellow, we will get a clash
                    chain_ids = sorted(pdb_object.atom_sequences.keys())

                    # Choose complementary colors, respecting the original saturation and lightness values
                    chain_colors = ggplot_color_wheel(max(len(chain_ids), min_colors_in_wheel), start = chain_seed_hue, saturation_adjustment = None, saturation = chain_seed_saturation, lightness = chain_seed_lightness)
                    assert(len(chain_colors) >= len(chain_ids))
                    self.chain_colors = {}
                    for i in xrange(len(chain_ids)):
                        self.chain_colors[chain_ids[i]] = str(list(mpl_colors.hex2color('#' + chain_colors[i])))

                    # Force use of the original seed as this may have been altered above in the "= max(" statements
                    self.chain_colors[chain_ids[0]] = str(list(mpl_colors.hex2color('#' + chain_seed_color)))

        except Exception, e:
            print('An exception occurred setting the chain colors. Ignoring exception and resuming with default colors.')
            print(str(e))
            print(traceback.format_exc())

        super(PyMOLStructure, self).__init__(
                 backbone_color = kwargs.get('backbone_color'), backbone_display = kwargs.get('backbone_display'),
                 sidechain_color = kwargs.get('sidechain_color'), sidechain_display = kwargs.get('sidechain_display'),
                 hetatm_color = kwargs.get('hetatm_color'), hetatm_display = kwargs.get('hetatm_display'),
                 visible = kwargs.get('visible', True),
                 )



    def add_residues_of_interest(self, residues_of_interest):
        # todo: we should check the residue IDs against the PDB object to make sure that the coordinates exist
        # For now, do a simple assignment
        if residues_of_interest:
            self.residues_of_interest = residues_of_interest


default_display_scheme = dict(
    GenericProtein = PyMOLStructureBase(),
)


def create_new_color_command(color_name, r, g, b):
    return 'set_color %(color_name)s, [%(r).10f,%(g).10f,%(b).10f]' % vars()


class ColorScheme(object):
    '''A dict wrapper class. The dict that is stored is intended to have a tree structure. The paths of the tree describe
       how the color should be used e.g. RosettaModel.bb should be used to color the backbone of a Rosetta model. The leaves of the
       tree are colors. If a new color is needed, use the create_new_color_command function to define the new color in
       the script before use.'''

    def __init__(self, custom_color_scheme = {}):
        '''If a color_scheme is passed in then this is merged with the default color scheme.'''
        color_scheme = {}
        color_scheme.update(default_color_scheme)
        display_scheme = {}
        display_scheme.update(default_display_scheme)
        if custom_color_scheme:
            assert(type(custom_color_scheme) == type(predefined))
            color_scheme.update(custom_color_scheme)
        self.color_scheme = color_scheme
        self.name = 'Default'

    def update(self, path, node):
        '''Update the dict with a new color using a 'path' through the dict. You can either pass an existing path e.g.
           'Scaffold.mutations' to override a color or part of the hierarchy or you can add a new leaf node or dict.'''
        assert(type(path) == type(self.name))
        assert(type(node) == type(self.name) or type(node) == type(predefined))

        d = self.color_scheme
        tokens = path.split('.')
        for t in tokens[:-1]:
            d = d.get(t)
            if d == None:
                raise Exception("Path '%s' not found.")
        d[tokens[-1]] = node

    def lookup(self, path, must_be_leaf = False):
        '''Looks up a part of the color scheme. If used for looking up colors, must_be_leaf should be True.'''
        assert(type(path) == type(self.name))

        d = self.color_scheme
        tokens = path.split('.')
        for t in tokens[:-1]:
            d = d.get(t)
            if d == None:
                raise Exception("Path '%s' not found.")
        if must_be_leaf:
            assert(type(d[tokens[-1]]) == type(self.name))
        return d[tokens[-1]]

    def __repr__(self):
        return str(self.color_scheme)

    def __getitem__(self, path):
        '''This lets us use the object somewhat like a dict where we do a lookup using a path e.g. cs['Scaffold.mutations']
           This also lets us use the object in a string formatting e.g. print('%(Scaffold.mutations)s' % cs) which is useful
           for the PyMOL script generators.'''
        return self.lookup(path)


if __name__ == '__main__':
    cs = ColorScheme()
    cs.update('ExpStructure.b', 'thallium')
    cs.update('ExpStructure.mutations', 'thallium')
    print('')
    print(cs.lookup('ExpStructure.b', must_be_leaf = True))
    print(cs['Scaffold.mutations'])
    print('Testing string formatting: Scaffold.mutations = %(Scaffold.mutations)s, RosettaModel.hetatm = %(RosettaModel.hetatm)s.' % cs)
    print(cs['global.background-color'])
    print('')

    cs = ColorScheme({'global' : {'background-color' : 'black'}})
    print(cs)
    print(cs['global.background-color'])
    print('')
