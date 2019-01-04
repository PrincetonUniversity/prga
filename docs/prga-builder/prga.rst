PRGA Builder API
================

This document describes the API to the PRGA Builder.

All classes/attributes/methods starting without underscores are high level APIs.
These APIs are more well-documented and robust, and are recommended for users
who are more interested in the back-end or hardware side of PRGA.

All classes/attributes/methods starting with one underscore are low level APIs.
For hackers and/or contributors, the low level APIs are a good starting point
for hacking.

High Level API
--------------

.. toctree:: 
   :maxdepth: 2

   prga.context
   prga.flow
   prga.exception
   
Low Level API
-------------

.. toctree::
   :maxdepth: 2

   prga._archdef
   prga._configcircuitry
   prga._context
   prga._optimization
   prga._rtlgen
   prga._timing
   prga._util
   prga._vpr
