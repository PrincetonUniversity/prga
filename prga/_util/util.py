# -*- enconding: ascii -*-

"""Utilities and helpers."""

__all__ = ['regex', 'DictProxy', 'uno']

import logging
_logger = logging.getLogger(__name__)

from mmh3 import hash64
import re
from itertools import ifilter
from copy import copy
from collections import Mapping

class regex(object):
    """A decorator class for simpler regexp processing.

    Args:
        pattern (:obj:`str`): the regexp pattern

    The constructor of this decorator class takes a string as the regexp pattern and constructs a decorator object
    which holds the compiled regexp program. The decorator object should be used to decorate a method which process
    the sub-strings extracted from a matched string. After decoration, a method is returned that can be used to
    match and process any string using the regexp pattern and the post-matching processing method.

    The decorated method must be a class member method or a :obj:`classmethod`, and must follow the format below:

        ``def f(self, dict_, string, pattern, *args, **kwargs)``

            * ``dict_`` is a :obj:`dict` object which contains all matched
              `symbolic group <https://docs.python.org/2/library/re.html>`_
            * ``string`` is the raw string passed into the decorated method
            * ``pattern`` is the regexp pattern
            * Any other positional and/or keyword arguments may be placed after the 4 arguments.

    The returned method is then callable as:

        ``def f(self, string, *args, **kwargs)``

    Example:
        >>> class SomeClass(object):
        ...     @classmethod
        ...     @regex("^(?P<i>\d+)(?:\.(?P<j>\d+))?$")
        ...     def foo(cls, dict_, string, pattern):
        ...         if dict_ is None:
        ...             print "'{}' does not match with regexp: '{}'".format(string, pattern)
        ...         else:
        ...             print dict_['i'], dict_.get('j', None)
        >>> SomeClass.regex('4.5')
        4 5
        >>> SomeClass.regex('4')
        4 None
        >>> SomeClass.regex('blah')
        "'blah' does not match with regexp: '^(?P<i>\d+)(?:\.(?P<j>\d+))?$'"

    """
    def __init__(self, pattern):
        self.__pattern = pattern
        self.__prog = re.compile(pattern)

    def __call__(self, f):
        def wrapped(obj, s, *args, **kwargs):
            matched = self.__prog.match(s)
            if matched is None:
                return f(obj, None, s, self.__pattern, *args, **kwargs)
            d = matched.groupdict()
            d = dict((k, v) for k, v in d.items() if v)
            return f(obj, d, s, self.__pattern, *args, **kwargs)
        wrapped.__doc__ = f.__doc__
        return wrapped

class DictProxy(Mapping):
    """A read-only proxy of a :obj:`dict` object.

    Args:
        d (:obj:`dict`): the :obj:`dict` object to be proxied
        filter (``lambda (key, value) -> bool``, default=None): an optional filter which filters the :obj:`dict` items

    A read-only proxy of a :obj:`dict` object. All read-only methods of :obj:`dict` are implemented while all mutating methods
    are removed.
    """
    def __init__(self, d, filter=None):
        self.__d = d
        self.__filter = filter

    def __len__(self):
        """Return the number of items in the filtered dictionary."""
        if self.__filter is None:
            return len(self.__d)
        else:
            return sum(1 for _ in ifilter(self.__filter, self.__d.iteritems()))

    def __getitem__(self, key):
        """Return the item with key *key* in the filtered dictionary.
        
        Args:
            key (:obj:`str`):

        Raises:
            `KeyError`: if *key* is not in the filtered dictionary.
        """
        try:
            value = self.__d[key]
        except KeyError:
            raise KeyError(key)
        if self.__filter is not None and not self.__filter((key, value)):
            raise KeyError(key)
        else:
            return value

    def __iter__(self):
        """Return an iterator over the keys of the filtered dictionary."""
        if self.__filter is None:
            return iter(self.__d)
        else:
            return iter(k for k, _ in ifilter(self.__filter, self.__d.iteritems()))

    def iteritems(self):
        """Return an iterator over the filtered (key, value) pairs."""
        if self.__filter is None:
            return self.__d.iteritems()
        else:
            return ifilter(self.__filter, self.__d.iteritems())

    def iterkeys(self):
        """Return an iterator over the keys of the filtered dictionary."""
        return iter(self)

    def itervalues(self):
        """Return an iterator over the values of the filtered dictionary."""
        if self.__filter is None:
            return self.__d.itervalues()
        else:
            return iter(v for _, v in ifilter(self.__filter, self.__d.iteritems()))

def uno(*args):
    """Return the first non- None value of the arguments

    Args:
        *args: variable positional arguments

    Returns:
        The first non- None value or None

    """
    try:
        return next(ifilter(lambda x: x is not None, args))
    except StopIteration:
        return None

def phash(obj):
    """Return a positive hash value of ``obj``"""
    return hash64(str(obj), 0xdeadbeef, signed = False)[0]
