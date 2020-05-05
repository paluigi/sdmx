import pytest
from sdmx.message import StructureMessage
from sdmx.model import Agency, Annotation, Code, Codelist


@pytest.fixture
def codelist():
    """A Codelist for writer testing."""
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
    cl.items['B1'] = Code(
        id='B1',
        name={'en': 'Child code of B'},
    )
    cl.items['B'].append_child(cl.items['B1'])

    cl.items['A'].annotations.append(Annotation(
        id='A1',
        type='NOTE',
        text={'en': 'Text annotation on Code A.'},
    ))

    return cl


@pytest.fixture
def structuremessage(codelist):
    """A StructureMessage for writer testing."""
    sm = StructureMessage()
    sm.codelist[codelist.id] = codelist

    return sm
