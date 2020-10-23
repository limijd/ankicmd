#!/usr/bin/env python3

#Create this script is because when ANKI update it's version. Default pypi ANKI library will have problem to support
#the latest ANKI database. 

#So I am building the new checked out ANKI library at ~/install/anki
#To run the script with latest ANKI, the python need to be the one in  ~/install/anki/pyenv/bin/python

import os
import sys

import subprocess

SCRIPT_PATH=os.path.dirname(os.path.realpath(__file__))
subprocess.call([os.path.expanduser("~/install/anki/pyenv/bin/python"), "%s/akcmd.py"%SCRIPT_PATH] + sys.argv[1:])
