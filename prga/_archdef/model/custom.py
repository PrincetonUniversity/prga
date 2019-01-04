# -*- enconding: ascii -*-

"""CustomModel: user-defined custom models.

Use 'CustomModel' to define a hard macro as an IP core that can be instantiated in the target design, or mapped by
the synthesizer.
"""

__all__ = ['CustomModel']

import logging
_logger = logging.getLogger(__name__)

from ..common import ModelPortClass, ModuleType
from port import ModelInputPort, ModelOutputPort, ModelClockPort
from ..moduleinstance.module import MutableLeafModule
from ...exception import PRGAInternalError, PRGAAPIError

# ----------------------------------------------------------------------------
# -- CustomModel -------------------------------------------------------------------
# ----------------------------------------------------------------------------
class CustomModel(MutableLeafModule):
    """User-defined custom models.

    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
        name (:obj:`str`): name of this model.
    """
    def __init__(self, context, name):
        super(CustomModel, self).__init__(context, name)

    # -- abstract property implementation ------------------------------------
    @property
    def type(self):
        """Type of this module."""
        return ModuleType.custom

    @property
    def is_logical(self):
        """Test if this is a logical module."""
        return True

    @property
    def is_physical(self):
        """Test if this is a physical module."""
        return True

    # -- exposed API --------------------------------------------------------
    def add_input(self, name, width = 1, clock = None):
        """Add an input port to this model.

        Args:
            name (:obj:`str`): name of the input port.
            width (:obj:`int`, default=1): width of the input port.
            clock (:obj:`str`, default=None): clock of this port if this port is a sequential endpoint.

        Raises:
            `PRGAAPIError`: if a port with the same name already exists.
        """
        if name in self._ports:
            raise PRGAAPIError("Custom model '{}' already has a port named '{}'"
                    .format(self.name, name))
        self._add_port(ModelInputPort(self, name, width, clock))

    def add_output(self, name, width = 1, clock = None, sources = None):
        """Add an output port to this model.

        Args:
            name (:obj:`str`): name of the output port.
            width (:obj:`int`, default=1): width of the output port.
            clock (:obj:`str`, default=None): clock of this port if this port is a sequential
                startpoint/endpoint.
            sources (:obj:`Sequence` [:obj:`str` ], default=tuple\(\)): names of the source ports of the
                combinational paths to this port

        Raises:
            `PRGAAPIError`: if a port with the same name already exists.
        """
        if name in self._ports:
            raise PRGAAPIError("Custom model '{}' already has a port named '{}'"
                    .format(self.name, name))
        self._add_port(ModelOutputPort(self, name, width, clock, sources))

    def add_clock(self, name):
        """Add a clock port to this model.

        Args:
            name (:obj:`str`): name of the clock port.

        Raises:
            `PRGAAPIError`: if a port with the same name already exists.
        """
        if name in self._ports:
            raise PRGAAPIError("Custom model '{}' already has a port named '{}'"
                    .format(self.name, name))
        self._add_port(ModelClockPort(self, name))

    def elaborate(self):
        """Elaborate this model (simply check all combinational/sequential paths are valid).
        
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
                    raise PRGAAPIError("Custom model '{}' does not have clock port '{}'"
                            .format(self.name, port.clock))
                if not clock.is_clock:
                    raise PRGAAPIError("Port '{}.{}' is not a clock"
                            .format(self.name, port.clock))
            if port.is_input:
                continue
            for src in port.sources:
                try:
                    source = self.ports[src]
                except KeyError:
                    raise PRGAAPIError("Custom model '{}' does not have input port '{}'"
                            .format(self.name, src))
                if not source.is_logical_source:
                    raise PRGAAPIError("Port '{}.{}' is not an input port"
                            .format(self.name, src))
