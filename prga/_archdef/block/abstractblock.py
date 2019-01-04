# -*- encoding: ascii -*-

"""Abstract base classes for all blocks, including routing blocks."""

__all__ = ['AbstractBlock', 'AbstractLogicalBlock']

import logging
_logger = logging.getLogger(__name__)

from port import PhysicalBlockInputPort, PhysicalBlockOutputPort
from ..common import ModuleType, BlockType, SwitchType
from ..moduleinstance.module import MutableNonLeafModule
from ..moduleinstance.instance import PhysicalInstance, Instance
from ..portpin.common import ConstNet
from ..portpin.port import PhysicalInputPort, PhysicalOutputPort
from ...exception import PRGAInternalError, PRGAAPIError
from ..._util.util import phash, uno

from itertools import ifilter, chain, izip
from abc import abstractproperty, abstractmethod
import re

# ----------------------------------------------------------------------------
# -- AbstractBlock -----------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractBlock(MutableNonLeafModule):
    """Abstract base class for all blocks, including routing blocks.
    
    Args:
        context (`ArchitectureContext`): the architecture context this block belongs to
        name (:obj:`str`): name of this block
    """

    def __init__(self, context, name):
        super(AbstractBlock, self).__init__(context, name)

    # -- internal API --------------------------------------------------------
    @property
    def is_physical(self):
        """Test if this is a physical module."""
        return True

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

    def _get_or_create_physical_input(self, name, width, global_ = None):
        """Get or create physical input port with the given name & width.

        Args:
            name (:obj:`str`):
            width (:obj:`int`):
            global_ (:obj:`str`, default=None):

        Returns:
            `PhysicalBlockInputPort`:

        Raises:
            `PRGAInternalError`: if a port with the given name already exists but the type/direction does not match
        """
        port = self._ports.get(name, None)
        if port is not None:
            if not (port.is_input and port.is_physical and port.width == width):
                raise PRGAInternalError("Port '{}' is not a {}-bit physical input"
                        .format(name, width))
            elif port.global_ is None:
                port.global_ = global_
            elif global_ is not None and port.global_ != global_:
                raise PRGAInternalError("Port '{}' was connected to global wire '{}' instead of '{}'"
                        .format(name, port.global_, global_))
        else:
            port = self._ports[name] = PhysicalBlockInputPort(self, name, width, global_)
        return port

    def _get_or_create_physical_output(self, name, width):
        """Get or create physical output port with the given name & width.

        Args:
            name (:obj:`str`):
            width (:obj:`int`):

        Returns:
            `PhysicalBlockOutputPort`:

        Raises:
            `PRGAInternalError`: if a port with the given name already exists but the type/direction does not match
        """
        port = self._ports.get(name, None)
        if port is not None:
            if not (port.is_output and port.is_physical and port.width == width):
                raise PRGAInternalError("Port '{}' is not a {}-bit physical output"
                        .format(name, width))
        else:
            port = self._ports[name] = PhysicalBlockOutputPort(self, name, width)
        return port

    # -- mapping physical bits -----------------------------------------------
    # -- find the physical paths ---------------------------------------------
    def _dfs_physical_paths(self, sink, sources):
        """Use DFS to find the physical path(s) to physical ``sink``.

        Args:
            sink (`PortOrPinBit`): the physical sink bit
            sources (:obj:`Sequence` [`PortOrPinBit` or `ConstNet`]): the physical source bits

        Returns:
            :obj:`list` [:obj:`tuple` \(`PortOrPinBit`, :obj:`list` [`PortOrPinBit` ] or None\)]: a list of 2-tuples.
                The first element is the physical source bit or const net that is configurably connected to ``sink``;
                the second element is a list of mux input bits on the physical path, or None if no path exist from the
                source bit to ``sink``. Note the returned list may not preserve the order of the ``sources`` passed in
        """
        stack, sources = [(sink, [])], list(iter(sources))
        results = []
        while len(stack) > 0:
            bit, path = stack.pop()
            if bit in sources:
                results.append( (bit, path) )
                sources.remove(bit)
            if bit.is_port or bit.is_open or bit.is_const:
                continue
            if bit.parent_instance.is_switch:
                assert bit.parent_instance.is_mux_switch
                for muxbit in bit.parent_instance._pins['i']:
                    stack.append( (muxbit._physical_source, [muxbit] + path) )
            elif bit.parent_instance.is_addon:
                eqv = bit.parent_instance.model._find_equivalent_pin(bit)
                if eqv is None:
                    continue
                stack.append( (eqv._physical_source, path) )
        results.extend( (unconnected, None) for unconnected in sources)
        return results

    # -- implement connections -----------------------------------------------
    def _instantiate_configurable_mux(self, sources, sink):
        """Instantiate a `PhysicalInstance` of a configurable mux between the given ``sources`` and ``sink``.

        Args:
            sources (:obj:`list` [`ConstNet` or `PortOrPinBit` ]):
            sink (`PortOrPinBit`):

        Returns:
            `PhysicalInstance`:

        The created `PhysicalInstance` will neither be added to the block nor connected to the ``sink``, because the
        muxes might be created when iterating through instances. However, the ``sources`` are connected, because
        connections are always stored in the drivee, which will not affect the ``sources``.
        """
        instance = PhysicalInstance(self._context._get_model('cmux{}'.format(len(sources))),
                'cmux_{:x}'.format(phash(sink.reference)))
        instance._pins['i']._physical_source = sources
        return instance

    def _materialize_connections(self):
        """Materialize logical connections.

        This method will materialize all logical connections. More specifically, for all logical sinks that have only
        one logical source, a direct physical connection will be created; for all logical sinks that have more than
        one logical source, a programmable mux will be created and connected.
        """
        muxes = []
        for port in ifilter(lambda x: x.is_sink, chain(self.ports.itervalues(),
            iter(pin for instance in self.instances.itervalues() for pin in instance.pins.itervalues()))):
            for bit in port:
                sink_bit = bit._physical_cp
                source_bits = tuple(x._physical_cp for x in bit._logical_sources)
                if len(source_bits) > 1: # a mux is needed
                    muxes.append((self._instantiate_configurable_mux(source_bits, sink_bit), sink_bit))
                elif len(source_bits) == 1: # direct connection
                    sink_bit._physical_source = source_bits[0]
        for mux, sink_bit in muxes:
            sink_bit._physical_source = mux._pins['o']
            self._add_instance(mux)

    # -- exposed API --------------------------------------------------------
    @property
    def type(self):
        """Type of this module."""
        return ModuleType.block

    @abstractproperty
    def block_type(self):
        """Type of this block."""
        raise NotImplementedError

