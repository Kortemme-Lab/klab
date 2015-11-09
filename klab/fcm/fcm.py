#!/usr/bin/python

blank_datafile = '/home/kyleb/Dropbox/UCSF/cas9/FCS/150916-3.1/kyleb/150916-rfp-cas9/96 Well - Flat bottom_002/Specimen_001_F1_F01_046.fcs'
script_output_dir = 'script_output'
sample_directory = '/home/kyleb/Dropbox/UCSF/cas9/FCS/150916-3.1/kyleb/150916-rfp-cas9/96 Well - Flat bottom_002'

rows_in_plate = 'ABCDEFGH'
cols_in_plate = range(1, 13)

from FlowCytometryTools import FCMeasurement, ThresholdGate
from FlowCytometryTools.core.gates import CompositeGate
import os, FlowCytometryTools
import pylab as P
import numpy as np
import scipy

class PlatePos:
    def __init__ (self, plate_position_str):
        self.row = plate_position_str[0]
        assert( self.row in rows_in_plate )
        self.col = int(plate_position_str[1:])

    # Returns the next position on the plate
    @property
    def next_pos(self):
        if self.row_index == len(rows_in_plate)-1:
            if self.col == cols_in_plate[-1]:
                return None

        if self.col == cols_in_plate[-1]:
            next_pos_row = rows_in_plate[ self.row_index+1 ]
            next_pos_col = 1
        else:
            next_pos_row = self.row
            next_pos_col = self.col + 1

        return PlatePos( '%s%d' % (next_pos_row, next_pos_col) )

    @property
    def row_index(self):
        return rows_in_plate.index(self.row)

    def __repr__(self):
        return '%s%02d' % (self.row, self.col)

    def __lt__ (self, other):
        if self.row == other.row:
            return self.col < other.col
        else:
            return self.row < other.row

    def __hash__(self):
        return hash( str(self) )

    def __eq__(self, other):
        return self.row == other.row and self.col == other.col

    def __ne__(self, other):
        return not self.__eq__(other)

class PlateInfo:
    def __init__ (self, name, value, new_positions):
        self.name = name

        if value == None:
            self.value = np.nan
        else:
            self.value = value

        self.positions = []

        if isinstance(new_positions, list):
            for new_position_range in new_positions:
                self.add_position_range(new_position_range)
        elif isinstance(new_positions, basestring):
            self.add_position_range(new_positions)
        else:
            raise Exception('Input new positions must be a list or string')

    def add_position_range(self, pos_range):
        if '-' in pos_range:
            first_pos_str, second_pos_str = pos_range.split('-')
            first_pos = PlatePos(first_pos_str)
            second_pos = PlatePos(second_pos_str)
            first_pos_char_index = rows_in_plate.index(first_pos.row)
            second_pos_char_index = rows_in_plate.index(second_pos.row)
            for char_index in xrange(first_pos_char_index, second_pos_char_index + 1):
                row = rows_in_plate[char_index]
                for col in xrange(first_pos.col, second_pos.col + 1):
                    self.add_position( '%s%d' % (row, col) )
        else:
            self.add_position(pos_range)

    def add_position(self, pos_str):
        pos = PlatePos(pos_str)
        if pos not in self.positions:
            self.positions.append(pos)
            self.positions.sort()

    @property
    def position_set(self):
        return_set = set()
        for pos in self.positions:
            return_set.add(pos)
        return return_set

    def __repr__(self):
        return str( self.positions )

class Plate:
    def __init__ (self, plate_info_list, sample_dir=None, verbose=False, name=None):
        self.name = name
        self.info_dict = {}
        self.samples = {}
        self.sample_dir = sample_dir
        for plate_info in plate_info_list:
            if plate_info.name not in self.info_dict:
                self.info_dict[plate_info.name] = {}
            assert( plate_info.value not in self.info_dict[plate_info.name] )
            self.info_dict[plate_info.name][plate_info.value] = plate_info
        if sample_dir != None:
            self.load_fcs_dir(sample_dir, verbose=verbose)

    def __repr__(self):
        return str(self.info_dict)

    @property
    def all_position_set(self):
        s = set()
        for name in self.info_dict:
            for value in self.info_dict[name]:
                s = s.union(self.info_dict[name][value].position_set)
        return s

    def get_by_well(self, well_pos):
        search_pos = PlatePos(well_pos)
        for pos in self.all_position_set:
            if pos == search_pos:
                return self.samples[pos]

    def parameter_values(self, parameter_name):
        return sorted( self.info_dict[parameter_name].keys() )

    def well_set(self, parameter_name, parameter_value=np.nan):
        if parameter_name not in self.info_dict or parameter_value not in self.info_dict[parameter_name]:
            return set()
        else:
            return self.info_dict[parameter_name][parameter_value].position_set

    @property
    def experimental_parameters(self):
        experimental_parameters = []
        for parameter_name in self.info_dict.keys():
            if 'blank' not in parameter_name.lower():
                if len(self.info_dict[parameter_name]) == 1 and np.nan in self.info_dict[parameter_name]:
                    experimental_parameters.append(parameter_name)
        return experimental_parameters

    def gate(self, gate):
        for pos in self.samples:
            self.samples[pos] = self.samples[pos].gate(gate)

    def load_fcs_dir(self, sample_directory, verbose=False):
        fcs_files = find_fcs_files(sample_directory)
        for plate_pos, filepath in fcs_files:
            assert(plate_pos not in self.samples)
            self.samples[plate_pos] = FCMeasurement(ID=str(plate_pos), datafile=filepath)
        if verbose:
            print 'Loaded %d FCS files from directory %s' % (len(fcs_files), sample_directory)

