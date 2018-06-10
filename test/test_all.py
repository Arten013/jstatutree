import os
import subprocess

testdir = os.path.dirname(os.path.abspath(__file__))
for file in os.listdir(testdir):
    if "_test.py" in file:
        print(os.path.join(testdir, file))
        subprocess.call("python -m unittest -v {}".format(os.path.join(testdir, file)), shell=True)
