import traceback

def stacktrace(line_separator = '\n'):
    s = []
    for line in traceback.format_stack():
        s.append(line.strip())
    return line_separator.join(s)
