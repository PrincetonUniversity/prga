# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import ModuleType
from prga._archdef.portpin.common import ConstNet
from prga._archdef.moduleinstance.module import AbstractLeafModule, AbstractNonLeafModule
from prga._archdef.moduleinstance.instance import PhysicalInstance

from abc import abstractproperty, abstractmethod

# ----------------------------------------------------------------------------
# -- AbstractSwitchModule ----------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractSwitchModule(AbstractLeafModule):
    """Abstract base class for switch modules.

    Args:
        name (:obj:`str`): name of this switch
    """
    @property
    def type(self):
        return ModuleType.switch

    @property
    def is_physical(self):
        """Test if this module is physical."""
        return True

    @abstractproperty
    def switch_type(self):
        """Type of this switch."""
        raise NotImplementedError

    @abstractproperty
    def inputs(self):
        """A :obj:`list` of `PortOrPinBit` that are the inputs to this switch."""
        raise NotImplementedError

    @abstractproperty
    def output(self):
        """One single `PortOrPinBit` that is the output of this switch."""
        raise NotImplementedError

# ----------------------------------------------------------------------------
# -- SwitchInstance ----------------------------------------------------------
# ----------------------------------------------------------------------------
class SwitchInstance(PhysicalInstance):
    """Physical instance of switch modules.

    Args:
        parent (`AbstractNonLeafModule`-subclass): the module this instance belongs to
        model (`AbstractSwitchModule`-subclass): the switch module to be instantiated
        name (:obj:`str`): the name of the instance
    """
    @property
    def inputs(self):
        """A :obj:`list` of `PortOrPinBit` that are the inputs to this switch instance."""
        return tuple(self._pins[x.bus.key][x.index] for x in self.model.inputs)

    @property
    def output(self):
        """A `PortOrPinBit` that is the output of this switch."""
        return self._pins[self.model.output.bus.key][self.model.output.index]

# ----------------------------------------------------------------------------
# -- AbstractShadowModule ----------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractShadowModule(AbstractLeafModule):
    """Abstract base class for shadow modules that do not affect the logical topology of the configurable modules.
    
    Args:
        name (:obj:`str`): name of this switch
    """
    @property
    def type(self):
        return ModuleType.shadow

    @property
    def is_physical(self):
        """Test if this module is physical."""
        return True

    def get_bit_through(self, bit):
        """Get the bit that is logically connected to the given ``bit`` in the module. 

        Args:
            bit (`PortOrPinBit`): a port bit in this module

        Note that the source/sink attribute of the bit through is usually flipped.
        """
        return ConstNet.open

# ----------------------------------------------------------------------------
# -- ShadowInstance ----------------------------------------------------------
# ----------------------------------------------------------------------------
class ShadowInstance(PhysicalInstance):
    """Physical instance of shadow modules.

    Args:
        parent (`AbstractNonLeafModule`-subclass): the module this instance belongs to
        model (`AbstractShadowModule`-subclass): the shadow module to be instantiated
        name (:obj:`str`): the name of the instance
    """
    def get_bit_through(self, bit):
        """Get the bit that is logically connected to the given ``bit`` in the instance.

        Args:
            bit (`PortOrPinBit`): a pin bit in this instance

        Note that the source/sink attribute of the bit through is usually flipped.
        """
        portbit = self.model.get_bit_through(bit.bus.port[bit.index])
        if portbit.is_open:
            return ConstNet.open
        else:
            return self._pins[portbit.bus.key][portbit.index]

# ----------------------------------------------------------------------------
# -- ConfigurableNonLeafModule -----------------------------------------------
# ----------------------------------------------------------------------------
class ConfigurableNonLeafModule(AbstractNonLeafModule):
    """Abstract configurable non-leaf module."""

    # == low-level API =======================================================
    def dfs_physical_paths(self, sink, sources):
        """Use DFS to find the physical path(s) to physical ``sink``.

        Args:
            sink (`PortOrPinBit`): the physical sink bit
            sources (:obj:`list` [`PortOrPinBit` or `ConstNet`]): the physical source bits 

        Returns:
            :obj:`list` [:obj:`tuple` \\(`PortOrPinBit`, :obj:`list` [`PortOrPinBit` ] or None\\)]: a list of
                2-tuples. The first element is the physical source bit or const net that can be connected to ``sink``
                under some confiragution; the second element is a list of switch input bits on the physical path, or
                None if no path exist from the source bit to ``sink``. Note the returned list may not preserve the
                order of ``sources``
        """
        stack, sources = [(sink.physical_source, [])], list(iter(sources))
        results = []
        while stack:
            bit, path = stack.pop()
            if bit in sources:
                results.append( (bit, path) )
                sources.remove( bit )
            if bit.is_port or bit.is_const: # reaches end of the subtree
                continue
            elif bit.parent.is_switch: # pass through a switch
                for ibit in bit.parent.inputs:
                    stack.append( (ibit.physical_source, [ibit] + path) )
            elif bit.parent.is_shadow: # pass through shadow physical-only instance
                bit = bit.parent.get_bit_through( bit )
                if bit.is_const:
                    stack.append( (bit, path) )
                else:
                    stack.append( (bit.physical_source, path) )
            else: # stop at other types of instance pins
                pass
        results.extend( (unconnected, None) for unconnected in sources )
        return results
