import sys
import shlex
import platform
from time import strftime
import traceback
import socket

if __name__ == '__main__':
    sys.path.insert(0, '/netapp/home/klabqb3backrub/pythonlibs/')

from klab.process import Popen_raw


def make_simple_xml_open_tag(tagname, attributes = {}):
    attstring = ""
    if attributes:
        attstring = " "
        for k, v in sorted(attributes.iteritems()):
            attstring += '%s="%s" ' % (k, v)        
    return '<%s%s>' % (tagname, attstring.rstrip())

def make_simple_xml_tag(tagname, content, attributes = {}):
    return '%s\n%s\n</%s>' % (make_simple_xml_open_tag(tagname, attributes), content, tagname)

def get_prejob_xml(job_id = None, task_id = None):
    s = []
    if job_id != None:
        s.append(make_simple_xml_tag('job_id', str(job_id)))
    if task_id != None:
        s.append(make_simple_xml_tag('task_id', str(task_id)))
    s.append(make_simple_xml_tag('job_start_time', strftime("%%Y-%%m-%%d %%H:%%M:%%S")))
    s.append(make_simple_xml_tag('host', socket.gethostname()))
    s.append(make_simple_xml_tag('arch', platform.machine() + ', ' + platform.processor() + ', ' + platform.platform()))
    return '\n'.join(s)

def get_postjob_xml(job_id = None, task_id = None):
    s = []
    s.append(make_simple_xml_tag('job_end_time', strftime("%%Y-%%m-%%d %%H:%%M:%%S")))
    if job_id != None and task_id != None:
        p = None
        try:
            # todo: handle the case with one task i.e. job_id is specified but task_id is None
            p = Popen_raw('qstat -j ' + str(job_id) + ' | grep -E "usage +' + str(task_id) + '" | sed "s/.*maxvmem=//"')
            mem_usage = p.stdout()
            s.append(make_simple_xml_tag('maxvmem', mem_usage))
        except Exception, e:
            if p:
                s.append(make_simple_xml_tag('error', '<![CDATA[\n' + p.stderr + ']]'))
            else:
                s.append(make_simple_xml_tag('error', 'An error occurred in the qstat call to gather memory usage.\n<![CDATA[\n%s\n%s]]' % (str(e), traceback.format_exc())))
    
    return '\n'.join(s)

if __name__ == '__main__':
    # test code
    print(get_prejob_xml(30892451, 4))
    print(make_simple_xml_tag('test', 'contents', {'mood' : 'happy'}))
    print(get_postjob_xml(30892451, 4))

