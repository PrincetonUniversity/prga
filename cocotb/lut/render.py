import os
from os import path
from jinja2 import Environment, FileSystemLoader

file_loader = FileSystemLoader('templates')
env = Environment(loader = file_loader)

makefile_template  = env.get_template('Makefile.tmpl')
test_template  = env.get_template('test.tmpl.py')

module = {"name":"lut4","test_name":"test","n_input":4}

if not path.exists('cocotb_test'):
    os.mkdir('cocotb_test')

with open('cocotb_test/Makefile', 'w') as f:
    makefile = makefile_template.render(module = module)
    f.write(makefile)

with open('cocotb_test/'+module['test_name']+'.py', 'w') as f:
    test = test_template.render(module = module)
    f.write(test)

