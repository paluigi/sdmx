"""SDMXML v2.1 reader."""
import logging
import re
from collections import defaultdict
from copy import copy
from itertools import chain, product
from operator import itemgetter
from sys import maxsize
from typing import Union

from lxml import etree
from lxml.etree import QName

import sdmx.urn
from sdmx import message, model
from sdmx.exceptions import XMLParseError  # noqa: F401
from sdmx.format.xml import MESSAGE, qname
from sdmx.reader import BaseReader

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


TO_SNAKE_RE = re.compile("([A-Z]+)")


def add_localizations(target, values):
    """Add localized strings from *values* to *target*."""
    if isinstance(values, tuple) and len(values) == 2:
        values = [values]
    target.localizations.update({locale: label for locale, label in values})


def setdefault_attrib(target, elem, *names):
    try:
        for name in names:
            try:
                target.setdefault(to_snake(name), elem.attrib[name])
            except KeyError:
                pass
    except AttributeError:
        pass


def to_snake(value):
    """Convert *value* from lowerCamelCase to snake_case."""
    return TO_SNAKE_RE.sub(r"_\1", value).lower()


def get_sdmx_class(elem_or_name: Union[etree.Element, str], package=None):
    try:
        name = QName(elem_or_name).localname
    except ValueError:
        name = elem_or_name
    name = {
        "Attribute": "DataAttribute",
        "Dataflow": "DataflowDefinition",
        "DataStructure": "DataStructureDefinition",
        "GroupDimension": "Dimension",
        "ObsKey": "Key",
        "Receiver": "Agency",
        "Sender": "Agency",
        "Source": "Agency",
    }.get(name, name)
    return model.get_class(name, package)


def to_tags(*args):
    return chain(*[[qname(tag) for tag in arg.split()] for arg in args])


SKIP = (
    "com:Annotations com:Footer footer:Message "
    # Key and observation values
    "gen:ObsDimension gen:ObsValue gen:Value "
    # Tags that are bare containers for other XML elements
    "str:Categorisations str:CategorySchemes str:Codelists str:Concepts "
    "str:ConstraintAttachment str:Constraints str:Dataflows "
    "str:DataStructureComponents str:DataStructures str:None str:OrganisationSchemes "
    "str:ProvisionAgreements "
    # Contents of references
    ":Ref :URN"
)


PARSE = {k: None for k in product(to_tags(SKIP), ["start", "end"])}


def start(*args, only=True):
    def decorator(func):
        for tag in to_tags(*args):
            PARSE[tag, "start"] = func
            if only:
                PARSE[tag, "end"] = None
        return func

    return decorator


def end(*args, only=True):
    def decorator(func):
        for tag in to_tags(*args):
            PARSE[tag, "end"] = func
            if only:
                PARSE[tag, "start"] = None
        return func

    return decorator


def matching_class(cls):
    return lambda item: isinstance(item, type) and issubclass(item, cls)


def matching_class0(cls):
    return lambda item: isinstance(item[0], type) and issubclass(item[0], cls)


class NotReference(Exception):
    pass


class Reference:
    """Temporary class for references.

    - id, cls, and version are always the ID for a MaintainableArtefact.
    - If the target is maintainable, child_id and child_cls are identical to id
      and version, respectively. Otherwise, they describe the targeted object.
    """

    def __init__(self, elem, cls_hint=None):
        try:
            # Use the first child
            elem = elem[0]
        except IndexError:
            raise NotReference

        if cls_hint:
            cls_hint = get_sdmx_class(cls_hint)

        if elem.tag == "Ref":
            match = None
            child_id = elem.attrib["id"]
            id = elem.attrib.get("maintainableParentID", None)
            version = elem.attrib.get("maintainableParentVersion", None)

            try:
                child_cls = get_sdmx_class(
                    elem.attrib["class"], elem.attrib["package"],
                )
            except KeyError:
                try:
                    child_cls = get_sdmx_class(elem.getparent())
                except KeyError:
                    child_cls = cls_hint

        elif elem.tag == "URN":
            match = sdmx.urn.match(elem.text)
            child_cls = get_sdmx_class(match["class"], match["package"])
            child_id = match["id"]
            id = match["id"]
            version = match["version"]
        else:
            raise NotReference

        if cls_hint and issubclass(cls_hint, child_cls):
            child_cls = cls_hint

        self.maintainable = issubclass(child_cls, model.MaintainableArtefact)

        if self.maintainable:
            cls, id = child_cls, child_id
        else:
            # Non-maintainable child of a MaintainableArtefact
            cls = model.parent_class(child_cls)

            if match:
                # Use the ID of the item from the URN
                child_id = match["item_id"]

        # Store
        self.child_cls = child_cls
        self.child_id = child_id
        self.cls = cls
        self.id = id
        self.version = version

    def __str__(self):
        return "{0.cls} {0.id} {0.version} / {0.child_cls} {0.child_id}".format(self)


