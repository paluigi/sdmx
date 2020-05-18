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
from sdmx.format.xml import NS, qname, tag_for_class
from sdmx.writer.base import BaseWriter

_element_maker = ElementMaker(nsmap={k: v for k, v in NS.items() if v is not None})

writer = BaseWriter("XML")


def Element(name, *args, **kwargs):
    # Remove None
    kwargs = dict(filter(lambda kv: kv[1] is not None, kwargs.items()))

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


def reference(obj, parent=None, tag=None, style="URN"):
    """Write a reference to `obj`."""
    tag = tag or tag_for_class(obj.__class__)

    elem = Element(tag)

    if style == "URN":
        ref = Element(":URN", obj.urn)
    elif style == "Ref":
        if isinstance(obj, model.MaintainableArtefact):
            ma = obj
        else:
            # TODO handle references to non-maintainable children of parent objects
            assert parent, f"Cannot write reference to {repr(obj)} without parent"
            ma = parent

        args = {
            "id": obj.id,
            "maintainableParentID": ma.id if parent else None,
            "agencyID": getattr(ma.maintainer, "id", None),
            "version": ma.version,
            "package": model.PACKAGE[obj.__class__],
            "class": etree.QName(tag_for_class(obj.__class__)).localname,
        }

        ref = Element(":Ref", **args)
    else:
        raise ValueError(style)

    elem.append(ref)
    return elem


# Writers for sdmx.message classes


@writer
def _sm(obj: message.StructureMessage):
    elem = Element("mes:Structure")

    # Empty header element
    elem.append(writer.recurse(obj.header))

    structures = Element("mes:Structures")
    elem.append(structures)

    for attr, tag in [
        # Order is important here to avoid forward references
        ("organisation_scheme", "OrganisationSchemes"),
        ("category_scheme", "CategorySchemes"),
        ("codelist", "Codelists"),
        ("concept_scheme", "Concepts"),
        ("dataflow", "Dataflows"),
        ("structure", "DataStructures"),
        ("constraint", "Constraints"),
        ("provisionagreement", "ProvisionAgreements"),
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


# Writers for sdmx.model classes
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
    elem = Element(kwargs.pop("_tag", tag_for_class(obj.__class__)), **kwargs)

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
    except (AttributeError, ValueError):
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
    return Element("str:TextFormat", textType=getattr(obj.value_type, "name", None))


@writer
def _rep(obj: model.Representation, tag):
    elem = Element(f"str:{tag}")
    if obj.enumerated:
        elem.append(reference(obj.enumerated, tag="str:Enumeration", style="URN"))
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


# §3.3: Basic Inheritance


@writer
def _component(obj: model.Component):
    elem = identifiable(obj)
    if obj.concept_identity:
        # TODO find a reference to the parent ConceptScheme
        # elem.append(reference(obj.concept_identity, style="Ref"))
        elem.append(Element("str:ConceptIdentity", "(not implemented)"))
        raise NotImplementedError(f"Write {obj.__class__.__name__} to XML")
    if obj.local_representation:
        elem.append(writer.recurse(obj.local_representation, "LocalRepresentation"))
    return elem


@writer
def _cl(obj: model.ComponentList):
    elem = identifiable(obj)
    raise NotImplementedError(f"Write {obj.__class__.__name__} to XML")
    elem.extend(writer.recurse(c) for c in obj.components)
    return elem


# §10.3: Constraints


@writer
def _cr(obj: model.CubeRegion):
    elem = Element("str:CubeRegion", include=str(obj.included).lower())
    raise NotImplementedError(f"Write {obj.__class__.__name__} to XML")
    return elem


@writer
def _cc(obj: model.ContentConstraint):
    elem = maintainable(
        obj, type=obj.role.role.name.replace("allowable", "allowed").title()
    )

    # Constraint attachment
    for ca in obj.content:
        ca_elem = Element("str:ConstraintAttachment")
        ca_elem.append(reference(ca, style="Ref"))
        elem.append(ca_elem)

    elem.extend(writer.recurse(dcr) for dcr in obj.data_content_region)
    return elem


# §5.2: Data Structure Definition


@writer
def _dsd(obj: model.DataStructureDefinition):
    elem = maintainable(obj)
    for attr in "attributes", "dimensions", "measures":
        elem.append(writer.recurse(getattr(obj, attr)))
    return elem


@writer
def _dfd(obj: model.DataflowDefinition):
    elem = maintainable(obj)
    elem.append(reference(obj.structure, style="Ref"))
    return elem
