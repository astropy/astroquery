import urllib.request

class EhstHandler(object):
    
    def __init__(self):
        return
    
    def get_file(self, url, filename, verbose=False):
        urllib.request.urlretrieve(url, filename)
        return

Handler = EhstHandler()

__all__ = ['EhstHandler', 'Handler']
