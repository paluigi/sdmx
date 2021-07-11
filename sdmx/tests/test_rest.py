import pytest

from sdmx import Resource


class TestResource:
    @pytest.mark.parametrize(
        "value, expected",
        [
            # Some values are mapped to different class names
            (Resource.dataflow, "DataflowDefinition"),
            (Resource.datastructure, "DataStructureDefinition"),
            # Other values pass through
            (Resource.agencyscheme, Resource.agencyscheme.value),
        ],
    )
    def test_class_name(self, value, expected):
        assert expected == Resource.class_name(value)
