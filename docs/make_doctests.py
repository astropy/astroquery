import glob
import os
import re

leftarrows = re.compile("^ *>>> ")
leftdots = re.compile("^ *\.\.\. ")
docskip = re.compile('doctest: \+SKIP')

def test_line(line):
    if docskip.search(line):
        return False
    elif leftarrows.search(line):
        return True
    elif leftdots.search(line):
        if line.count('...') == 1:
            return True

def strip_line(line):
    return leftdots.sub("",leftarrows.sub("",L))

with open('doctests.py','w') as doctests:
    for root,dirs,files in os.walk('.'):
        for fn in files:
            if os.path.splitext(fn)[1] == '.rst':
                with open(os.path.join(root, fn),'r') as f:
                    lines = f.readlines()

                pylines = [strip_line(L)
                           for L in lines if test_line(L)]
                doctests.write("# {fn}\n".format(fn=fn))
                doctests.writelines(pylines)
