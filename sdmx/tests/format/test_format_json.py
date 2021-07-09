from sdmx.format import json


def test_content_types():
    assert 5 == len(json.CONTENT_TYPES)
