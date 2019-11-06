Development Guide: Architecture
===============================

Domains
-------

The key challenge of PRGA is to make multiple tools work together seamlessly.
PRGA tackles this challenge by dividing the architecture into three domains:
the user domain, the logical domain, and the physical domain.

.. image:: /_static/images/domains.png

The figure above shows an IOB in different domains:

User Domain
^^^^^^^^^^^

The figure to the left shows the IOB in the user domain. All instances in this
domain are converted to `\<pb_type\>
<http://docs.verilogtorouting.org/en/latest/arch/reference/#complex-blocks>`_
s when generating `VPR <http://docs.verilogtorouting.org/en/latest/vpr/>`_ 's
architecture description of the FPGA, and available to FPGA users. Each
output port or input pin may be connected to more than one input port or
output pin in this domain, indicating the configurability of these connections.
These connections are converted to `\<interconnect\>
<http://docs.verilogtorouting.org/en/latest/arch/reference/#interconnect>`_ tags
when generating `VPR <http://docs.verilogtorouting.org/en/latest/vpr/>`_ 's
architecture description.

Logical Domain
^^^^^^^^^^^^^^

The figure in the middle shows the IOB in the logical domain. Configurable
connections are implemented with switches. Configuration circuitry is also
injected and connected.

Most of the code of PRGA works in this domain.

Physical Domain
^^^^^^^^^^^^^^^

Physical domain is used for RTL generation as well as backend processing. Note
that in the figure shown above, the IO pad instance is not present in the
physical domain. Each pin of this logical-only instance is mapped to a physical
port, shown as the dashed lines in the figure.
