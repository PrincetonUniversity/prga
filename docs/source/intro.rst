Introduction
============

Princeton Reconfigurable Gate Array (PRGA) is a customizable, scalable,
versatile, extensible open-source framework for building and using custom
FPGAs.

Prerequisites
-------------

Tools
^^^^^

PRGA is dependent on the following third-party tools:

* `Icarus Verilog <http://iverilog.icarus.com/>`_ or `Synopsys VCS
  <https://www.synopsys.com/verification/simulation/vcs.html>`_

Installation
------------

PRGA includes `Yosys <http://www.clifford.at/yosys/>`_ and `VTR
<http://www.clifford.at/yosys/>`_ as submodules, 
uses `pyenv <https://github.com/pyenv/pyenv>`_ and `pipenv
<https://github.com/pypa/pipenv>`_ to manage Python interpretter and
dependecies, and simplifies the installation with one single bash script that
does not require root access:

.. code-block:: bash

    cd /path/to/prga/
    ./envscr/install

Examples
--------

Examples are provided in the ``examples/`` directory. FPGA building examples are
provided in the ``examples/fpga/`` directory, and RTL-to-verification examples
are provided in the ``examples/target/`` directory.

To build an FPGA, run the following commands:

.. code-block:: bash

    cd /path/to/prga/                           # cd to the root 
    ./envscr/activate                           # activate the virtual environment
    cd examples/fpga/tiny/k4_N2_8x8             # choose one FPGA building example
    make                                        # build the FPGA!

To implement a target design and simulate it with an FPGA design, run the
following commands:

.. code-block:: bash

    cd /path/to/prga/                           # cd to the root 
    ./envscr/activate                           # activate the virtual environment
    cd examples/target/bcd2bin/tiny_k4_N2_8x8   # choose one design and one FPGA
    make                                        # run all the way to verification
