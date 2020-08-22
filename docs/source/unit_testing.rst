************
UNIT TESTING
************
PRGA provides a pass which automatically generate unit tests for the Verilog Modules used in the FPGA Fabric along with a route testing.

The tests use `cocotb <https://cocotb.readthedocs.io/>`_, a framework for testing VHDL/Verilog designs using python.

Requirements
------------
* `Context` object which was used for descibing the FPGA Architecture

.. code-block:: python

    from prga import *
    from prga.core.context import Context

    