import logging
import typing
from collections import OrderedDict
from enum import Enum
from functools import lru_cache
from typing import Any, Mapping, Tuple, TypeVar, Union

import pydantic
from pydantic import DictError, Extra, ValidationError, validator  # noqa: F401
from pydantic.class_validators import make_generic_validator

KT = TypeVar("KT")
VT = TypeVar("VT")

log = logging.getLogger(__name__)


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


class DictLike(OrderedDict, typing.MutableMapping[KT, VT]):
    """Container with features of a dict & list, plus attribute access."""

    def __getitem__(self, key: Union[KT, int]) -> VT:
        try:
            return super().__getitem__(key)
        except KeyError:
            if isinstance(key, int):
                return list(self.values())[key]
            elif isinstance(key, str) and key.startswith("__"):
                raise AttributeError
            else:
                raise

    def __setitem__(self, key: KT, value: VT) -> None:
        key = self._apply_validators("key", key)
        value = self._apply_validators("value", value)
        super().__setitem__(key, value)

    # Access items as attributes
    def __getattr__(self, name) -> VT:
        try:
            return self.__getitem__(name)
        except KeyError as e:
            raise AttributeError(*e.args) from None

    def validate(cls, value, field):
        if not isinstance(value, (dict, DictLike)):
            raise ValueError(value)

        result = DictLike()
        result.__fields = {"key": field.key_field, "value": field}
        result.update(value)
        return result

    def _apply_validators(self, which, value):
        try:
            field = self.__fields[which]
        except AttributeError:
            return value
        result, error = field._apply_validators(
            value, validators=field.validators, values={}, loc=(), cls=None
        )
        if error:
            raise ValidationError([error], self.__class__)
        else:
            return result

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


def validate_dictlike(*fields):
    def decorator(cls):
        v = make_generic_validator(DictLike.validate)
        for field in fields:
            cls.__fields__[field].post_validators = [v]
        return cls

    return decorator


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
