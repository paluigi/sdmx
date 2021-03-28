import logging
import typing
from enum import Enum
from functools import lru_cache
from typing import Any, Mapping, Tuple, TypeVar, Union

import pydantic
from pydantic import Field, ValidationError, validator
from pydantic.class_validators import make_generic_validator
from pydantic.typing import get_origin  # type: ignore [attr-defined]

KT = TypeVar("KT")
VT = TypeVar("VT")

log = logging.getLogger(__name__)

__all__ = [
    "BaseModel",
    "DictLike",
    "Resource",
    "compare",
    "dictlike_field",
    "summarize_dictlike",
    "validate_dictlike",
    "validator",
]


class Resource(str, Enum):
    """Enumeration of SDMX REST API endpoints.

    ====================== ================================================
    :class:`Enum` member   :mod:`sdmx.model` class
    ====================== ================================================
    ``categoryscheme``     :class:`.CategoryScheme`
    ``codelist``           :class:`.Codelist`
    ``conceptscheme``      :class:`.ConceptScheme`
    ``data``               :class:`.DataSet`
    ``dataflow``           :class:`.DataflowDefinition`
    ``datastructure``      :class:`.DataStructureDefinition`
    ``provisionagreement`` :class:`.ProvisionAgreement`
    ====================== ================================================
    """

    # agencyscheme = 'agencyscheme'
    # attachementconstraint = 'attachementconstraint'
    # categorisation = 'categorisation'
    categoryscheme = "categoryscheme"
    codelist = "codelist"
    conceptscheme = "conceptscheme"
    # contentconstraint = 'contentconstraint'
    data = "data"
    # dataconsumerscheme = 'dataconsumerscheme'
    dataflow = "dataflow"
    # dataproviderscheme = 'dataproviderscheme'
    datastructure = "datastructure"
    # hierarchicalcodelist = 'hierarchicalcodelist'
    # metadata = 'metadata'
    # metadataflow = 'metadataflow'
    # metadatastructure = 'metadatastructure'
    # organisationscheme = 'organisationscheme'
    # organisationunitscheme = 'organisationunitscheme'
    # process = 'process'
    provisionagreement = "provisionagreement"
    # reportingtaxonomy = 'reportingtaxonomy'
    # schema = 'schema'
    # structure = 'structure'
    # structureset = 'structureset'

    @classmethod
    def from_obj(cls, obj):
        """Return an enumeration value based on the class of *obj*."""
        clsname = {"DataStructureDefinition": "datastructure"}.get(
            obj.__class__.__name__, obj.__class__.__name__
        )
        return cls[clsname.lower()]

    @classmethod
    def describe(cls):
        return "{" + " ".join(v.name for v in cls._member_map_.values()) + "}"


class BaseModel(pydantic.BaseModel):
    """Common settings for :class:`pydantic.BaseModel` in :mod:`sdmx`."""

    class Config:
        copy_on_model_validation = False
        validate_assignment = True


