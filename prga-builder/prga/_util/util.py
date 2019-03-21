# Python 2 and 3 compatible
from prga.compatible import *

"""Utilities and helpers."""

__all__ = ['regex', 'DictDelegate', 'uno']

from prga.exception import PRGAInternalError

from mmh3 import hash64
import re
from copy import copy

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
        ...     @regex("^(?P<i>\\d+)(?:\\.(?P<j>\\d+))?$")
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
        "'blah' does not match with regexp: '^(?P<i>\\d+)(?:\\.(?P<j>\\d+))?$'"

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

class DictDelegate(Mapping):
    """A read-only delegate of a :obj:`dict` object.

    Args:
        d (:obj:`dict`): the :obj:`dict` object to be proxied
        filter_ (``lambda (key, value) -> bool``, default=None): an optional filter which filters the :obj:`dict` items

    A read-only delegate of a :obj:`dict` object. All read-only methods of :obj:`dict` are implemented while all mutating
    methods are removed.
    """
    def __init__(self, d, filter_=None):
        self.__d = d
        self.__filter = filter_

    def __len__(self):
        """Return the number of items in the filtered dictionary."""
        if self.__filter is None:
            return len(self.__d)
        else:
            return sum(1 for _ in filter(self.__filter, iteritems(self.__d)))

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
            return iter(k for k, _ in filter(self.__filter, iteritems(self.__d)))

def uno(*args):
    """Return the first non- None value of the arguments

    Args:
        *args: variable positional arguments

    Returns:
        The first non- None value or None

    """
    try:
        return next(filter(lambda x: x is not None, args))
    except StopIteration:
        return None

def phash(obj):
    """Return a positive hash value of ``obj``"""
    return hash64(str(obj), 0xdeadbeef, signed = False)[0]

class _ExtensionsDelegate(MutableMapping):
    def __init__(self, obj):
        self.__obj = obj

    def __getitem__(self, key):
        try:
            d = self.__obj.__ext
        except AttributeError:
            d = {}
        try:
            return d[key]
        except KeyError:
            try:
                return self.__obj._fixed_ext[key]
            except KeyError:
                raise

    def __setitem__(self, key, value):
        try:
            d = self.__obj.__ext
        except AttributeError:
            d = self.__obj.__ext = {}
        d[key] = value

    def __delitem__(self, key):
        del self.__obj.__ext[key]

    def __iter__(self):
        try:
            return iter(set(self.__obj.__ext) | set(self.__obj._fixed_ext))
        except AttributeError:
            return iter(self.__obj._fixed_ext)

    def __len__(self):
        try:
            return len(set(self.__obj.__ext) | set(self.__obj._fixed_ext))
        except AttributeError:
            return len(self.__obj._fixed_ext)

class ExtensibleObject(object):
    """``object`` with extensions supports."""
    @property
    def _fixed_ext(self):
        return {}

    @property
    def _ext(self):
        return _ExtensionsDelegate(self)

_registered_extensions = {}
def register_extension(extension, owner):
    """A relatively weak way to avoid extension confliction.

    Args:
        extension (:obj:`str`): name of the extension to be registered
        owner (:obj:`str`): owner of the extension. typically the ``__name__`` of a module
    """
    if extension in _registered_extensions:
        raise PRGAInternalError("Extension '{}' is already registered by '{}'"
                .format(extension, _registered_extensions[extension]))
    else:
        _registered_extensions[extension] = owner