class Reader(BaseReader):
    _ss_missing_dsd = False

    def read_message(self, source, dsd=None):
        self.stack = defaultdict(list)

        self._ss_missing_dsd = False

        self.ignore = set([id(dsd)])

        self.push(dsd)

        try:
            for event, element in etree.iterparse(source, events=("start", "end")):
                try:
                    func = PARSE[element.tag, event]
                except KeyError:
                    # Fail immediately
                    raise NotImplementedError(element.tag, event) from None

                try:
                    result = func(self, element)
                except TypeError:
                    if func is None:
                        continue
                    else:
                        raise
                else:
                    self.push(result)
                    if event == "end":
                        element.clear()

        except Exception as exc:
            self._dump()
            raise XMLParseError from exc
            # raise

        # Count only non-ignored items
        uncollected = -1
        for key, objects in self.stack.items():
            uncollected += sum([1 if id(o) not in self.ignore else 0 for o in objects])

        if uncollected > 0:
            self._dump()
            raise RuntimeError(f"{uncollected} uncollected items")

        return self.get(message.Message)

    def _clean(self):
        for key in list(self.stack.keys()):
            if len(self.stack[key]) == 0:
                self.stack.pop(key)

    def _dump(self):
        self._clean()
        print("\n\n")
        for key, values in self.stack.items():
            print(key, values)

    def push(self, *args):
        """Push an object into the appropriate stack."""
        if args[0] is None:
            return

        if len(args) == 1:
            args = (args[0].__class__, args[0])
        elif len(args) == 2 and isinstance(args[0], etree._Element):
            args = (QName(args[0]).localname, args[1])
        elif len(args) > 2:
            raise ValueError(args)

        self.stack[args[0]].append(args[1])

    def stash(self, *keys):
        self.stack["_stash"].append({k: self.pop_all(k, strict=True) for k in keys})

    def unstash(self):
        try:
            for key, values in self.stack["_stash"].pop(-1).items():
                self.stack[key].extend(values)
        except IndexError:
            pass

    def get(self, cls_or_name, id=None, strict=False):
        if isinstance(cls_or_name, str) or strict:
            results = self.stack.get(cls_or_name, [])
        else:
            results = chain(
                *map(
                    itemgetter(1),
                    filter(matching_class0(cls_or_name), self.stack.items()),
                )
            )

        if id:
            for obj in results:
                if obj.id == id:
                    return obj
        else:
            results = list(results)
            return None if len(results) != 1 else results[0]

    def pop_all(self, cls_or_name, strict=False):
        """Remove all instances of *cls_or_name* from the stack and return.

        Returns
        -------
        list
        """
        if isinstance(cls_or_name, str):
            return self.stack.pop(cls_or_name, [])
        else:
            cond = matching_class(cls_or_name)
            return list(
                chain(
                    *[
                        self.stack.pop(k) if cond(k) else []
                        for k in list(self.stack.keys())
                    ]
                )
            )

    def pop_single(self, cls_or_name):
        try:
            return self.stack[cls_or_name].pop(-1)
        except (IndexError, KeyError):
            return None

    def pop_resolved_ref(self, cls, cls_or_name=None):
        return self.resolve(cls, self.pop_single(cls_or_name or cls))

    def resolve(self, cls, ref):
        if not isinstance(ref, Reference):
            return ref

        assert issubclass(ref.cls, cls) or issubclass(ref.child_cls, cls)

        # log.info(f"Resolving {ref}")

        # Try to get the target directly
        result = self.get(ref.child_cls, ref.child_id)

        if result:
            # Success
            # log.info(f"Internal ref to {repr(result)}")
            pass
        elif not ref.maintainable:
            # Retrieve the parent MaintainableArtefact or create a reference
            parent = self.get(ref.cls, ref.id)

            if parent is None:
                parent = self.maintainable(
                    ref.cls, None, id=ref.id, is_external_reference=True,
                )
                self.push(parent)

            if parent.is_external_reference:
                result = None
                log.info(
                    f"Parent {repr(ref.id)} is external; cannot resolve child "
                    f"{repr(ref.child_id)}"
                )
            else:
                result = parent[ref.child_id]
                # log.info(
                #     f"Internal ref to child {repr(ref.child_id)} of {repr(ref.id)}"
                # )
        else:
            # log.info(f"External ref to {repr(ref.id)}")
            result = self.maintainable(
                ref.cls, None, id=ref.id, is_external_reference=True,
            )
            self.push(result)

        return result

    def annotable(self, cls, elem, **kwargs):
        """Create a AnnotableArtefact of `cls` from `elem` and `kwargs`.

        Collects all parsed <com:Annotation>.
        """
        if elem is not None:
            kwargs.setdefault("annotations", [])
            kwargs["annotations"].extend(self.pop_all(model.Annotation))
        return cls(**kwargs)

    def identifiable(self, cls, elem, **kwargs):
        """Create a IdentifiableArtefact of `cls` from `elem` and `kwargs`."""
        setdefault_attrib(kwargs, elem, "id")
        return self.annotable(cls, elem, **kwargs)

    def nameable(self, cls, elem, **kwargs):
        """Create a NameableArtefact of `cls` from `elem` and `kwargs`.

        Collects all parsed :class:`.InternationalString` localizations of <com:Name>
        and <com:Description>.
        """
        obj = self.identifiable(cls, elem, **kwargs)
        if elem is not None:
            add_localizations(obj.name, self.pop_all("Name"))
            add_localizations(obj.description, self.pop_all("Description"))
        return obj

    def versionable(self, cls, elem, **kwargs):
        """Create a VersionableArtefact of `cls` from `elem` and `kwargs`."""
        setdefault_attrib(kwargs, elem, "version")
        return self.nameable(cls, elem, **kwargs)

    def maintainable(self, cls, elem, **kwargs):
        """Create a MaintainableArtefact of `cls` from `elem` and `kwargs`.

        Following the SDMX-IM class hierachy, :meth:`maintainable` calls
        :meth:`versionable`, which in turn calls :meth:`nameable`, etc.
        For all of these methods:

        - Already-parsed items are only removed from the stack if `elem` is not
          :obj:`None`.
        - `kwargs` (e.g. 'id') take precedences over values retrieved from attributes
           of `elem`.
        """
        setdefault_attrib(kwargs, elem, "isExternalReference", "isFinal", "uri", "urn")
        return self.versionable(cls, elem, **kwargs)


