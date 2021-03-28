import pydantic
import pytest
from pydantic import StrictStr

from sdmx.util import BaseModel, DictLike, validate_dictlike


class TestDictLike:
    @pytest.fixture
    def Foo(self):
        # Example class
        @validate_dictlike
        class Foo(BaseModel):
            items: DictLike[StrictStr, int] = DictLike()

        yield Foo

    def test_init(self):
        # NB use with "assert False" in DictLike.__setitem__
        DictLike(foo=1)
        DictLike((("foo", 1),))
        DictLike(dict(foo=1))

    def test_class(self):
        dl = DictLike()

        # Set by item name
        dl["TIME_PERIOD"] = 3
        dl["CURRENCY"] = "USD"

        # Access by attribute name
        assert dl.TIME_PERIOD == 3

        # Access by item index
        assert dl[1] == "USD"

        # Access beyond index
        with pytest.raises(KeyError):
            dl["FOO"]

        with pytest.raises(IndexError):
            dl[2]

        with pytest.raises(AttributeError):
            dl.FOO

        # copy() returns same class
        copied = dl.copy()
        assert isinstance(copied, DictLike)
        assert copied.TIME_PERIOD == dl.TIME_PERIOD

    def test_validate_dictlike(self, Foo):
        """``@validate_dictlike()`` adds a validator to a pydantic model field."""
        assert 1 <= len(Foo.__fields__["items"].post_validators)
        assert "_validate_whole" == Foo.__fields__["items"].post_validators[0].func_name

        # ValidationError
        f = Foo()
        with pytest.raises(pydantic.ValidationError, match="not a valid dict"):
            f.items = {"bar", "baz"}

    def test_validation(self, Foo):
        f = Foo()
        assert type(f.items) is DictLike

        # Can be set with DictLike
        f.items = DictLike(a=1, b=2)
        assert type(f.items) is DictLike

        # Can be set with dict()
        f.items = {"a": 1, "b": 2}
        assert type(f.items) is DictLike

        # Type checking on creation
        with pytest.raises(pydantic.ValidationError):
            f = Foo(items={1: "a"})

        # Type checking on assignment
        f = Foo()
        with pytest.raises(pydantic.ValidationError):
            f.items = {1: "a"}

        # Type checking on setting elements
        f = Foo(items={"a": 1})
        with pytest.raises(pydantic.ValidationError):
            f.items[123] = 456

        # commented: this does not work, since validate_dictlike does not operate
        # until initial values are assigned to the field
        # f = Foo()
        # with pytest.raises(pydantic.ValidationError):
        #     f.items[123] = 456

        # Use validate_dictlike() twice
        @validate_dictlike
        class Bar(BaseModel):
            elems: DictLike[StrictStr, float] = DictLike()
