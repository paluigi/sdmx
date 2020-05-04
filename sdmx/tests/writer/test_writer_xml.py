import pytest
import sdmx
from sdmx.message import StructureMessage


def test_codelist(codelist):
    sdmx.to_xml(codelist)


def test_not_implemented():
    msg = StructureMessage()

    with pytest.raises(NotImplementedError,
                       match='write StructureMessage to XML'):
        sdmx.to_xml(msg)