@start(*[f"mes:{k}" for k in MESSAGE.keys() if k != "Structure"])
@start("mes:Structure", only=False)
def _message(reader, elem):
    """Start of a Message."""
    # <mes:Structure> within <mes:Header> of a data message is handled by
    # _header_structure() below.
    if getattr(elem.getparent(), "tag", None) == qname("mes", "Header"):
        return

    # With 'dsd' argument, the message should be structure-specific
    if (
        "StructureSpecific" in elem.tag
        and reader.get(model.DataStructureDefinition) is None
    ):
        log.warning(f"sdmxml.Reader got no dsd=… argument for {QName(elem).localname}")
        reader._ss_missing_dsd = True
    elif "StructureSpecific" not in elem.tag and reader.get(
        model.DataStructureDefinition
    ):
        log.warning("Ambiguous: dsd=… argument for non–structure-specific message")

    # Instantiate the message object
    cls = MESSAGE[QName(elem).localname]
    return cls()


@end("mes:Structure", only=False)
def _header_structure(reader, elem):
    """<mes:Structure> within <mes:Header> of a DataMessage."""
    # The root node of a structure message is handled by _message(), above.
    if elem.getparent() is None:
        return

    msg = reader.get(message.Message)

    # Retrieve a DSD supplied to the parser, e.g. for a structure specific message
    provided_dsd = reader.get(model.DataStructureDefinition)

    # Resolve the <com:Structure> child to a DSD, maybe is_external_reference=True
    header_dsd = reader.pop_resolved_ref(model.DataStructureDefinition, "Structure")
    # Resolve the <str:StructureUsage> child, if any, and remove it from the stack
    header_su = reader.pop_resolved_ref(object, "StructureUsage")
    reader.pop_single(model.StructureUsage)

    if provided_dsd:
        dsd = provided_dsd
    else:
        if header_su:
            su_dsd = reader.maintainable(
                model.DataStructureDefinition,
                None,
                id=header_su.id,
                maintainer=header_su.maintainer,
                version=header_su.version,
            )

        if header_dsd:
            if header_su:
                assert header_dsd == su_dsd
            dsd = header_dsd
        elif header_su:
            reader.push(su_dsd)
            dsd = su_dsd
        else:
            raise RuntimeError

        # Store as an object that won't cause a parsing error if it is left over
        reader.ignore.add(id(dsd))

    # Store
    msg.dataflow.structure = dsd

    # Store under the structure ID, so it can be looked up by that ID
    reader.push(elem.attrib["structureID"], dsd)

    try:
        # Information about the 'dimension at observation level'
        dim_at_obs = elem.attrib["dimensionAtObservation"]
    except KeyError:
        pass
    else:
        # Store
        if dim_at_obs == "AllDimensions":
            # Use a singleton object
            dim = model.AllDimensions
        elif provided_dsd:
            # Use existing dimension from the provided DSD
            dim = dsd.dimensions.get(dim_at_obs)
        else:
            # Force creation of the 'dimension at observation' level
            dim = dsd.dimensions.getdefault(
                dim_at_obs,
                cls=(
                    model.TimeDimension
                    if "TimeSeries" in elem.getparent().getparent().tag
                    else model.Dimension
                ),
                # TODO later, reduce this
                order=maxsize,
            )
        msg.observation_dimension = dim


