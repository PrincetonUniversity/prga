# Python 2 and 3 compatible
from prga.compatible import *

from prga._archdef.common import ModuleType, PrimitiveType, PrimitivePortClass
from prga._archdef.moduleinstance.module import MutableLeafModule
from prga._archdef.primitive.port import PrimitiveInputPort, PrimitiveOutputPort, PrimitiveClockPort
from prga.exception import PRGAInternalError, PRGAAPIError

# ----------------------------------------------------------------------------
# -- CustomPrimitive ---------------------------------------------------------
# ----------------------------------------------------------------------------
class CustomPrimitive(MutableLeafModule):
    """User-defined custom primitives.o

    Args:
        name (:obj:`str`): name of this primitive
    """
    # == low-level API =======================================================
    @property
    def type(self):
        """Type of this module."""
        return ModuleType.primitive

    @property
    def primitive_type(self):
        """Type of this primitive."""
        return PrimitiveType.custom

    @property
    def is_logical(self):
        """Test if this is a logical primitive."""
        return True

    @property
    def is_physical(self):
        """Test if this is a physical primitive."""
        return True

    # == high-level API ======================================================
    def add_input(self, name, width, clock = None):
        """Add an input port to this primitive.

        Args:
            name (:obj:`str`): name of the input port.
            width (:obj:`int`): width of the input port.
            clock (:obj:`str`): clock of this port if this port is a sequential endpoint.

        Raises:
            `PRGAAPIError`: if a port with the same name already exists.
        """
        try:
            self.add_port(PrimitiveInputPort(self, name, width, clock))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

    def add_output(self, name, width, clock = None, sources = None):
        """Add an output port to this primitive.

        Args:
            name (:obj:`str`): name of the output port.
            width (:obj:`int`): width of the output port.
            clock (:obj:`str`): clock of this port if this port is a sequential startpoint/endpoint.
            sources (:obj:`list` [:obj:`str` ]): names of the source ports of the combinational paths to this port

        Raises:
            `PRGAAPIError`: if a port with the same name already exists.
        """
        try:
            self.add_port(PrimitiveOutputPort(self, name, width, clock, sources))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

    def add_clock(self, name):
        """Add a clock port to this primitive.

        Args:
            name (:obj:`str`): name of the clock port.

        Raises:
            `PRGAAPIError`: if a port with the same name already exists.
        """
        try:
            self.add_port(PrimitiveClockPort(self, name))
        except PRGAInternalError as e:
            raise_from(PRGAAPIError(e.message), e)

    def elaborate(self):
        """Elaborate this primitive (simply check all combinational/sequential paths are valid).
        
        Raises:
            `PRGAAPIError`: if invalid combinational/sequential paths exist.
        """
        for port in self.ports.itervalues():
            if port.is_clock:
                continue
            if port.clock is not None:
                try:
                    clock = self.ports[port.clock]
                except KeyError:
                    raise PRGAAPIError("Custom primitive '{}' does not have clock port '{}'"
                            .format(self.name, port.clock))
                if not clock.is_clock:
                    raise PRGAAPIError("Port '{}/{}' is not a clock"
                            .format(self.name, port.clock))
            if port.is_input:
                continue
            for src in port.sources:
                try:
                    source = self.ports[src]
                except KeyError:
                    raise PRGAAPIError("Custom primitive '{}' does not have input port '{}'"
                            .format(self.name, src))
                if not source.is_logical_source:
                    raise PRGAAPIError("Port '{}/{}' is not an input port"
                            .format(self.name, src))
