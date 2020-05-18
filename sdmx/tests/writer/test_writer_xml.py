import logging

import pytest

import sdmx
from sdmx.message import DataMessage
from sdmx.tests.data import specimen


log = logging.getLogger(__name__)


def test_codelist(tmp_path, codelist):
    result = sdmx.to_xml(codelist, pretty_print=True)
    print(result.decode())


def test_structuremessage(tmp_path, structuremessage):
    result = sdmx.to_xml(structuremessage, pretty_print=True)
    print(result.decode())

    # Message can be round-tripped to/from file
    path = tmp_path / "output.xml"
    path.write_bytes(result)
    msg = sdmx.read_sdmx(path)

    # Contents match the original object
    assert (
        msg.codelist["CL_COLLECTION"]["A"].name["en"]
        == structuremessage.codelist["CL_COLLECTION"]["A"].name["en"]
    )

    # False because `structuremessage` lacks URNs, which are constructed automatically
    # by `to_xml`
    assert not msg.compare(structuremessage, strict=True)
    # Compares equal when allowing this difference
    assert msg.compare(structuremessage, strict=False)


@pytest.mark.parametrize('specimen_id, strict', [
    pytest.param(
        'ECB_EXR/1/structure-full.xml', False, marks=pytest.mark.xfail(
            raises=NotImplementedError,
            match="Write AttributeDescriptor to XML")
    ),
    # ('ISTAT/47_850-structure.xml', True),
    ('SGR/common-structure.xml', True),
])
def test_structure_roundtrip(specimen_id, strict, tmp_path):
    # Read a specimen file
    with specimen(specimen_id) as f:
        msg0 = sdmx.read_sdmx(f)

    # Write to file
    path = tmp_path / "output.xml"
    path.write_bytes(sdmx.to_xml(msg0, pretty_print=True))

    # Read again
    msg1 = sdmx.read_sdmx(path)

    # Contents are identical
    assert msg0.compare(msg1, strict), path


def test_not_implemented():
    msg = DataMessage()

    with pytest.raises(NotImplementedError, match="write DataMessage to XML"):
        sdmx.to_xml(msg)