class DictLike(dict, typing.MutableMapping[KT, VT]):
    """Container with features of a dict & list, plus attribute access."""

    __slots__ = ("__dict__", "__field")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensures attribute access to dict items
        self.__dict__ = self

        # Reference to the pydantic.field.ModelField for the entries
        self.__field = None

    def __getitem__(self, key: Union[KT, int]) -> VT:
        """:meth:`dict.__getitem__` with integer access."""
        try:
            return super().__getitem__(key)
        except KeyError:
            if isinstance(key, int):
                # int() index access
                return list(self.values())[key]
            else:
                raise

    def __setitem__(self, key: KT, value: VT) -> None:
        """:meth:`dict.__setitem` with validation."""
        super().__setitem__(*self._validate_entry(key, value))

    def __copy__(self):
        # Construct explicitly to avoid returning the parent class, dict()
        return DictLike(**self)

    def copy(self):
        """Return a copy of the DictLike."""
        return self.__copy__()

    # pydantic compat

    @classmethod
    def __get_validators__(cls):
        yield cls._validate_whole

    @classmethod
    def _validate_whole(cls, v, field: pydantic.fields.ModelField):
        """Validate `v` as an entire DictLike object."""
        # Convert anything that can be converted to a dict(). pydantic internals catch
        # most other invalid types, e.g. set(); no need to handle them here.
        result = cls(v)

        # Reference to the pydantic.field.ModelField for the entries
        result.__field = field

        return result

    def _validate_entry(self, key, value):
        """Validate one `key`/`value` pair."""
        try:
            # Use pydantic's validation machinery
            v, error = self.__field._validate_mapping_like(
                ((key, value),), values={}, loc=(), cls=None
            )
        except AttributeError:
            # .__field is not populated
            return key, value
        else:
            if error:
                raise ValidationError([error], self.__class__)
            else:
                return v.popitem()

    def compare(self, other, strict=True):
        """Return :obj:`True` if `self` is the same as `other`.

        Two DictLike instances are identical if they contain the same set of keys, and
        corresponding values compare equal.

        Parameters
        ----------
        strict : bool, optional
            Passed to :func:`compare` for the values.
        """
        if set(self.keys()) != set(other.keys()):
            log.info(f"Not identical: {sorted(self.keys())} / {sorted(other.keys())}")
            return False

        for key, value in self.items():
            if not value.compare(other[key], strict):
                return False

        return True


# Utility methods for DictLike
#
# These are defined in separate functions to avoid collisions with keys and the
# attribute access namespace, e.g. if the DictLike contains keys "summarize" or
# "validate".


def dictlike_field():
    """Shorthand for :class:`pydantic.Field` with :class:`.DictLike` default factory."""
    return Field(default_factory=DictLike)


def summarize_dictlike(dl, maxwidth=72):
    """Return a string summary of the DictLike contents."""
    value_cls = dl[0].__class__.__name__
    count = len(dl)
    keys = " ".join(dl.keys())
    result = f"{value_cls} ({count}): {keys}"

    if len(result) > maxwidth:
        # Truncate the list of keys
        result = result[: maxwidth - 3] + "..."

    return result


def validate_dictlike(cls):
    """Adjust `cls` so that its DictLike members are validated.

    This is necessary because DictLike is a subclass of :class:`dict`, and so
    :mod:`pydantic` fails to call :meth:`~DictLike.__get_validators__` and register
    those on BaseModels which include DictLike members.
    """
    # Iterate over annotated members of `cls`; only those which are DictLike
    for name, anno in filter(
        lambda item: get_origin(item[1]) is DictLike, cls.__annotations__.items()
    ):
        # Add the validator(s)
        field = cls.__fields__[name]
        field.post_validators = field.post_validators or []
        field.post_validators.extend(
            make_generic_validator(v) for v in DictLike.__get_validators__()
        )

    return cls


def compare(attr, a, b, strict: bool) -> bool:
    """Return :obj:`True` if ``a.attr`` == ``b.attr``.

    If strict is :obj:`False`, :obj:`None` is permissible as `a` or `b`; otherwise,
    """
    return getattr(a, attr) == getattr(b, attr) or (
        not strict and None in (getattr(a, attr), getattr(b, attr))
    )
    # if not result:
    #     log.info(f"Not identical: {attr}={getattr(a, attr)} / {getattr(b, attr)}")
    # return result


@lru_cache()
def direct_fields(cls) -> Mapping[str, pydantic.fields.ModelField]:
    """Return the :mod:`pydantic` fields defined on `obj` or its class.

    This is like the ``__fields__`` attribute, but excludes the fields defined on any
    parent class(es).
    """
    return {
        name: info
        for name, info in cls.__fields__.items()
        if name not in set(cls.mro()[1].__fields__.keys())
    }


try:
    from typing import get_args  # type: ignore [attr-defined]
except ImportError:

    def get_args(tp) -> Tuple[Any, ...]:
        """For Python <3.8."""
        return tp.__args__
