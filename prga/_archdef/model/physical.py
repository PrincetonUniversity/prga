# -*- enconding: ascii -*-

"""Configuration and add-on physical-only models."""

__all__ = []

import logging
_logger = logging.getLogger(__name__)

from ..common import ModuleType
from ..moduleinstance.module import AbstractLeafModule
from ...exception import PRGAInternalError

# ----------------------------------------------------------------------------
# -- _AbstractPhysicalModel --------------------------------------------------
# ----------------------------------------------------------------------------
class _AbstractPhysicalModel(AbstractLeafModule):
    """Abstract base class for `AbstractAddonModel` and `AbstractConfigModel`"""

    @property
    def template(self):
        """Name of the template if there is one."""
        return None

    @property
    def rtlgen_parameters(self):
        """Parameters used for RTL generation."""
        return {}

    @property
    def is_physical(self):
        """Test if this is a physical module."""
        return True

# ----------------------------------------------------------------------------
# -- AbstractAddonModel ------------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractAddonModel(_AbstractPhysicalModel):
    """Abstract base class for add-on physical-only models.

    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
        name (:obj:`str`): name of this model
    """
    @property
    def type(self):
        """Type of this module."""
        return ModuleType.addon

    def _find_equivalent_pin(self, bit):
        """Find the equivalent pin of the given ``bit``.

        Args:
            bit (`PortOrPinBit`): a bit in a pin of an instance of this model
        """
        return None

# ----------------------------------------------------------------------------
# -- AbstractConfigModel -----------------------------------------------------
# ----------------------------------------------------------------------------
class AbstractConfigModel(_AbstractPhysicalModel):
    """Abstract base class for configuration models.

    Args:
        context (`ArchitectureContext`): the architecture context this model belongs to
        name (:obj:`str`): name of this model
    """
    @property
    def type(self):
        """Type of this module."""
        return ModuleType.config
