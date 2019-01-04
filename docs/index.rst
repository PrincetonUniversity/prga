.. Princeton Reconfigurable Gate Array documentation master file, created by
   sphinx-quickstart on Mon Oct 29 21:04:40 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the documentation of Princeton Reconfigurable Gate Array!
====================================================================

Princeton Reconfigurable Gate Array (PRGA) is a customizable, scalable,
versatile, extensible open-source framework for building and using custom
FPGAs.

PRGA consists of three parts:

* The front-end, **the PRGA Builder**, a Python API for you to describe,
  optimize, and build your custom FPGAs. It is able to automatically inject
  switches and configuration circuitry into the custom FPGA, as well as
  automatically generate synthesizable RTL and other file inputs to the
  back-end RTL-to-bitstream flow.
* The back-end, **the PRGA Tool Chain**, a complete RTL-to-bitstream flow for
  implementing a target design on the custom FPGA. It uses `Yosys
  <http://www.clifford.at/yosys/>`_ for synthesis, `VPR
  <https://verilogtorouting.org/>`_ for pack, place & route. Unlike many of its
  predecessors, PRGA is not based on VPR, but only uses VPR as an external tool.
  In this way, PRGA is always ready for the latest updates and new features of
  VPR.
* **The PRGA Bitgen**, a C++ framework for creating bitstream generators for
  different configuration circuitry types. Bitstream generator built with this
  framework is able to process Yosys and VPR outputs and generates bitstream for
  the custom FPGA.

Features
--------
* Highly customizable FPGA structures: supporting custom IP cores,
  heterogeneous CLB/IOBs, custom routing connectivity, and more
* Scalability: capable of imitating commercial-class FPGAs
* Extensibility: modularized workflow and well-documented low-level API
* Versatility: supporting different configuration circuitry types

PRGA Documentation
==================

.. toctree::
   :maxdepth: 2
   
   intro
   prga-builder/prga

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
