"""Information related to the SDMX-REST web service standard."""
from enum import Enum

# Mapping from Resource value to class name.
CLASS_NAME = {
    "dataflow": "DataflowDefinition",
    "datastructure": "DataStructureDefinition",
}

# Inverse of :data:`CLASS_NAME`.
VALUE = {v: k for k, v in CLASS_NAME.items()}


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
    ----------------------------- ------------------------------------------------------
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
        """Return an enumeration value based on the class of `obj`."""
        value = obj.__class__.__name__
        return cls[VALUE.get(value, value)]

    @classmethod
    def class_name(cls, value: "Resource", default=None) -> str:
        """Return the name of a :mod:`sdmx.model` class from an enum value.

        Values are returned in lower case.
        """
        return CLASS_NAME.get(value.value, value.value)

    @classmethod
    def describe(cls):
        return "{" + " ".join(v.name for v in cls._member_map_.values()) + "}"


#: Response codes defined by the SDMX-REST standard.
RESPONSE_CODE = {
    200: "OK",
    304: "No changes",
    400: "Bad syntax",
    401: "Unauthorized",
    403: "Semantic error",  # or "Forbidden"
    404: "Not found",
    406: "Not acceptable",
    413: "Request entity too large",
    414: "URI too long",
    500: "Internal server error",
    501: "Not implemented",
    503: "Unavailable",
}
