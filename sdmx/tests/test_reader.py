import pytest

from sdmx.reader import get_reader_for_content_type


def test_get_reader_for_content_type():
    ctype = "application/x-pdf"
    with pytest.raises(ValueError, match=f"Unsupported content type: {ctype}"):
        get_reader_for_content_type(ctype)
