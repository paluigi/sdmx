from functools import lru_cache

from lxml.etree import QName


# XML Namespaces
_base_ns = 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1'
NS = {
    'com': f'{_base_ns}/common',
    'data': f'{_base_ns}/data/structurespecific',
    'str': f'{_base_ns}/structure',
    'mes': f'{_base_ns}/message',
    'gen': f'{_base_ns}/data/generic',
    'footer': f'{_base_ns}/message/footer',
    'xml': 'http://www.w3.org/XML/1998/namespace',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    }


@lru_cache()
def qname(ns, name):
    """Return a fully-qualified tag *name* in namespace *ns*."""
    return QName(NS[ns], name)
