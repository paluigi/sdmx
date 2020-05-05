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


def write(obj, *args, **kwargs):
    pp = kwargs.pop('pretty_print', True)
    tree = Writer.recurse(obj, *args, **kwargs)
    return etree.tostring(
        tree,
        pretty_print=pp,
    )


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
    msg = Element('mes:StructureMessage')
    structures = Element('mes:Structures')
    msg.append(structures)

    codelists = Element('mes:Codelists')
    structures.append(codelists)
    codelists.extend(Writer.recurse(cl) for cl in obj.codelist.values())

    return msg


@Writer.register
def _(obj: model.ItemScheme):
    elem = maintainable(obj)
    elem.extend(Writer.recurse(i, parent_elem=elem)
                for i in obj.items.values())
    return elem


@Writer.register
def _(obj: model.Item, parent_elem):
    # NB this isn't correct: produces .Codelist instead of .Code
    elem = Element(f'str:{obj.__class__.__name__}',
                   urn=f"{parent_elem.attrib['urn']}.{obj.id}")
    nameable(obj, elem)
    return elem
