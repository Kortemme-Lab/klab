import hashlib
from klab.general.strutil import remove_trailing_line_whitespace

def get_hexdigest(content, rm_trailing_line_whitespace = False):
    if rm_trailing_line_whitespace:
        content = remove_trailing_line_whitespace(content)
    md5hash = hashlib.md5()
    md5hash.update(content)
    hexdigest = md5hash.hexdigest()
    assert(len(hexdigest) == 32)
    return hexdigest
