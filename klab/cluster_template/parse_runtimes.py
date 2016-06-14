import sys
import os
from datetime import datetime

starting_time_str = 'Starting time: '
ending_time_str = 'Ending time: '
dt_format = '%Y-%m-%d %H:%M:%S'

def ts(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6) / 1e6

def main():
    output_dir = sys.argv[1]
    assert( os.path.isdir(output_dir) )

    app_runtimes = {}
    last_starting_time = None
    last_app = None
    for dir_item in os.listdir(output_dir):
        output_file_path = os.path.join(output_dir, dir_item)
        if '.o' in dir_item and os.path.isfile(output_file_path):
            with open(output_file_path, 'r') as f:
                for line in f:
                    if line.startswith(starting_time_str):
                        if last_starting_time == None:
                            try:
                                last_starting_time = datetime.strptime(line[len(starting_time_str):].strip(), dt_format)
                            except ValueError:
                                last_starting_time = None
                    elif line.startswith('[') and 'source/bin' in line:
                        if last_starting_time != None:
                            last_app = line[line.find('/'):line.find("'", line.find('/'))]
                    elif line.startswith(ending_time_str):
                        if last_app != None and last_starting_time != None:
                            try:
                                ending_time = datetime.strptime(line[len(ending_time_str):].strip(), dt_format)
                            except ValueError:
                                last_starting_time = None
                                last_app = None
                                continue

                            if last_app not in app_runtimes:
                                app_runtimes[last_app] = []
                            app_runtimes[last_app].append( ending_time - last_starting_time )
                        last_starting_time = None
                        last_app = None
    mean_runtimes = []
    for app in app_runtimes:
        mean_runtimes.append( (
            float(sum([ts(td) for td in app_runtimes[app]])) / float(len(app_runtimes[app]))
            , len(app_runtimes[app]), app) )
    mean_runtimes.sort()

    for seconds, n, app in mean_runtimes:
        print '%s: %.1f minutes (n=%d)' % (app, seconds/60.0, n)

    app_types = {}
    for app in app_runtimes:
        app_type = app.split('/')[-1].split('.')[0]
        if app_type not in app_types:
            app_types[app_type] = []
        app_types[app_type].append(app)

    print

    for app_type in app_types:
        apps = sorted( app_types[app_type] )
        app_type_mean_runtimes = []
        for seconds, n, app in mean_runtimes:
            if app in apps:
                app_type_mean_runtimes.append( (seconds, n, app) )
        app_type_mean_runtimes.sort()
        print app_type
        for seconds, n, app in app_type_mean_runtimes:
            print '%s: %.2f x, %.2f minutes (n=%d)' % (app, seconds/app_type_mean_runtimes[0][0], seconds/60.0, n)
        print

if __name__ == '__main__':
    main()
