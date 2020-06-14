import os
from os import path
from jinja2 import Environment, FileSystemLoader
import pickle
file_loader = FileSystemLoader('templates')
env = Environment(loader = file_loader)

makefile_template  = env.get_template('Makefile.tmpl')
config_template  = env.get_template('config.py')

module = {"name":"fle6","test_name":"test","n_input":6}


if not path.exists('cocotb_test'):
    os.mkdir('cocotb_test')

with open('cocotb_test/Makefile', 'w') as f:
    makefile = makefile_template.render(module = module)
    f.write(makefile)

with open('cocotb_test/config.py', 'w') as f:
    config = config_template.render(module = module)
    f.write(config)

outfile = open('cocotb_test/test.pckl','wb')
pickle.dump(module,outfile)
outfile.close()