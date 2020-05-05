import pytest
import sdmx
from sdmx.message import DataMessage


def test_codelist(tmp_path, codelist):
    result = sdmx.to_xml(codelist, pretty_print=True)
    print(result.decode())


def test_structuremessage(tmp_path, structuremessage):
    result = sdmx.to_xml(structuremessage, pretty_print=True)
    print(result.decode())

    # Message can be round-tripped to/from file
    path = tmp_path / 'output.xml'
    path.write_bytes(result)
    msg = sdmx.read_sdmx(path)

    # Contents match the original object
    assert (
        msg.codelist['CL_COLLECTION']['A'].name['en']
        == structuremessage.codelist['CL_COLLECTION']['A'].name['en']
    )


def test_not_implemented():
    msg = DataMessage()

    with pytest.raises(NotImplementedError,
                       match='write DataMessage to XML'):
        sdmx.to_xml(msg)
