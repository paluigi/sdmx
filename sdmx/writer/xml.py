from lxml import etree
from lxml.builder import ElementMaker

from sdmx.format.xml import NS, qname
from sdmx.model import Codelist, ItemScheme
import sdmx.urn


_ALIAS = {
    Codelist: ItemScheme,
}

E = ElementMaker(nsmap=NS)


def write(obj, *args, **kwargs):
    """Convert an SDMX *obj* to XML.

    Implements a dispatch pattern according to the type of *obj*. For instance,
    a :class:`.DataSet` object is converted using :func:`.write_dataset`. See
    individual ``write_*`` methods named for more information on their
    behaviour, including accepted *args* and *kwargs*.
    """
    return etree.tostring(_write(obj, *args, **kwargs), pretty_print=True)


def _write(obj, *args, **kwargs):
    """Helper for :meth:`write`; returns :class:`lxml.Element` object(s)."""
    cls = obj.__class__
    func_name = 'write_' + _ALIAS.get(cls, cls).__name__.lower()
    try:
        func = globals()[func_name]
    except KeyError:
        raise NotImplementedError(f'write {obj.__class__.__name__} to XML')
    else:
        return func(obj, *args, **kwargs)


def write_nameableartefact(obj, elem):
    for locale, label in obj.name.localizations.items():
        child = E(qname('com', 'Name'), label)
        child.set(qname('xml', 'lang'), locale)
        elem.append(child)


def write_maintainableartefact(obj):
    urn = sdmx.urn.make(obj)
    elem = E(qname('str', obj.__class__.__name__), urn=urn)
    write_nameableartefact(obj, elem)
    return elem


def write_itemscheme(obj):
    elem = write_maintainableartefact(obj)
    elem.extend(write_item(i, parent_elem=elem) for i in obj.items.values())
    return elem


def write_item(obj, parent_elem):
    # NB this isn't correct: produces .Codelist instead of .Code
    elem = E(qname('str', 'Code'), urn=f"{parent_elem.attrib['urn']}.{obj.id}")
    write_nameableartefact(obj, elem)
    return elem
