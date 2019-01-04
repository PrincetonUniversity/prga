# -*- enconding: ascii -*-

"""Model port classes."""

__all__ = ['LogicalModelInputPort', 'LogicalModelOutputPort', 'LogicalModelClockPort',
        'ModelInputPort', 'ModelOutputPort', 'ModelClockPort']

import logging
_logger = logging.getLogger(__name__)

from ..common import ModelPortClass
from ..portpin.port import AbstractInputPort, AbstractClockPort, AbstractOutputPort
from ...exception import PRGAInternalError
from ..._util.util import uno

# ----------------------------------------------------------------------------
# -- Logical Model Ports -----------------------------------------------------
# ----------------------------------------------------------------------------
class LogicalModelInputPort(AbstractInputPort):
    """Logical model input port.

    Args:
        module (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        clock (:obj:`str`, default=None): name of the clock port if this port is a sequential endpoint
        port_class (`ModelPortClass`, default=None): [TODO: add explanation]
    """
    def __init__(self, module, name, width, clock = None, port_class = None):
        super(LogicalModelInputPort, self).__init__(module, name, width)
        self.__clock = clock
        self.__port_class = port_class

    @property
    def clock(self):
        """Name of the clock port if this is a sequential endpoint."""
        return self.__clock

    @property
    def port_class(self):
        """The 'port_class' of this model port."""
        return self.__port_class

    @property
    def is_logical(self):
        """Test if this is a logical port/pin."""
        return True

class LogicalModelOutputPort(AbstractOutputPort):
    """Logical model output port.

    Args:
        module (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        clock (:obj:`str`, default=None): name of the clock port if this port is a sequential
            startpoint/endpoint
        sources (:obj:`Sequence` [:obj:`str` ], default=tuple\(\)): names of the source ports of the
            combinational paths to this port
        port_class (`ModelPortClass`, default=None): [TODO: add explanation]
    """
    def __init__(self, module, name, width, clock = None, sources = None, port_class = None):
        super(LogicalModelOutputPort, self).__init__(module, name, width)
        self.__clock = clock
        self.__sources = uno(sources, tuple())
        self.__port_class = port_class

    @property
    def clock(self):
        """Name of the clock port if this is a sequential startpoint/endpoint."""
        return self.__clock

    @property
    def sources(self):
        """Names of the source ports of the combinational paths to this port."""
        return self.__sources

    @property
    def port_class(self):
        """The 'port_class' of this model port."""
        return self.__port_class

    @property
    def is_logical(self):
        """Test if this is a logical port/pin."""
        return True

class LogicalModelClockPort(AbstractClockPort):
    """Logical model clock port.

    Args:
        module (`AbstractLeafModule`-subclass): the module this port belongs to
        name (:obj:`str`): name of this port
        port_class (`ModelPortClass`, default=None): [TODO: add explanation]
    """
    def __init__(self, module, name, port_class = None):
        super(LogicalModelClockPort, self).__init__(module, name)
        self.__port_class = port_class

    @property
    def port_class(self):
        """The 'port_class' of this model port."""
        return self.__port_class

    @property
    def is_logical(self):
        """Test if this is a logical port/pin."""
        return True

# ----------------------------------------------------------------------------
# -- Logical & Physical Model Ports ------------------------------------------
# ----------------------------------------------------------------------------
class ModelInputPort(LogicalModelInputPort):
    """Model input port.

    Args:
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        clock (:obj:`str`, default=None): name of the clock port if this port is a sequential endpoint
        port_class (`ModelPortClass`, default=None): [TODO: add explanation]
    """

    @property
    def is_physical(self):
        """Test if this is a physical port/pin."""
        return True

class ModelOutputPort(LogicalModelOutputPort):
    """Model output port.

    Args:
        name (:obj:`str`): name of this port
        width (:obj:`int`): width of this port
        clock (:obj:`str`, default=None): name of the clock port if this port is a sequential
            startpoint/endpoint
        sources (:obj:`Sequence` [:obj:`str` ], default=tuple\(\)): names of the source ports of the
            combinational paths to this port
        port_class (`ModelPortClass`, default=None): [TODO: add explanation]
    """

    @property
    def is_physical(self):
        """Test if this is a physical port/pin."""
        return True

class ModelClockPort(LogicalModelClockPort):
    """Model clock port.

    Args:
        name (:obj:`str`): name of this port
        port_class (`ModelPortClass`, default=None): [TODO: add explanation]
    """

    @property
    def is_physical(self):
        """Test if this is a physical port/pin."""
        return True
