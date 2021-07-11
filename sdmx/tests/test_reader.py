import pytest

from sdmx.reader import get_reader_for_content_type


def test_get_reader_for_content_type():
    ctype = "application/x-pdf"
    with pytest.raises(
        ValueError, match=f"Content type '{ctype}' not supported by any of"
    ):
        get_reader_for_content_type(ctype)
