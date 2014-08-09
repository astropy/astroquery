def stringy(x):
    if hasattr(x, 'decode'):
        return x.decode()
    else:
        return x