@start("mes:DataSet", only=False)
def _ds_start(reader, elem):
    ds = model.DataSet()

    # Store a reference to the DSD that structures the data set
    id = elem.attrib.get("structureRef", None) or elem.attrib.get(
        qname("data:structureRef"), None
    )
    if id:
        ds.structured_by = reader.get(id)
    else:
        log.info("No DSD when creating DataSet {reader.stack}")

    return ds


@end("mes:DataSet", only=False)
def _ds_end(reader, elem):
    ds = reader.pop_single(model.DataSet)

    # Collect observations not grouped by SeriesKey
    ds.add_obs(reader.pop_all(model.Observation))

    # Create group references
    for obs in ds.obs:
        ds._add_group_refs(obs)

    # Add the data set to the message
    reader.get(message.Message).data.append(ds)


@end("gen:Series")
def _series(reader, elem):
    ds = reader.get(model.DataSet)
    sk = reader.pop_single(model.SeriesKey)
    sk.attrib.update(reader.pop_single("Attributes") or {})
    ds.add_obs(reader.pop_all(model.Observation), sk)


@end("gen:Group")
def _group(reader, elem):
    ds = reader.get(model.DataSet)

    gk = reader.pop_single(model.GroupKey)
    gk.attrib.update(reader.pop_single("Attributes") or {})

    # Group association of Observations is done in _ds_end()
    ds.group[gk] = []


@end("gen:Attributes")
def _avs(reader, elem):
    ad = reader.get(model.DataSet).structured_by.attributes

    result = {}
    for e in elem.iterchildren():
        da = ad.getdefault(e.attrib["id"])
        result[da.id] = model.AttributeValue(value=e.attrib["value"], value_for=da)

    reader.push("Attributes", result)


@end("gen:Obs")
def _obs(reader, elem):
    dim_at_obs = reader.get(message.Message).observation_dimension
    dsd = reader.get(model.DataSet).structured_by

    args = dict()

    for e in elem.iterchildren():
        localname = QName(e).localname
        if localname == "Attributes":
            args["attached_attribute"] = reader.pop_single("Attributes")
        elif localname == "ObsDimension":
            # Mutually exclusive with ObsKey
            args["dimension"] = dsd.make_key(
                model.Key, {dim_at_obs.id: e.attrib["value"]}
            )
        elif localname == "ObsKey":
            # Mutually exclusive with ObsDimension
            args["dimension"] = reader.pop_single(model.Key)
        elif localname == "ObsValue":
            args["value"] = e.attrib["value"]

    return model.Observation(**args)


