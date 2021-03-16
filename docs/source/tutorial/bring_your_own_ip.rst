Bring Your Own IP Core
======================

This tutorial introduces how to bring your own hard IP cores into a custom FPGA
and use it during synthesis and place\&route.
The full script and source files can be found at
`examples/fpga/magic/hardpico`_,
and an example application can be found at
`examples/app/picosoc/margic_hardpico`_.

.. _examples/fpga/magic/hardpico: https://github.com/PrincetonUniversity/prga/tree/release/examples/fpga/magic/hardpico
.. _examples/app/picosoc/margic_hardpico: https://github.com/PrincetonUniversity/prga/tree/release/examples/app/picosoc/magic_hardpico

Introduction
------------

Hard IP cores fall in the :ref:`Logic Primitive` category in PRGA.
The first step of the RTL-to-bitstream CAD flow is to synthesize the app
design onto :ref:`Logic Primitive` s.
PRGA uses `Yosys`_ for synthesis, and supports
combinations of the following synthesis approaches:

.. _Yosys: http://www.clifford.at/yosys 

- **Explicit Instantiation**: Directly instantiate :ref:`Logic Primitive` s in the
  target RTL.
- **Technology Mapping**: Map high-level operations (for example
  multiplication) and logic patterns (for example memory inferrence) onto
  specialized :ref:`Logic Primitive` s.
- **Logic Synthesis**: Implement combinational logic with LUTs (or other basic
  gates).

Work in progress.
