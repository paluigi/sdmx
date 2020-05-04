import pytest
import sdmx
from sdmx.message import StructureMessage
from sdmx.model import Agency, Code, Codelist


def test_codelist():
    ECB = Agency(id='ECB')
    cl = Codelist(
        id='CL_COLLECTION',
        version='1.0',
        is_final=False,
        is_external_reference=False,
        maintainer=ECB,
        name={'en': 'Collection indicator code list'},
    )
    cl.items['A'] = Code(
        id='A',
        name={'en': "Average of observations through period"},
    )
    cl.items['B'] = Code(
        id='B',
        name={'en': 'Beginning of period'},
    )

    sdmx.to_xml(cl)


def test_not_implemented():
    msg = StructureMessage()

    with pytest.raises(NotImplementedError,
                       match='write StructureMessage to XML'):
        sdmx.to_xml(msg)