class FCSFile:
    def __init__ (self, filepath, plate_position_str):
        self.filepath = filepath
        self.plate_position_obj = PlatePos(plate_position_str)

    @property
    def plate_position(self):
        return str( self.plate_position_obj )

    @property
    def plate_row(self):
        return self.plate_position_obj.row

    @property
    def plate_col(self):
        return self.plate_position_obj.col

    def __lt__ (self, other):
        return self.plate_position < other.plate_position

    def __repr__(self):
        return self.plate_position

def find_fcs_files(sample_directory):
    fcs_files = []
    for filename in os.listdir(sample_directory):
        if filename.endswith('.fcs'):
            full_filename = os.path.join(sample_directory, filename)
            fcs_files.append( (PlatePos(filename.split('_')[2]), full_filename) )
    fcs_files.sort()
    return fcs_files

def ticks_format(value, index):
    """
    get the value and returns the value as:
       integer: [0,99]
       1 digit float: [0.1, 0.99]
       n*10^m: otherwise
    To have all the number of the same size they are all returned as latex strings

    http://stackoverflow.com/questions/17165435/matplotlib-show-labels-for-minor-ticks-also
    """
    exp = np.floor(np.log10(value))
    base = value/10**exp
    if exp == 0 or exp == 1:
        return '${0:d}$'.format(int(value))
    if exp == -1:
        return '${0:.1f}$'.format(value)
    else:
        return '${0:d}\\times10^{{{1:d}}}$'.format(int(base), int(exp))

def output_medians_and_sums():
    fsc_gate = ThresholdGate(10000.0, 'FSC-A', region='above')
    ssc_gate = ThresholdGate(9000.0, 'SSC-A', region='above')
    fsc_ssc_gate = CompositeGate(fsc_gate, 'and', ssc_gate)

    # Load blank data
    blank_sample = FCMeasurement(ID='blank', datafile=blank_datafile).gate(fsc_gate)

    fcs_files = find_fcs_files(sample_directory)

    channel_medians = {channel_name : {} for channel_name in blank_sample.channel_names}
    channel_sums = {channel_name : {} for channel_name in blank_sample.channel_names}
    for plate_pos, filepath in fcs_files:
        sample = FCMeasurement(ID='sample', datafile=filepath).gate(fsc_gate)
        for channel_name in sample.channel_names:
            if plate_pos.row not in channel_medians[channel_name]:
                channel_medians[channel_name][plate_pos.row] = {}
                channel_sums[channel_name][plate_pos.row] = {}
            assert( plate_pos.col not in channel_medians[channel_name][plate_pos.row] )
            channel_medians[channel_name][plate_pos.row][plate_pos.col] =  sample.data[channel_name].median()
            channel_sums[channel_name][plate_pos.row][plate_pos.col] =  np.sum(sample.data[channel_name])
        #     if channel_name in ['B-A', 'A-A']:
        #         print filename, channel_name
        #         sample.plot(channel_name, bins=100, alpha=0.9, color='green');
        #         blank_sample.plot(channel_name, bins=100, alpha=0.9, color='blue');
        #         P.grid(True)
        #         P.show() # <-- Uncomment when running as a script.

    if not os.path.isdir(script_output_dir):
        os.makedirs(script_output_dir)

    rows = [char for char in 'ABCDEFGH']
    cols = range(1, 13)
    for channel, data_type in [(channel_medians, 'medians'), (channel_sums, 'sums')]:
        for channel_name in channel:
            filename = os.path.join(script_output_dir, '%s_%s.csv' % (channel_name, data_type))
            with open(filename, 'w') as f:
                for col in cols:
                    for row in rows:
                        if row in channel[channel_name] and col in channel[channel_name][row]:
                            f.write('%.2f,' % channel[channel_name][row][col])
                        else:
                            f.write('NA,')
                    f.write('\n')

def points_above_line(x_data, y_data, m, b):
    # Calculate y-intercepts for all points given slope m
    comp_bs = np.subtract(y_data, np.multiply(x_data, m))
    # Return number of points whose y intercept is above passed in b
    return np.count_nonzero(comp_bs > b)

def find_perpendicular_gating_line(x_data, y_data, threshold):
    # Returns the line parameters which give you a certain percentage (threshold) of population
    # above the line
    x_data = np.sort( x_data  )
    y_data = np.sort( y_data  )
    x_max = np.amax(x_data)
    y_max = np.amax(y_data)
    # y = mx + b
    m, b, r, p, stderr = scipy.stats.linregress(x_data, y_data)
    inv_m = -1.0 / m
    inv_b = y_max
    percent_above_line = points_above_line(x_data, y_data, inv_m, inv_b) / float(len(x_data))
    desired_points_above_line = int(threshold * len(x_data))
    def obj_helper(calc_b):
        return abs(points_above_line(x_data, y_data, inv_m, calc_b) - desired_points_above_line)
    res = scipy.optimize.minimize(obj_helper, inv_b, method='nelder-mead', options={'disp': False, 'maxiter': 1000})
    inv_b = res.x[0]
    return (inv_m, inv_b)

def mean_confidence_interval(data, confidence=0.95):
    a = 1.0*np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t._ppf((1+confidence)/2., n-1)
    return m, m-h, m+h

if __name__ == '__main__':
    output_medians_and_sums()
