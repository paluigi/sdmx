from lxml import etree
from lxml.builder import ElementMaker

from sdmx import message, model
from sdmx.format.xml import NS, qname
import sdmx.urn
from sdmx.writer.base import BaseWriter


_element_maker = ElementMaker(nsmap=NS)


def Element(name, *args, **kwargs):
    name = name.split(':')
    name = qname(*name) if len(name) == 2 else name[0]
    return _element_maker(name, *args, **kwargs)


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

def i11lstring(obj, name):
    """InternationalString.

    Returns a list of elements with name `name`.
    """
    elems = []

    for locale, label in obj.localizations.items():
        child = Element(name, label)
        child.set(qname('xml', 'lang'), locale)
        elems.append(child)

    return elems


def annotable(obj, name, *args, **kwargs):
    elem = Element(name, *args, **kwargs)

    if len(obj.annotations):
        e_anno = Element('com:Annotations')
        e_anno.extend(Writer.recurse(a) for a in obj.annotations)
        elem.append(e_anno)

    return elem


def identifiable(obj, name, *args, **kwargs):
    return annotable(obj, name, *args, id=obj.id, **kwargs)


def nameable(obj, name, *args, **kwargs):
    elem = identifiable(obj, name, *args, **kwargs)
    elem.extend(i11lstring(obj.name, 'com:Name'))
    return elem


def maintainable(obj, parent=None):
    return nameable(
        obj,
        f'str:{obj.__class__.__name__}',
        urn=sdmx.urn.make(obj, parent),
    )


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
    elem = maintainable(obj, parent=parent)

    if obj.parent:
        # Reference to parent code
        e_parent = Element('str:Parent')
        e_parent.append(Element('Ref', id=obj.parent.id))
        elem.append(e_parent)

    return elem


@Writer.register
def _(obj: model.Annotation):
    elem = Element('com:Annotation')
    if obj.id:
        elem.attrib['id'] = obj.id
    elem.extend(i11lstring(obj.text, 'com:AnnotationText'))
    return elem
