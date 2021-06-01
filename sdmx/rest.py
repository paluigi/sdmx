"""Information related to the SDMX-REST web service standard."""

from enum import Enum


class Resource(str, Enum):
    """Enumeration of SDMX-REST API resources.

    ============================= ======================================================
    :class:`Enum` member          :mod:`sdmx.model` class
    ============================= ======================================================
    ``actualconstraint``          :class:`.ContentConstraint`
    ``agencyscheme``              :class:`.AgencyScheme`
    ``allowedconstraint``         :class:`.ContentConstraint`
    ``attachementconstraint``     :class:`.AttachmentConstraint`
    ``categorisation``            :class:`.Categorisation`
    ``categoryscheme``            :class:`.CategoryScheme`
    ``codelist``                  :class:`.Codelist`
    ``conceptscheme``             :class:`.ConceptScheme`
    ``contentconstraint``         :class:`.ContentConstraint`
    ``data``                      :class:`.DataSet`
    ``dataflow``                  :class:`.DataflowDefinition`
    ``dataconsumerscheme``        :class:`.DataConsumerScheme`
    ``dataproviderscheme``        :class:`.DataProviderScheme`
    ``datastructure``             :class:`.DataStructureDefinition`
    ``organisationscheme``        :class:`.OrganisationScheme`
    ``provisionagreement``        :class:`.ProvisionAgreement`
    ``structure``                 Mixed.
    ============================= ======================================================
    ``customtypescheme``          Not implemented.
    ``hierarchicalcodelist``      Not implemented.
    ``metadata``                  Not implemented.
    ``metadataflow``              Not implemented.
    ``metadatastructure``         Not implemented.
    ``namepersonalisationscheme`` Not implemented.
    ``organisationunitscheme``    Not implemented.
    ``process``                   Not implemented.
    ``reportingtaxonomy``         Not implemented.
    ``rulesetscheme``             Not implemented.
    ``schema``                    Not implemented.
    ``structureset``              Not implemented.
    ``transformationscheme``      Not implemented.
    ``userdefinedoperatorscheme`` Not implemented.
    ``vtlmappingscheme``          Not implemented.
    ============================= ======================================================
    """

    actualconstraint = "actualconstraint"
    agencyscheme = "agencyscheme"
    allowedconstraint = "allowedconstraint"
    attachementconstraint = "attachementconstraint"
    categorisation = "categorisation"
    categoryscheme = "categoryscheme"
    codelist = "codelist"
    conceptscheme = "conceptscheme"
    contentconstraint = "contentconstraint"
    customtypescheme = "customtypescheme"
    data = "data"
    dataconsumerscheme = "dataconsumerscheme"
    dataflow = "dataflow"
    dataproviderscheme = "dataproviderscheme"
    datastructure = "datastructure"
    hierarchicalcodelist = "hierarchicalcodelist"
    metadata = "metadata"
    metadataflow = "metadataflow"
    metadatastructure = "metadatastructure"
    namepersonalisationscheme = "namepersonalisationscheme"
    organisationscheme = "organisationscheme"
    organisationunitscheme = "organisationunitscheme"
    process = "process"
    provisionagreement = "provisionagreement"
    reportingtaxonomy = "reportingtaxonomy"
    rulesetscheme = "rulesetscheme"
    schema = "schema"
    structure = "structure"
    structureset = "structureset"
    transformationscheme = "transformationscheme"
    userdefinedoperatorscheme = "userdefinedoperatorscheme"
    vtlmappingscheme = "vtlmappingscheme"

    @classmethod
    def from_obj(cls, obj):
        """Return an enumeration value based on the class of *obj*."""
        clsname = {"DataStructureDefinition": "datastructure"}.get(
            obj.__class__.__name__, obj.__class__.__name__
        )
        return cls[clsname.lower()]

    @classmethod
    def class_name(cls, value, default=None):
        return {
            cls.agencyscheme: "AgencyScheme",
            cls.codelist: "Codelist",
        }.get(value, default)

    @classmethod
    def describe(cls):
        return "{" + " ".join(v.name for v in cls._member_map_.values()) + "}"
