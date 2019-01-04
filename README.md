# **P**rinceton **R**econfigurable **G**ate **A**rray

It's reconfigurable outside Princeton, too!

## Prerequisites

PRGA depends on the following libraries, tools, and Python modules:

### Libraries
- [Boost Graph
  Library](https://www.boost.org/doc/libs/1_69_0/libs/graph/doc/index.html)
- [Expat](https://libexpat.github.io/)

### Tools
- [Google Proto Buffer](https://developers.google.com/protocol-buffers/)
- [Yosys](http://www.clifford.at/yosys/)
- [Verilog-to-Routing](https://verilogtorouting.org/)
- [Icarus Verilog](http://iverilog.icarus.com/)

### Python modules
- [networkx](https://networkx.github.io/)
- [jinja2](http://jinja.pocoo.org/docs/2.10/)
- [mmh3](https://pypi.org/project/mmh3/)
- [lxml](https://lxml.de/)

### Optional
- [Sphinx](http://www.sphinx-doc.org/en/master/examples.html) for building the
  docs

## Installation

Note that PRGA contains sub-modules. Run the following commands after cloning
this project to download the sub-modules:

```bash
git submodule init
git submodule update
```

Some part of the PRGA needs compilation. Run the following commands:

```bash
cd /path/to/prga                        # cd to the root folder of PRGA
source envscr/settings.vm.sh            # set up environment
mkdir build && cd build                 # that's where we will build everything
cmake3 ..                               # run CMake
make                                    # run Make
```

## How to run example?

Examples are provided in the `examples/` directory. Follow the commands below to
run an example:

```bash
cd /path/to/prga                        # cd to the root folder of PRGA
source envscr/settings.vm.sh            # set up environment
cd examples/small/build                 # cd to one of the example directories
make                                    # this will run all the way to post-implementation simulation
```

Each example is organized in the following hierarchy:
* `src/`:
    * `build.py`: the Python script for building the FPGA
    * `{example}.v`: the target design
    * `{example}.tb.v`: the testbench for the target design
    * `{example}.impl.v`: the wrapper for the target design implemented on the FPGA
    * `synth.ys`: the Yosys script for synthesizing the target design
    * `fix_io.py`: a temporary Python script for fixing VPR's packing result
* `build/`:
    * `Makefile`: the Make script

## Coding Styles
1. Use explicit `import`s to make searching for source code easier.
2. You will never have too many classes. Use different classes when there are
   different needs instead of sharing classes and add checking/validation logic.
3. Following Python's coding style (to be in practice in later commits):
    - Use CamelCase naming conventions for classes
    - Use underscore naming conventions instead of CamelCase for methods
    - Methods starting with *capitalized letter* are `staticmethod` or `classmethod` API
    - Methods starting with *lower-case letter* are API
    - Methods starting with *one underscore* are internal methods
    - Methods starting with *two underscores* are class-private methods
