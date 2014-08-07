import glob
import os

with open('doctests.py','w') as doctests:
    for root,dirs,files in os.walk('.'):
        for fn in files:
            if os.path.splitext(fn)[1] == '.rst':
                print os.path.join(root, fn)
                with open(os.path.join(root, fn),'r') as f:
                    lines = f.readlines()

                pylines = [L.lstrip().lstrip(">").lstrip()
                           for L in lines if '>>>' in L]
                doctests.write("# {fn}\n".format(fn=fn))
                doctests.writelines(pylines)
