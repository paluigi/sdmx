import re

from sdmx.model import PACKAGE


# Regular expression for URNs
URN = re.compile(r'urn:sdmx:org\.sdmx\.infomodel'
                 r'\.(?P<package>[^\.]*)'
                 r'\.(?P<class>[^=]*)=((?P<agency>[^:]*):)?'
                 r'(?P<id>[^\(\.]*)(\((?P<version>[\d\.]*)\))?'
                 r'(\.(?P<item_id>.*))?')

_BASE = (
    'urn:sdmx:org.sdmx.infomodel.{package}.{obj.__class__.__name__}='
    '{obj.maintainer.id}:{obj.id}({obj.version})'
)


def make(obj):
    return _BASE.format(obj=obj, package=PACKAGE[obj.__class__])


def match(string):
    return URN.match(string).groupdict()