@end(":Obs")
def _obs_ss(reader, elem):
    # StructureSpecificData message—all information stored as XML
    # attributes of the <Observation>.
    attrib = copy(elem.attrib)

    # Value of the observation
    value = attrib.pop("OBS_VALUE", None)

    # Use the DSD to separate dimensions and attributes
    dsd = reader.get(model.DataStructureDefinition)

    # Extend the DSD if the user failed to provide it
    key = dsd.make_key(model.Key, attrib, extend=reader._ss_missing_dsd)

    # Remove attributes from the Key to be attached to the Observation
    aa = key.attrib
    key.attrib = {}

    return model.Observation(dimension=key, value=value, attached_attribute=aa)


@end("gen:ObsKey gen:GroupKey gen:SeriesKey")
def _key(reader, elem):
    cls = get_sdmx_class(elem)

    kv = {e.attrib["id"]: e.attrib["value"] for e in elem.iterchildren()}

    dsd = reader.get(model.DataSet).structured_by

    return dsd.make_key(cls, kv, extend=True)


@end(":Group")
def _group_ss(reader, elem):
    ds = reader.get(model.DataSet)
    attrib = copy(elem.attrib)

    group_id = attrib.pop(qname("xsi", "type"), None)

    gk = ds.structured_by.make_key(
        model.GroupKey, attrib, extend=reader._ss_missing_dsd,
    )

    if group_id:
        # The group_id is in a format like "foo:GroupName", where "foo" is an XML
        # namespace
        ns, group_id = group_id.split(":")
        assert ns in elem.nsmap

        try:
            gk.described_by = ds.structured_by.group_dimensions[group_id]
        except KeyError:
            if not reader._ss_missing_dsd:
                raise

    ds.group[gk] = []


@end(":Series")
def _series_ss(reader, elem):
    ds = reader.get(model.DataSet)
    ds.add_obs(
        reader.pop_all(model.Observation),
        ds.structured_by.make_key(
            model.SeriesKey, elem.attrib, extend=reader._ss_missing_dsd,
        ),
    )


@end("footer:Footer")
def _footer(reader, elem):
    # Get attributes from the child <footer:Messsage>
    args = dict()
    setdefault_attrib(args, elem[0], "code", "severity")
    if "code" in args:
        args["code"] = int(args["code"])

    reader.get(message.Message).footer = message.Footer(
        text=list(map(model.InternationalString, reader.pop_all("Text"))), **args,
    )


@end("mes:Structures")
def _structures(reader, elem):
    msg = reader.get(message.Message)

    # Populate dictionaries by ID
    for attr, name in (
        ("dataflow", model.DataflowDefinition),
        ("codelist", model.Codelist),
        ("constraint", model.ContentConstraint),
        ("structure", model.DataStructureDefinition),
        ("category_scheme", model.CategoryScheme),
        ("concept_scheme", model.ConceptScheme),
        ("organisation_scheme", model.OrganisationScheme),
        ("provisionagreement", model.ProvisionAgreement),
    ):
        for obj in reader.pop_all(name):
            getattr(msg, attr)[obj.id] = obj

    # Check, but do not store, categorizations
    for c in reader.pop_all(model.Categorisation):
        log.info(" ".join(map(repr, [c, c.artefact, c.category])))


@start("str:Agency str:Code str:Category str:DataProvider", only=False)
def _item_start(reader, elem):
    try:
        if not (elem[0].tag in ("Ref", "URN")):
            # Avoid stealing the name(s) of the parent ItemScheme from the stack
            # TODO check this works for annotations
            reader.stash("Name")
    except IndexError:
        pass


@end("str:Agency str:Code str:Category str:DataProvider", only=False)
def _item(reader, elem):
    try:
        # <str:DataProvider> may be a reference, e.g. in <str:ConstraintAttachment>
        return Reference(elem)
    except NotReference:
        pass

    cls = get_sdmx_class(elem)
    item = reader.nameable(cls, elem)

    # Hierarchy is stored in two ways

    # (1) XML sub-elements of the parent. These have already been parsed.
    for e in elem:
        if e.tag == elem.tag:
            # Found 1 child XML element with same tag → claim 1 child object
            item.append_child(reader.pop_single(cls))

    # (2) through <str:Parent>
    parent = reader.pop_resolved_ref(cls, "Parent")
    if parent:
        parent.append_child(item)

    reader.unstash()
    return item


