from httplib import HTTPConnection

def get(url):
    url = url.strip()
    if url[:7].lower()==("http://"):
        url = url[7:]
    idx = url.find('/')

    root = url[:idx]
    resource = url[idx:]
    c = HTTPConnection(root )
    c.request("GET", resource)
    response = c.getresponse()
    contents = response.read()
    c.close()
    return contents