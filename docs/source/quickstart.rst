Quickstart
==========

Prerequisites
-------------

RTL Simulator
^^^^^^^^^^^^^

PRGA currently provides scripts to use `Icarus Verilog`_ (open-source) or
`Synopsys VCS`_ (commercial) for RTL simulation.
However, the FPGA CAD flow does not depend on any simulator, so you may use any
simulator of your choice.
`Synopsys VCS`_ or other commercial simulators are recommended, because `Icarus
Verilog`_ couldn't handle large designs.

.. _Synopsys VCS: https://www.synopsys.com/verification/simulation/vcs.html
.. _Icarus Verilog: http://iverilog.icarus.com

Install with Automated Installation Script
------------------------------------------

PRGA provides a push-button installation Bash script, `envscr/install`_, which
installs the following tools locally, without the requirement of root access:

* `Python 3.8+`_: PRGA uses `pyenv`_, `pipenv`_ and `venv`_ to manage the Python
  binaries, packages and virtual environments. This minimizes the impact and
  possible conflicts with system-default Python binaries/packages.
* `Yosys`_: Open-source synthesis tool. This tool is included in PRGA as a
  submodule, and is automatically installed with the `envscr/install`_ script.
* `VPR`_: Open-source FPGA place-and-route tool. This tool is included in PRGA as
  a submodule, and is automatically installed with the `envscr/install`_ script.

To run this automated installation script:

.. code-block:: bash

    cd /path/to/prga
    ./envscr/install

If there's any error when installing `Yosys`_ or `VPR`_, please refer to their
installation guides and address any missing packages, libraries, or compiler
requirements.
For example, `VPR`_ requires `CMake 3.0+`_, and `Yosys`_ required ``tcl-dev``.

.. _envscr/install: https://github.com/PrincetonUniversity/prga/blob/release/envscr/install
.. _Python 3.8+: https://www.python.org/
.. _pyenv: https://github.com/pyenv/pyenv
.. _pipenv: https://pypi.org/project/pipenv/
.. _venv: https://docs.python.org/3/tutorial/venv.html
.. _Yosys: http://www.clifford.at/yosys
.. _VPR: https://verilogtorouting.org/
.. _CMake 3.0+: https://cmake.org/

Run a Quick Test
----------------

Once `envscr/install`_ finishes, you may source `envscr/activate`_ to activate the
Python virtual environment.
Run any command as if you are using a normal bash terminal.
Use ``deactivate`` to exit the virtual environment.

.. code-block:: bash
  
   cd /path/to/prga
   . ./envscr/activate
   python --version                                 # 3.8.2
   python -c "import prga; print(prga.VERSION)"     # 0.3.3
   deactivate

To run an FPGA-building example, run the following commands:

.. code-block:: bash

   # re-activate the virtual environment if you are not in it
   cd /path/to/prga
   . ./envscr/activate

   # run an FPGA-building example
   cd examples/fpga/scanchain/k4_N2_8x8
   make

To run an application-implementation example, run the following commands:

.. code-block:: bash

   # re-activate the virtual environment if you are not in it
   # make sure you build the corresponding FPGA first

   cd examples/target/bcd2bin/scanchain_k4_N2_8x8  # choose one design and one FPGA
   make                                            # make project
   make -C design                                  # run RTL-to-bitstream flow
   make -C tests/basic behav                       # run behavioral verification
   make -C tests/basic postsyn                     # run post-synthesis verification
   make -C tests/basic postimpl                    # run post-implementation verification

.. _envscr/install: https://github.com/PrincetonUniversity/prga/blob/release/envscr/install
.. _envscr/activate: https://github.com/PrincetonUniversity/prga/blob/release/envscr/activate