@end("str:Concept", only=True)
def _concept(reader, elem):
    concept = _item(reader, elem)
    concept.core_representation = reader.pop_single(model.Representation)
    return concept


@end("str:CoreRepresentation str:LocalRepresentation")
def _rep(reader, elem):
    return model.Representation(
        enumerated=reader.pop_resolved_ref(model.ItemScheme, "Enumeration"),
        non_enumerated=(
            reader.pop_all("EnumerationFormat") + reader.pop_all("TextFormat")
        ),
    )


@end("str:EnumerationFormat str:TextFormat")
def _facet(reader, elem):
    attrib = copy(elem.attrib)

    # Parse facet value type; SDMX-ML default is 'String'
    fvt = attrib.pop("textType", "String")

    f = model.Facet(
        # Convert case of the value. In XML, first letter is uppercase; in
        # the spec and Python enum, lowercase.
        value_type=model.FacetValueType[fvt[0].lower() + fvt[1:]],
        # Other attributes are for Facet.type, an instance of FacetType. Convert
        # the attribute name from camelCase to snake_case
        type=model.FacetType(**{to_snake(key): val for key, val in attrib.items()}),
    )
    reader.push(elem, f)


@end(
    "str:AgencyScheme str:Codelist str:ConceptScheme str:CategoryScheme "
    "str:DataProviderScheme",
)
def _itemscheme(reader, elem):
    cls = get_sdmx_class(elem)

    # Iterate over all Item objects *and* their children
    iter_all = chain(*[iter(item) for item in reader.pop_all(cls._Item)])
    # Set of objects already added to `items`
    seen = dict()
    # Flatten the list
    items = [seen.setdefault(i, i) for i in iter_all if i not in seen]

    return reader.maintainable(cls, elem, items=items)


@end("com:Annotation")
def _a(reader, elem):
    args = dict(
        title=reader.pop_single("AnnotationTitle"),
        type=reader.pop_single("AnnotationType"),
        url=reader.pop_single("AnnotationURL"),
    )

    # Optional 'id' attribute
    setdefault_attrib(args, elem, "id")

    a = model.Annotation(**args)
    add_localizations(a.text, reader.pop_all("AnnotationText"))

    return a


@end("mes:Header")
def _header(reader, elem):
    # Attach to the Message
    header = message.Header(
        id=reader.pop_single("ID") or None,
        prepared=reader.pop_single("Prepared") or None,
        receiver=reader.pop_single("Receiver"),
        sender=reader.pop_single("Sender") or None,
        test=str(reader.pop_single("Test")).lower() == "true",
    )
    add_localizations(header.source, reader.pop_all("Source"))

    reader.get(message.Message).header = header

    # TODO check whether these occur anywhere besides footer.xml
    reader.pop_all("Timezone")
    reader.pop_all("DataSetAction")
    reader.pop_all("DataSetID")


@end(
    "mes:DataSetAction mes:DataSetID mes:ID mes:Prepared mes:Test mes:Timezone "
    "com:AnnotationType com:AnnotationTitle com:AnnotationURL com:Email com:None "
    "com:Telephone com:URI com:URN com:Value"
)
def _text(reader, elem):
    reader.push(elem, elem.text)


@end("mes:Receiver mes:Sender")
def _header_org(reader, elem):
    reader.push(elem, reader.nameable(get_sdmx_class(elem), elem))


@end(
    "com:AnnotationText com:Name com:Department com:Description com:Role com:Text "
    "mes:Source"
)
def _localization(reader, elem):
    reader.push(
        elem, (elem.attrib.get(qname("xml:lang"), model.DEFAULT_LOCALE), elem.text)
    )


@end(
    # in <mes:Header> of structure-specific data message
    "com:Structure "
    # in <mes:Header>/<mes:Structure> of generic data message
    "com:StructureUsage str:AttachmentGroup str:ConceptIdentity str:DimensionReference"
    " str:Parent str:Source "
    # In e.g. <str:Dataflow>
    "str:Structure str:Target str:Enumeration"
)
def _ref(reader, elem):
    localname = QName(elem).localname

    # Certain XML elements always point to certain classes
    cls_hint = {
        "AttachmentGroup": "GroupDimensionDescriptor",
        "DimensionReference": "Dimension",
        "Parent": QName(elem.getparent()).localname,
        "Structure": "DataStructureDefinition",
    }.get(localname, None)

    reader.push(localname, Reference(elem, cls_hint))


