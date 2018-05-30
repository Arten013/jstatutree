import unittest
import sys, os
sys.path.append(
    os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    )
import xml_jstatutree as jstatutree
import xml_etype_class as etype
from myexceptions import LawError


files = []
for r, d, f in os.walk(PATH):
    files += f
files = list(set(files))
def find_all_files(directory, extentions=None):
    for root, dirs, files in os.walk(directory):
        if extentions is None or os.path.splitext(root)[1] in extentions:
            yield root
        for file in files:
            if extentions is None or os.path.splitext(file)[1] in extentions:
                yield os.path.join(root, file)

for path in find_all_files(PATH):
    path = os.path.join(PATH, path)
    print(path)
    rr = jstatutree.ReikiXMLReader(path)
    rr.open()
    tree = rr.get_tree()
    try:
        for child in tree.depth_first_iteration():
            print(child)
    except LawError as e:
        print(e)

