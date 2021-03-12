Bring Your Own IP Core
======================

This tutorial introduces how to bring your own hard IP cores into a custom FPGA
and use it during synthesis and place\&route.
The full script and source files can be found at
`examples/fpga/magic/hardpico`_,
and an example application can be found at
`examples/target/picosoc/margic_hardpico`_.

.. _examples/fpga/magic/hardpico: https://github.com/PrincetonUniversity/prga/tree/release/examples/fpga/magic/hardpico
.. _examples/target/picosoc/margic_hardpico: https://github.com/PrincetonUniversity/prga/tree/release/examples/target/picosoc/magic_hardpico

Introduction
------------

When discussing 

Hard IP cores are classified as ``Logic Primitive`` s in PRGA.
``Logic Primitive`` s (also called ``Logic Element`` s) are the lowest-level,
indivisible logical resources on an FPGA, for example LUTs, flipflops, and hard
adders.
The first step of the RTL-to-bitstream CAD flow is to synthesize the target
design onto ``Logic Primitive`` s.
PRGA uses `Yosys`_ for synthesis, and supports
combinations of the following synthesis approaches:

.. _Yosys: http://www.clifford.at/yosys 

- **Explicit Instantiation**: Directly instantiate ``Logic Primitive`` s in the
  target RTL.
- **Technology Mapping**: Map high-level operations (for example
  multiplication) and logic patterns (for example memory inferrence) onto
  specialized ``Logic Primitive`` s.
- **Logic Synthesis**: Implement combinational logic with LUTs (or other basic
  gates).

* **TODO**: Add an introduction about `ModuleView` s.