# ----------------------------------------------------------------------------
# -- AbstractLogicalBlock ----------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractLogicalBlock(AbstractBlock):
    """Abstract base class for logic and IO blocks."""

    def __init__(self, context, name):
        super(AbstractLogicalBlock, self).__init__(context, name)
        self._pack_patterns = []    # a pair of (source, sink) pin/port bits

    # -- internal API --------------------------------------------------------
    def _validate_port_name(self, name):
        """Validate the name of the port.
        
        Raises:
            `PRGAAPIError`: if the block already has a port with the same name, or the name of the port conflicts
                with reserved port names.
        """
        self._context._validate_block_port_name(name)
        if name in self._ports:
            raise PRGAAPIError("Block '{}' already has a port named '{}'"
                    .format(self.name, name))

    def _dereference_net(self, reference, physical_allowed = False):
        """Dereference a net reference.

        Args:
            reference (`NetReference`): a reference to ports
            physical_allowed (:obj:`bool`, default=False): if physical bits are allowed to be dereferenced

        Returns:
            :obj:`Sequence` [`ConstNet` or `PortOrPinBit`]: the referenced port bits

        Raises:
            `PRGAInternalError`: if the reference does not refer to any port/pin in the module
        """
        if reference.is_open or reference.is_const:
            return (ConstNet(reference.type), ) * reference.high
        pin = None
        if reference.is_port:
            try:
                pin = (self._ports if physical_allowed else self.ports)[reference.pin]
            except KeyError:
                raise PRGAInternalError("Port '{}' not found in logic/io block '{}'"
                        .format(reference.pin, self.name))
        else:
            try:
                instance = (self._instances if physical_allowed else self.instances)[reference.instance]
            except KeyError:
                raise PRGAInternalError("Sub-instance '{}' not found in logic/io block '{}'"
                        .format(reference.instance, self.name))
            try:
                pin = (instance._pins if physical_allowed else instance.pins)[reference.pin]
            except KeyError:
                raise PRGAInternalError("Pin '{}' not found in sub-instance '{}' in logic/io block '{}'"
                        .format(reference.pin, reference.instance, self.name))
        if reference.low is None:
            return pin[:]
        elif reference.high >= pin.width or reference.low >= pin.width:
            raise PRGAInternalError("Port '{}.{}' width: {}, reference range: [{}:{}]"
                    .format(uno(reference.instance, self.name), pin.name, pin.width, reference.high, reference.low))
        else:
            return pin[reference.low : reference.high + 1]

    def _reorder_ports(self):
        """Reorder ports to meet VPR's ordering requirements."""
        inputs, outputs, clocks, others = [], [], [], []
        for port in self._ports.itervalues():
            if not port.is_logical:
                others.append(port)
            elif port.is_clock:
                clocks.append(port)
            elif port.is_input:
                inputs.append(port)
            else:
                outputs.append(port)
        self._ports.clear()
        for port in chain(sorted(inputs, key=lambda x: x.name),
                sorted(outputs, key=lambda x: x.name),
                sorted(clocks, key=lambda x: x.name),
                others):
            self._ports[port.name] = port

    # -- exposed API --------------------------------------------------------
    @property
    def width(self):
        """Width of the block."""
        return 1

    @property
    def height(self):
        """Height of the block."""
        return 1

    @property
    def capacity(self):
        """Number of blocks placed in one tile."""
        return 1

    def add_instance(self, name, model):
        """Add a sub-instance to this block.

        Args:
            name (:obj:`str`): name of this instance
            model (:obj:`str`): name of the model being instantiated

        Raises:
            `PRGAAPIError`: if no model with the name ``model`` is found in the `ArchitectureContext` this block
                belongs to, or an instance with the same name already exists, or the ``name`` conflicts with reserved
                instance names [TODO: add explanation of reserved names]

        This method will look for the model in the `ArchitectureContext` this block belongs to, and create an instance
        of the model.
        """
        try:
            # 1. check if the name is a reserved name
            self._context._validate_block_instance_name(name)
            if name in self._instances:
                raise PRGAAPIError("Block '{}' already has a sub-instance named '{}'"
                        .format(self.name, name))
            # 2. find the model
            try:
                model = self._context._get_user_model(model)
            except PRGAInternalError as e:
                raise PRGAAPIError(str(e))
            # 3. create and add the instance to this block
            self._add_instance(Instance(model, name))
        except PRGAAPIError:
            raise

    def add_connections(self, sources, sinks, fully_connected = False, pack_pattern = False):
        """Add configurable connections between logical ports/pins inside the block.

        Args:
            sources, sinks: a bit, a list of bits, a port, a list of ports, etc.
            fully_connected (:obj:`bool`, default=``False``): by default, the connections are created in a bit-wise
                pairing manner. If set to ``True``, a full connection will be created between the sources and sinks
            pack_pattern (:obj:`bool`, default=``False``): this is an advanced feature for VPR only. Set this to True
                will mark all created connections as `pack_pattern
                <http://docs.verilogtorouting.org/en/latest/arch/reference/#tag-interconnect-pack_pattern>`_

        Raises:
            `PRGAAPIError`: if not fully connected and the number of source bits and the number of sink bits don't
                match, or any of the sources is not a logical source, or any of the sinks is not a logical sink

        Examples:
            >>> block = ... # assume a block is created somehow
            # set up ports & instances
            >>> block.add_input("A", 8, Side.left)
            >>> block.add_input("AX", 1, Side.left)
            >>> block.add_output("O", 2, Side.right)
            >>> block.add_output("OX", 1, Side.right)
            >>> block.add_clock("C", Side.bottom)
            >>> block.add_instance("lut_inst0", "lut4")
            >>> block.add_instance("lut_inst1", "lut4")
            >>> block.add_instance("ff_inst0", "flipflop")
            >>> block.add_instance("ff_inst1", "flipflop")
            >>> block.add_instance("mux_inst0", "MUX2") # MUX2 is a user-defined mux
            # add connections by port/pin
            >>> block.add_connections(block.instances['mux_inst0'].pins['out'], block.ports['OX'])
            # add connections by bits
            >>> block.add_connections(block.ports['AX'], block.instances['mux_inst0'].pins['sel'][0])
            # use fully_connected
            >>> block.add_connections(block.ports['C'],
                    [block.instances['ff_inst0'].pins['c'], block.instances['ff_inst1'].pins['c']],
                    fully_connected = True)
            # add connections by mixing port slices, lists and non-lists
            >>> block.add_connections(block.ports['A'][0:3], block.instances['lut_inst0'].pins['i'])
            >>> block.add_connections(block.ports['A'][4:7], block.instances['lut_inst1'].pins['i'])
            >>> block.add_connections(
                    [block.instances['lut_inst0'].pins['o'], block.instances['lut_inst1'].pins['o']],
                    block.instances['mux_inst0'].pins['i'])
            # use pack_pattern
            >>> block.add_connections(
                    [block.instances['lut_inst0'].pins['o'], block.instances['lut_inst1'].pins['o']],
                    [block.instances['ff_inst0'].pins['d'], block.instances['ff_inst0'].pins['d']],
                    pack_pattern = True)
            # add multiple connections to the same port/pin will cause a programmable mux to be created later
            >>> block.add_connections(
                    [block.instances['lut_inst0'].pins['o'], block.instances['lut_inst1'].pins['o']],
                    block.ports['O'])
            >>> block.add_connections(
                    [block.instances['ff_inst0'].pins['q'], block.instances['ff_inst1'].pins['q']],
                    block.ports['O'])
        """
        # 1. create the list of sources
        sources_ = []
        try:
            for src in sources:
                try:
                    for s in src:
                        sources_.append(s)
                except TypeError:
                    sources_.append(src)
        except TypeError:
            sources_.append(sources)
        for source in sources_:
            if not source.is_logical_source:
                raise PRGAAPIError("'{}' is not a logical source".format(source))
        # 2. create the list of sinks
        sinks_ = []
        try:
            for sink in sinks:
                try:
                    for s in sink:
                        sinks_.append(s)
                except TypeError:
                    sinks_.append(sink)
        except TypeError:
            sinks_.append(sinks)
        for sink in sinks_:
            if not sink.is_logical_sink:
                raise PRGAAPIError("'{}' is not a logical sink".format(sink))
        # 3. create the actual connections
        if fully_connected:
            for sink in sinks_:
                sink._add_logical_sources(sources_)
                if pack_pattern:
                    for source in sources_:
                        self._pack_patterns.append( (source, sink) )
        else:
            if len(sources_) != len(sinks_):
                raise PRGAAPIError("The number of source bits ({}) does not match with the number of sink bits ({})"
                        .format(len(sources_), len(sinks_)))
            for source, sink in izip(iter(sources_), iter(sinks_)):
                sink._add_logical_sources(source)
                if pack_pattern:
                    self._pack_patterns.append( (source, sink) )
