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

* `Verilog-to-Routing <https://verilogtorouting.org/>`_
* `Yosys <http://www.clifford.at/yosys/>`_
* `Icarus Verilog <http://iverilog.icarus.com/>`_ or `Synopsys VCS
  <https://www.synopsys.com/verification/simulation/vcs.html>`_

Python
^^^^^^

PRGA works with Python 2.7.x and Python 3.7.x. However, Python 2.x will reach
its end of life on `January 1st, 2020
<https://www.python.org/doc/sunset-python-2/>`_ , so we recommend using Python
3.7.x if possible.


Examples
--------

Examples are provided in the ``examples/`` directory. FPGA building examples are
provided in the ``examples/fpga/`` directory, and RTL-to-verification examples
are provided in the ``examples/target/`` directory.

To build an FPGA, run the following commands:

.. code-block:: bash

    cd /path/to/prga/                           # cd to the root 
    source envscr/settings.sh                   # set up the environment
    cd examples/fpga/tiny/k4_N2_8x8             # choose one FPGA building example
    make                                        # build the FPGA!

To implement a target design and simulate it with an FPGA design, run the
following commands:

.. code-block:: bash

    cd /path/to/prga/                           # cd to the root 
    source envscr/settings.sh                   # set up the environment
    cd examples/target/bcd2bin/tiny_k4_N2_8x8   # choose one design and one FPGA
    make                                        # run all the way to verification
