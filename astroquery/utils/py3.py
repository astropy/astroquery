from astropy import log

def stringy(x):
    if hasattr(x, 'decode'):
        try:
            return x.decode()
        except UnicodeDecodeError:
            log.warn("Encountered a unicode decoding error.")
            return x
        except UnicodeEncodeError:
            log.warn("Encountered a unicode encoding error.")
            return x
    else:
        return x

def bitey(x):
    if hasattr(x, 'encode'):
        try:
            return x.encode()
        except UnicodeDecodeError:
            log.warn("Encountered a unicode decoding error.")
            return x
        except UnicodeEncodeError:
            log.warn("Encountered a unicode encoding error.")
            return x
    else:
        return x
