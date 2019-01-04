Module: prga.context
====================

.. module:: prga.context

High Level API
--------------

.. autoclass:: ArchitectureContext
   :show-inheritance:

   .. attribute:: name
      
      :obj:`str`, read-only
      
      The name of this context. This will be used as the name of the top-level
      RTL module.

   .. attribute:: array
   
      `prga._archdef.array.array.Array`, read-only

      The block array.
   
   .. attribute:: models
   
      :obj:`dict`, read-only

      Logic element (primitive) models indexed by their names. For example, you
      may use ``models["lut4"]`` to get the model for 4-input LUTs.

   .. attribute:: blocks
   
      :obj:`dict`, read-only

      CLB/IOBs indexed by their names.

   .. attribute:: globals
   
      :obj:`dict`, read-only

      Global routing wires indexed by their names.

   .. attribute:: segments
   
      :obj:`dict`, read-only

      Routing wire segments indexed by their names.

   .. automethod:: create_model

   .. automethod:: create_logic_block

   .. automethod:: create_io_block

   .. automethod:: create_segment

   .. automethod:: create_global

   .. automethod:: pickle

   .. automethod:: unpickle

.. autoclass:: Side
   :members:
   :show-inheritance:

Low Level API
-------------
.. attribute:: ArchitectureContext._models

   :obj:`dict`

   Leaf-level RTL modules indexed by their names. More modules are indexable
   via this attribute than `ArchitectureContext.models`, including configurable
   mux modules and other modules that cannot be used as logic elements
   (primitives).

.. attribute:: ArchitectureContext._blocks

   :obj:`dict`

   The same :obj:`dict` as `ArchitectureContext.blocks`, only that this
   attribute allows writing to it.

.. attribute:: ArchitectureContext._connection_blocks

   :obj:`dict`

   Connection blocks indexed by their names.

.. attribute:: ArchitectureContext._switch_blocks

   :obj:`dict`

   Switch blocks indexed by their names.

.. automethod:: ArchitectureContext._iter_physical_blocks

.. automethod:: ArchitectureContext._get_user_model

.. automethod:: ArchitectureContext._get_model

.. automethod:: ArchitectureContext._validate_block_port_name

.. automethod:: ArchitectureContext._validate_block_instance_name

.. automethod:: ArchitectureContext._get_or_create_connection_block

.. automethod:: ArchitectureContext._get_or_create_switch_block
