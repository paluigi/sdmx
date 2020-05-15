from functools import lru_cache

from lxml.etree import QName

from sdmx import message

# XML Namespaces
_base_ns = "http://www.sdmx.org/resources/sdmxml/schemas/v2_1"
NS = {
    "": None,
    "com": f"{_base_ns}/common",
    "data": f"{_base_ns}/data/structurespecific",
    "str": f"{_base_ns}/structure",
    "mes": f"{_base_ns}/message",
    "gen": f"{_base_ns}/data/generic",
    "footer": f"{_base_ns}/message/footer",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


@lru_cache()
def qname(ns_or_name, name=None):
    """Return a fully-qualified tag *name* in namespace *ns*."""
    ns, name = ns_or_name.split(":") if name is None else (ns_or_name, name)
    return QName(NS[ns], name)


# Mapping tag names → Message classes
MESSAGE = {
    "Structure": message.StructureMessage,
    "GenericData": message.DataMessage,
    "GenericTimeSeriesData": message.DataMessage,
    "StructureSpecificData": message.DataMessage,
    "StructureSpecificTimeSeriesData": message.DataMessage,
    "Error": message.ErrorMessage,
}
