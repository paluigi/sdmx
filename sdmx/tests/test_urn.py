import re

import pytest

from sdmx.urn import match


def test_exception():
    urn = "urn:sdmx:org.sdmx.infomodel.codelist=BBK:CLA_BBK_COLLECTION(1.0)"
    with pytest.raises(ValueError, match=re.escape(f"not a valid SDMX URN: {urn}")):
        match(urn)
