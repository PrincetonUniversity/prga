prga.tools.simproj package
==========================

Generate a simulation/verification project for a target design on a custom FPGA built with PRGA.

This tool is composed of three sub-tools, namely :py:mod:`prga.tools.simproj.tbgen`,
:py:mod:`prga.tools.simproj.ysgen`, and :py:mod:`prga.tools.simproj.mkgen`.

The first one, :py:mod:`prga.tools.simproj.tbgen`, generates a testbench Verilog module given a test **host** module.
It handles the bitstream loading logic, keeps track of simulation time, and connects the test host and the custom FPGA
correctly based on the IO binding specified by the user. The generated testbench has one macro, ``FPGA_TEST``, which
enables the simulation of the target design implemented on the custom FPGA if set.

A **host** module is expected to have all the ports that the target design has, with opposite direction. In addition,
3 input ports (``sys_clk``, ``sys_rst``, and ``cycle_count``) and 2 output ports (``sys_success``, and ``sys_fail``)
are required to communicate with the generated testbench. The functions of these ports are straightforward as
suggested by their names.

The second one, :py:mod:`prga.tools.simproj.ysgen`, generates the synthesis script for Yosys. Available logic elements
(primitives) and IP cores on the custom FPGA are specified in the generated script, so Yosys is able to utilize those
when synthesizing the target design.

The last one, :py:mod:`prga.tools.simproj.mkgen` generates a ``Makefile``, which allows the user to run the complete
Verilog-to-bitstream flow and simulate the target design with one command.

This Python module can also be run as one single program via the '-m' switch. For example:

.. code-block:: python

    python -m prga.tools.simproj CTX.pickled TARGET.v HOST.v IO.pads

This will automatically run all three sub-tools and create a complete simulation/verification project.

Submodules
----------

.. toctree::

   prga.tools.simproj.mkgen
   prga.tools.simproj.tbgen
   prga.tools.simproj.ysgen

Module contents
---------------

.. automodule:: prga.tools.simproj
    :members:
    :undoc-members:
    :show-inheritance:
