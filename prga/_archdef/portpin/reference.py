# -*- enconding: ascii -*-

"""Net reference used for serialization/deserialization."""

__all__ = ['NetBundle', 'NetReference']

import logging
_logger = logging.getLogger(__name__)

from common import AbstractNet
from ..common import NetType
from ...exception import PRGAInternalError
from ..._util.util import regex, uno

from collections import namedtuple

# ----------------------------------------------------------------------------
# -- NetBundle ---------------------------------------------------------------
# ----------------------------------------------------------------------------
class NetBundle(namedtuple('NetBundle_namedtuple', 'type bus low high'), AbstractNet):
    """Helper class used to bundle individual port/pin bits back to bus slices.

    Args:
        type (`NetType`): type of this reference
        bus (Port or `Pin`): the original bus to be sliced
        low, high (:obj:`int`): the LSB and MSB of the slice
    """

    @classmethod
    def _Create(cls, bit):
        """Create a bundle from a single bit.

        Args:
            bit (`PortOrPinBit` or `ConstNet`):

        Returns:
            `NetBundle`:
        """
        if bit.is_const or bit.is_open:
            return cls(bit.type, None, None, 1)
        else:
            return cls(bit.type, bit.parent, bit.index, bit.index)

    @classmethod
    def _Bundle(cls, bits):
        """Create a list of bundles for a list of bits.

        Args:
            bits (:obj:`list` [`PortOrPinBit` or `ConstNet` ]):

        Returns:
            :obj:`list` [`NetBundle` ]:
        """
        list_, bundle = [], None
        for bit in bits:
            if bundle is None:
                bundle = cls._Create(bit)
            elif bundle.type is bit.type:
                if bit.is_const or bit.is_open:
                    bundle = bundle._replace(high = prev.high + 1)
                elif (bit.index == bundle.high + 1 and bit.parent is bundle.bus):
                    bundle = bundle._replace(high = bundle.high + 1)
                else:
                    list_.append(bundle)
                    bundle = cls._Create(bit)
            else:
                list_.append(bundle)
                bundle = cls._Create(bit)
        list_.append(bundle)
        return list_

# ----------------------------------------------------------------------------
# -- NetReference ------------------------------------------------------------
# ----------------------------------------------------------------------------
class NetReference(namedtuple('NetReference_namedtuple', 'type instance pin low high'), AbstractNet):
    """Helper class used to bundle individual port/pin bits back to slices.
    
    Args:
        type (`NetType`): type of this reference
        instance (:obj:`str`): the parent instance. Use None if the parent is a block
        pin (:obj:`str`): the pin (or port) these nets belong to
        low, high (:obj:`int`): the LSB and MSB of the reference
    """

    @classmethod
    def _From_bundle(cls, bundle):
        """Create a reference from a `NetBundle`."""
        return cls(bundle.type,
                bundle.bus.parent_instance if bundle.type is NetType.pin else None,
                bundle.low, bundle.high)

    @classmethod
    @regex("^(?:(?:1'b(?P<const>[01]))|"
            "(?:(?:(?P<instance>\w[\w\d]*)\.)?(?P<pin>\w[\w\d]*)(?:\[(?P<index>\d+)\])?))$")
    def _Parse_net(cls, d, s, e):
        """Parse a single bit net reference.

        Args:
            s (:obj:`str`): the string to be parsed

        Returns:
            `NetReference`: the parsed net reference

        Raises:
            `PRGAInternalError`: if the string is not a valid string
        """
        if d is None:
            raise PRGAInternalError("'{}' does not match with regexp '{}'"
                    .format(s, e))
        if 'const' in d:
            return cls(NetType.zero if d['const'] == '0' else NetType.one, None, None, None, 1)
        else:
            return cls(NetType.pin if 'instance' in d else NetType.port,
                    d.get('instance', None), d['pin'], int(d.get('index', 0)), int(d.get('index', 0)))

    @classmethod
    @regex("^(?:(?:(?P<width>[1-9]\d*)'b(?P<const>[01]))|"
            "(?:(?:(?P<instance>\w[\w\d]*)\.)?(?P<pin>\w[\w\d]*)(?:\[(?:(?P<high>\d+):)?(?P<low>\d+)\])?))$")
    def _Parse_nets(cls, d, s, e):
        """Parse a multi bit net reference.

        Args:
            s (:obj:`str`): the string to be parsed

        Returns:
            `NetReference`: the parsed net reference

        Raises:
            `PRGAInternalError`: if the string is not a valid string
        """
        if d is None:
            raise PRGAInternalError("'{}' does not match with regexp '{}'"
                    .format(s, e))
        if 'const' in d:
            return cls(NetType.zero if d['const'] == '0' else NetType.one, None, None, None, int(d['width']))
        else:
            low = int(d['low']) if 'low' in d else None
            high = int(d['high']) if 'high' in d else low
            return cls(NetType.pin if 'instance' in d else NetType.port,
                    d.get('instance', None), d['pin'], low, high)
