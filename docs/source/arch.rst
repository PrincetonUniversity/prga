Architecture & Customizability
==============================

.. image:: /_static/images/zoomx3.png
   :width: 100 %
   :alt: PRGA Architecture Hierarchy
   :align: center

The FPGA architecture supported by PRGA is highly customizable and flexible.
As shown in the figure above, the FPGA is organized as a 2-dimensional ``Array``
of ``Tile`` s, ``Switch Box`` es, and nested ``Array`` s.
Each ``Tile`` contains one ``Logic Block`` or multiple ``IO Block`` s, in
addition to various numbers of ``Connection Box`` es.
Each ``Logic Block`` or ``IO Block`` consists of zero to many ``Slice`` s
and ``Logic Primitive`` s.
``Slice`` s are composed of nested ``Slice`` s and ``Logic Primitive`` s.
Readers familiar with `VPR`_ should find these concept pretty intuitive.

.. _VPR: https://verilogtorouting.org/
