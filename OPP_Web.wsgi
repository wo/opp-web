import sys
from os.path import abspath, dirname, join
import logging

root = abspath(dirname(__file__))

# activate python environment:
activate_this = join(root, 'venv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

# add opp-web to python path:
sys.path.insert(0, root)

# logging:
logging.basicConfig(filename='error.log',level=logging.DEBUG)

# start application:
from OPP_Web import app as application
