"""Stuff for Python 2.7+ and 3.3+ compatibility."""

from future.utils import with_metaclass, raise_from, iteritems, itervalues, string_types
from future.builtins import object, range

try:
    from itertools import imap as map, ifilter as filter, izip as zip
except ImportError:
    pass

try:
    from collections.abc import Sequence, MutableSequence, Mapping, MutableMapping, Hashable
except ImportError:
    from collections import Sequence, MutableSequence, Mapping, MutableMapping, Hashable

try:
    from io import BytesIO as StringIO
except ImportError:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
