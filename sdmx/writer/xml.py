"""SDMXML v2.1 writer."""
# Contents of this file are organized in the order:
#
# - Utility methods and global variables.
# - writer functions for sdmx.message classes, in the same order as message.py
# - writer functions for sdmx.model classes, in the same order as model.py


from lxml import etree
from lxml.builder import ElementMaker

import sdmx.urn
from sdmx import message, model
from sdmx.format.xml import NS, qname
from sdmx.writer.base import BaseWriter


_element_maker = ElementMaker(nsmap={k: v for k, v in NS.items() if v is not None})

writer = BaseWriter("XML")


def Element(name, *args, **kwargs):
    return _element_maker(qname(name), *args, **kwargs)


def to_xml(obj, **kwargs):
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
    return etree.tostring(writer.recurse(obj), **kwargs)


def reference(obj, tag, style="URN"):
    """Write a reference to `obj`."""
    elem = Element(tag)
    if style == "URN":
        elem.append(Element(":URN", obj.urn))
    return elem


# writers for sdmx.message classes


@writer
def _sm(obj: message.StructureMessage):
    elem = Element("mes:Structure")

    # Empty header element
    elem.append(writer.recurse(obj.header))

    structures = Element("mes:Structures")
    elem.append(structures)

    for attr, tag in [
        ("category_scheme", "CategorySchemes"),
        ("codelist", "Codelists"),
        ("concept_scheme", "Concepts"),
        # TODO extend
    ]:
        container = Element(f"str:{tag}")
        container.extend(writer.recurse(s) for s in getattr(obj, attr).values())
        structures.append(container)

    return elem


@writer
def _header(obj: message.Header):
    elem = Element("mes:Header")
    elem.append(Element("mes:Test", str(obj.test).lower()))
    if obj.id:
        elem.append(Element("mes:ID", obj.id))
    if obj.prepared:
        elem.append(Element("mes:Prepared", obj.prepared))
    if obj.sender:
        elem.append(writer.recurse(obj.sender, _tag="mes:Sender"))
    return elem


# writers for sdmx.model classes
# §3.2: Base structures


def i11lstring(obj, name):
    """InternationalString.

    Returns a list of elements with name `name`.
    """
    elems = []

    for locale, label in obj.localizations.items():
        child = Element(name, label)
        child.set(qname("xml", "lang"), locale)
        elems.append(child)

    return elems


@writer
def _a(obj: model.Annotation):
    elem = Element("com:Annotation")
    if obj.id:
        elem.attrib["id"] = obj.id
    if obj.type:
        elem.append(Element("com:AnnotationType", obj.type))
    elem.extend(i11lstring(obj.text, "com:AnnotationText"))
    return elem


def annotable(obj, **kwargs):
    elem = Element(kwargs.pop("_tag", f"str:{obj.__class__.__name__}"), **kwargs)

    if len(obj.annotations):
        e_anno = Element("com:Annotations")
        e_anno.extend(writer.recurse(a) for a in obj.annotations)
        elem.append(e_anno)

    return elem


def identifiable(obj, **kwargs):
    kwargs.setdefault("id", obj.id)
    try:
        kwargs.setdefault(
            "urn", obj.urn or sdmx.urn.make(obj, kwargs.pop("parent", None))
        )
    except ValueError:
        pass
    return annotable(obj, **kwargs)


def nameable(obj, **kwargs):
    elem = identifiable(obj, **kwargs)
    elem.extend(i11lstring(obj.name, "com:Name"))
    elem.extend(i11lstring(obj.description, "com:Description"))
    return elem


def maintainable(obj, **kwargs):
    elem = nameable(obj, **kwargs)
    # TODO add maintainer, version, etc.
    return elem


# §3.5: Item Scheme

@writer
def _i(obj: model.Item, **kwargs):
    elem = nameable(obj, **kwargs)

    if obj.parent:
        # Reference to parent Item
        e_parent = Element("str:Parent")
        e_parent.append(Element(":Ref", id=obj.parent.id))
        elem.append(e_parent)

    return elem


@writer
def _is(obj: model.ItemScheme):
    elem = maintainable(obj)
    elem.extend(writer.recurse(i, parent=obj) for i in obj.items.values())
    return elem


# §3.6: Structure


@writer
def _facet(obj: model.Facet):
    return Element("str:TextFormat", textType=obj.value_type.name)


@writer
def _rep(obj: model.Representation, tag):
    elem = Element(f"str:{tag}")
    if obj.enumerated:
        elem.append(reference(obj.enumerated, "str:Enumeration", "URN"))
    if obj.non_enumerated:
        elem.extend(writer.recurse(facet) for facet in obj.non_enumerated)
    return elem


# §4.4: Concept Scheme


@writer
def _concept(obj: model.Concept, parent):
    elem = _i(obj, parent=parent)

    if obj.core_representation:
        elem.append(writer.recurse(obj.core_representation, "CoreRepresentation"))

    return elem
