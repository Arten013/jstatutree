import os
import subprocess

for file in os.listdir(os.path.dirname(os.path.abspath(__file__))):
    if "_test.py" in file:
        subprocess.call("python -m unittest -v {}".format(file), shell=True)
