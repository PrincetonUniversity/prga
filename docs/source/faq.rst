Frequently Asked Questions
==========================

This part covers some of the frequently asked questions.

Simulation stuck at bitstream loading
-------------------------------------

Cause
~~~~~

When simulating bitstream loading, the simulation might be stuck at some
point. A common cause of the problem is that a zero-delay combinational loop
forms due to a partial configuration. This is very common in serial
configuration circuitries such as bitchain, widechain, packetized-chain, etc.

Solution
~~~~~~~~
Modify the RTL generated for the switches (normally named ``cfg_mux*.v``) and
add a small delay in the combinational path (for small FPGAs ``#0.1`` is good
enough, but if VPR routes a very long path, ``#0.01`` or smaller may be
needed).