@end(
    "str:Attribute str:Dimension str:GroupDimension str:MeasureDimension "
    "str:PrimaryMeasure str:TimeDimension"
)
def _component(reader, elem):
    try:
        # May be a reference
        return Reference(elem)
    except NotReference:
        pass

    # Object class: {,Measure,Time}Dimension or DataAttribute
    cls = get_sdmx_class(elem)

    args = dict(
        concept_identity=reader.pop_resolved_ref(model.Concept, "ConceptIdentity"),
        local_representation=reader.pop_single(model.Representation),
    )
    try:
        args["order"] = int(elem.attrib["position"])
    except KeyError:
        pass

    # DataAttribute only
    ar = reader.pop_all(model.AttributeRelationship)
    if len(ar):
        assert len(ar) == 1
        args["related_to"] = ar[0]

    return reader.identifiable(cls, elem, **args)


@end("str:AttributeRelationship")
def _ar(reader, elem):
    # Retrieve the current DSD
    dsd = reader.get(model.DataStructureDefinition)

    if "None" in elem[0].tag:
        return model.NoSpecifiedRelationship()

    # Iterate over the stack of parsed references
    args = dict(dimensions=list())
    for ref in reader.pop_all(Reference, strict=True):
        # Use the <Ref id="..."> to retrieve a Component from the DSD
        try:
            if issubclass(ref.child_cls, model.DimensionComponent):
                component = dsd.dimensions.get(ref.child_id)
                args["dimensions"].append(component)
            elif issubclass(ref.child_cls, model.PrimaryMeasure):
                component = dsd.measures.get(ref.child_id)
                assert False
            elif ref.child_cls is model.GroupDimensionDescriptor:
                args["group_key"] = dsd.group_dimensions[ref.child_id]
        except KeyError:
            log.warning(f"Not implemented: forward ref to {str(ref)}")

    ref = reader.pop_single("AttachmentGroup")
    if ref:
        args["group_key"] = dsd.group_dimensions[ref.child_id]

    if len(args["dimensions"]):
        return model.DimensionRelationship(**args)
    else:
        args.pop("dimensions")
        return model.GroupRelationship(**args)


@end("str:AttributeList str:DimensionList str:Group str:MeasureList")
def _cl(reader, elem):
    try:
        # <str:Group> may be a reference
        return Reference(elem, cls_hint="GroupDimensionDescriptor")
    except NotReference:
        pass

    # Retrieve the DSD
    dsd = reader.get(model.DataStructureDefinition)
    if dsd is None:
        assert False

    # Retrieve the components
    args = dict(components=reader.pop_all(model.Component))

    # Determine the class
    localname = QName(elem).localname
    if localname == "Group":
        cls_name = "GroupDimensionDescriptor"
    else:
        # SDMX-ML spec for, e.g. DimensionList: "The id attribute is
        # provided in this case for completeness. However, its value is
        # fixed to 'DimensionDescriptor'."
        cls_name = elem.attrib.get("id", localname.replace("List", "Descriptor"))
        args["id"] = cls_name

    # GroupDimensionDescriptor only
    for ref in reader.pop_all("DimensionReference"):
        args["components"].append(dsd.dimensions.get(ref.child_id))

    cl = reader.identifiable(get_sdmx_class(cls_name), elem, **args)

    try:
        # DimensionDescriptor only
        cl.assign_order()
    except AttributeError:
        pass

    # Assign to the DSD eagerly for reference by next ComponentLists
    attr = {
        model.DimensionDescriptor: "dimensions",
        model.AttributeDescriptor: "attributes",
        model.MeasureDescriptor: "measures",
        model.GroupDimensionDescriptor: "group_dimensions",
    }.get(cl.__class__)
    if attr == "group_dimensions":
        getattr(dsd, attr)[cl.id] = cl
    else:
        setattr(dsd, attr, cl)


@start("str:DataStructure", only=False)
def _dsd_start(reader, elem):
    # Get an external reference, possibly created earlier
    ext_dsd = reader.get(model.DataStructureDefinition)

    # Children are not parsed at this point
    candidate = reader.maintainable(model.DataStructureDefinition, elem)

    if candidate != ext_dsd:
        reader.push(candidate)


