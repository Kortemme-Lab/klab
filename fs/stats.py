import subprocess

df_conversions = {
    'MB': float(2 ** 10),
    'GB': float(2 ** 20),
    'TB': float(2 ** 30),
}

def df(unit = 'GB'):
    '''A wrapper for the df shell command.'''
    details = {}
    headers = ['Filesystem', 'Size', 'Used', 'Available', 'Use%', 'MountedOn']
    n = len(headers)

    unit = df_conversions[unit]
    p = subprocess.Popen(args = ['df'], stdout = subprocess.PIPE)
    stdout, stderr = p.communicate()

    lines = stdout.split("\n")
    lines[0] = lines[0].replace("Mounted on", "MountedOn").replace("1K-blocks", "Size")
    assert(lines[0].split() == headers)

    lines = [l.strip() for l in lines if l.strip()]
    for line in lines[1:]:
        tokens = line.split()
        if tokens[0] == 'none': # skip uninteresting entries
            continue
        assert(len(tokens) == n)
        d = {}
        for x in range(1, len(headers)):
            d[headers[x]] = tokens[x]
        d['Size'] = float(d['Size']) / unit
        d['Used'] = float(d['Used']) / unit
        details[tokens[0]] = d
    return details
