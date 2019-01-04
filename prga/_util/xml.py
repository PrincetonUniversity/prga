# -*- encoding: ascii -*-

"""A XML generator based on lxml.etree."""

__all__ = ['XMLGenerator']

import logging
_logger = logging.getLogger(__name__)

from util import uno

import lxml.etree as et
from collections import Mapping

# ----------------------------------------------------------------------------
# -- XMLGenerator ------------------------------------------------------------
# ----------------------------------------------------------------------------
class XMLGenerator(object):
    """A XML Generator based on lxml.etree.

    Args:
        f (file-like object): the output stream
    """
    def __init__(self, f):
        self.__f = f

    def __enter__(self):
        self.__context = et.xmlfile(self.__f, encoding='ascii')
        self._xf = self.__context.__enter__()
        self._depth = 0
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.__context.__exit__(exc_type, exc_value, traceback)

    def _indent(self):
        if self._depth > 0:
            self._xf.write('\t' * self._depth)

    def _newline(self):
        if self._depth > 0:
            self._xf.write('\n')

    class __XMLElementContextManager(object):
        """Context manager for an XML element."""
        def __init__(self, generator, tag, attrs):
            self.__gen = generator
            self.__tag = tag
            self.__attrs = attrs

        def __enter__(self):
            self.__gen._indent()
            self.__gen._depth += 1
            self.__context = self.__gen._xf.element(self.__tag, self.__attrs)
            ret = self.__context.__enter__()
            self.__gen._newline()
            return ret

        def __exit__(self, exc_type, exc_value, traceback):
            self.__gen._depth -= 1
            self.__gen._indent()
            ret = self.__context.__exit__(exc_type, exc_value, traceback)
            self.__gen._newline()
            return ret

    def element(self, tag, attrs = None):
        return self.__XMLElementContextManager(self, tag, {k: str(v) for k, v in uno(attrs, {}).iteritems()})

    def element_leaf(self, tag, dict_ = None):
        dict_ = uno(dict_, {})
        attrs = {k: str(v) for k, v in dict_.iteritems() if not k.startswith('@') and k != '#text'}
        text = str(dict_.get('#text', ''))
        children = {k[1:]: v for k, v in dict_.iteritems() if k.startswith('@')}
        self._indent()
        with self._xf.element(tag, attrs):
            if len(text) > 0:
                self._xf.write(text)
            elif len(children) > 0:
                self._depth += 1
                self._newline()
                for k, v in children.iteritems():
                    if isinstance(v, Mapping):
                        v = [v]
                    for vv in v:
                        self.element_leaf(k, vv)
                self._depth -= 1
                self._indent()
        self._newline()