@end("str:DataStructure", only=False)
def _dsd_end(reader, elem):
    dsd = reader.get(model.DataStructureDefinition)
    # TODO also handle annotations etc.
    add_localizations(dsd.name, reader.pop_all("Name"))


@end("str:Dataflow")
def _dfd(reader, elem):
    try:
        # <str:Dataflow> may be a reference, e.g. in <str:ConstraintAttachment>
        return Reference(elem)
    except NotReference:
        pass

    structure = reader.pop_resolved_ref(model.DataStructureDefinition, "Structure")
    if structure is None:
        log.warning(
            "Not implemented: forward reference to:\n" + etree.tostring(elem).decode()
        )
        arg = {}
    else:
        arg = dict(structure=structure)

    # Create first to collect names
    return reader.maintainable(model.DataflowDefinition, elem, **arg)


@end("str:Categorisation")
def _cat(reader, elem):
    return reader.maintainable(
        model.Categorisation,
        elem,
        artefact=reader.pop_resolved_ref(model.IdentifiableArtefact, "Source"),
        category=reader.pop_resolved_ref(model.Category, "Target"),
    )


@end("str:ContentConstraint")
def _cc(reader, elem):
    cr_str = elem.attrib["type"].lower().replace("allowed", "allowable")

    content = set()
    for ref in reader.pop_all(Reference):
        resolved = reader.resolve(model.ConstrainableArtefact, ref)
        if resolved is None:
            log.warning(
                f"Unable to resolve Content.Constraint.content reference:\n  "
                + str(ref)
            )
        else:
            content.add(resolved)

    return reader.nameable(
        model.ContentConstraint,
        elem,
        role=model.ConstraintRole(role=model.ConstraintRoleType[cr_str]),
        content=content,
        data_content_keys=reader.pop_single(model.DataKeySet),
        data_content_region=reader.pop_all(model.CubeRegion),
    )


@end("str:CubeRegion")
def _cr(reader, elem):
    return model.CubeRegion(
        included=elem.attrib["include"],
        # Combine member selections for Dimensions and Attributes
        member={ms.values_for: ms for ms in reader.pop_all(model.MemberSelection)},
    )


@end("com:Attribute com:KeyValue")
def _ms(reader, elem):
    # Values are for either a Dimension or Attribute, based on tag name
    kind = {
        "KeyValue": ("dimensions", model.Dimension),
        "Attribute": ("attributes", model.DataAttribute),
    }.get(QName(elem).localname)

    try:
        # Navigate from the current ContentConstraint to a
        # ConstrainableArtefact. If this is a DataFlow, it has a DSD, which
        # has an Attribute- or DimensionDescriptor
        cc_content = reader.stack[Reference]
        assert len(cc_content) == 1
        dfd = reader.resolve(model.ConstrainableArtefact, cc_content[0])
        cl = getattr(dfd.structure, kind[0])
    except AttributeError:
        # Failed because the ContentConstraint is attached to something,
        # e.g. DataProvider, that does not provide an association to a DSD.
        # Try to get a Component from the current scope with matching ID.
        cl = None
        component = reader.get(kind[1], id=elem.attrib["id"])
    else:
        # Get the Component
        component = cl.get(elem.attrib["id"])

    # Convert to MemberValue
    values = map(lambda v: model.MemberValue(value=v), reader.pop_all("Value"))

    if not component:
        log.warning(
            f"{cl} has no {kind[1].__name__} with ID {elem.attrib['id']}; XML element "
            "ignored and MemberValues discarded"
        )
        # Values are discarded
        return None

    return model.MemberSelection(values_for=component, values=list(values))


@end("str:DataKeySet")
def _dks(reader, elem):
    return model.DataKeySet(
        included=elem.attrib["isIncluded"],
        keys=reader.pop_all(model.DataKey)
    )


@end("str:Key")
def _dk(reader, elem):
    return model.DataKey(
        included=elem.attrib.get("isIncluded", True),
        # Convert MemberSelection/MemberValue from _ms() to ComponentValue
        key_value={
            ms.values_for: model.ComponentValue(
                value_for=ms.values_for,
                value=ms.values.pop().value,
            ) for ms in reader.pop_all(model.MemberSelection)
        },
    )
