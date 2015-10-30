white, black = '#ffffff', '#000000'
grey = '#eeeeec', '#d3d7cf', '#babdb6', '#888a85', '#555753', '#2e3436'

red =    '#ef2929', '#cc0000', '#a40000'
orange = '#fcaf3e', '#f57900', '#ce5c00'
yellow = '#fce94f', '#edd400', '#c4a000'
green =  '#8ae234', '#73d216', '#4e9a06'
blue =   '#729fcf', '#3465a4', '#204a87'
purple = '#ad7fa8', '#75507b', '#5c3566'
brown =  '#e9b96e', '#c17d11', '#8f5902'

def color_from_cycle(index):
    cycle = (blue[1], red[1], green[2], orange[1], purple[1], brown[1],
             blue[0], red[0], green[1], orange[0], purple[0], brown[0])
    return cycle[index % len(cycle)]
