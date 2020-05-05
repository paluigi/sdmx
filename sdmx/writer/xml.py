from lxml import etree
from lxml.builder import ElementMaker

from sdmx import message, model
from sdmx.format.xml import NS, qname
import sdmx.urn
from sdmx.writer.base import BaseWriter


_element_maker = ElementMaker(nsmap=NS)


def Element(name, *args, **kwargs):
    return _element_maker(qname(*name.split(':')), *args, **kwargs)


Writer = BaseWriter('XML')


def write(obj, **kwargs):
    """Convert an SDMX *obj* to SDMX-ML.

    Parameters
    ----------
    kwargs
        Passed to :meth:`lxml.etree.to_string`, e.g. `pretty_print` =
        :obj:`True`.

    Raises
    ------
    NotImplementedError
        If writing specific objects to SDMX-ML has not been implemented in
        :mod:`sdmx`.
    """
    return etree.tostring(Writer.recurse(obj), **kwargs)


# Utility functions

def nameable(obj, elem):
    for locale, label in obj.name.localizations.items():
        child = Element('com:Name', label)
        child.set(qname('xml', 'lang'), locale)
        elem.append(child)


def maintainable(obj):
    urn = sdmx.urn.make(obj)
    elem = Element(f'str:{obj.__class__.__name__}', urn=urn)
    nameable(obj, elem)
    return elem


@Writer.register
def _(obj: message.StructureMessage):
    msg = Element('mes:Structure')

    # Empty header element
    msg.append(Element('mes:Header'))

    structures = Element('mes:Structures')
    msg.append(structures)

    codelists = Element('mes:Codelists')
    structures.append(codelists)
    codelists.extend(Writer.recurse(cl) for cl in obj.codelist.values())

    return msg


@Writer.register
def _(obj: model.ItemScheme):
    elem = maintainable(obj)
    elem.extend(Writer.recurse(i, parent=obj) for i in obj.items.values())
    return elem


@Writer.register
def _(obj: model.Item, parent):
    # NB this isn't correct: produces .Codelist instead of .Code
    elem = Element(
        f'str:{obj.__class__.__name__}',
        id=obj.id,
        urn=sdmx.urn.make(obj, parent),
    )
    nameable(obj, elem)
    return elem
