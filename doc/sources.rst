.. currentmodule:: sdmx

Data sources
============

SDMX makes a distinction between data providers and sources:

- a **data provider** is the original publisher of statistical information and
  metadata.
- a **data source** is a specific web service that provides access to
  statistical information.

Each data *source* might aggregate and provide data or metadata from multiple data *providers*.
Or, an agency might operate a data source that only contains information they provide themselves; in this case, the source and provider are identical.

:mod:`sdmx` identifies each data source using a string such as ``'ABS'``, and has built-in support for a number of data sources.
Use :meth:`list_sources` to list these.
Read the following sections, or the file ``sources.json`` in the package source code, for more details.

:mod:`sdmx` also supports adding other data sources; see :meth:`add_source` and :class:`~.source.Source`.

.. contents::
   :local:
   :backlinks: none


Data source limitations
-----------------------

Each SDMX web service provides a subset of the full SDMX feature set, so the same request made to two different sources may yield different results, or an error message.

A key difference is between sources offering SDMX-ML and SDMX-JSON APIs.
SDMX-JSON APIs do not support metadata, or structure queries; only data queries.

.. note:: For JSON APIs, start by browsing the source's website to retrieve the dataflow you're interested in. Then try to fine-tune a planned data request by providing a valid key (= selection of series from the dataset).
   Because structure metadata is unavailable, :mod:`sdmx` cannot automatically validate keys.

In order to anticipate and handle these differences:

1. :meth:`add_source` accepts "data_content_type" and "supported" keys. For
   example:

   .. code-block:: json

      [
        {
          "id": "ABS",
          "data_content_type": "JSON"
        },
        {
          "id": "UNESCO",
          "unsupported": ["datastructure"]
        },
      ]

   :mod:`sdmx` will raise :class:`NotImplementedError` on an attempt to query the "datastructure" API endpoint of either of these data sources.

2. :mod:`sdmx.source` includes adapters (subclasses of :class:`~.source.Source`) with hooks used when querying sources and interpreting their HTTP responses.
   These are documented below: ABS_, ESTAT_, and SGR_.


.. _ABS:

``ABS``: Australian Bureau of Statistics
----------------------------------------

SDMX-JSON —
`Website <http://www.abs.gov.au/>`__

.. autoclass:: sdmx.source.abs.Source
   :members:


.. _ESTAT:

``ESTAT``: Eurostat
-------------------

SDMX-ML —
`Website <http://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1>`__

- Thousands of dataflows on a wide range of topics.
- No categorisations available.
- Long response times are reported.
  Increase the timeout attribute to avoid timeout exceptions.
- Does not return DSDs for dataflow requests with the ``references='all'`` query parameter.

.. autoclass:: sdmx.source.estat.Source
   :members:


``ECB``: European Central Bank
------------------------------

SDMX-ML —
`Website <http://www.ecb.europa.eu/stats/ecb_statistics/co-operation_and_standards/sdmx/html/index.en.html>`__

- Supports categorisations of data-flows.
- Supports preview_data and series-key based key validation.
- In general short response times.


``ILO``: International Labour Organization
------------------------------------------

SDMX-ML —
`Website <www.ilo.org/ilostat/>`__

- :class:`sdmx.source.ilo.Source` handles some particularities of the ILO
  web service. Others that are not handled:

  - Data flow IDs take on the role of a filter.
    E.g., there are dataflows for individual countries, ages, sexes etc. rather than merely for different indicators.
  - The service returns 413 Payload Too Large errors for some queries, with messages like: "Too many results, please specify codelist ID".
    Test for :class:`sdmx.exceptions.HTTPError` (= :class:`requests.exceptions.HTTPError`) and/or specify a ``resource_id``.

- It is highly recommended to read the `API guide <http://www.ilo.org/ilostat/content/conn/ILOSTATContentServer/path/Contribution%20Folders/statistics/web_pages/static_pages/technical_page/ilostat_appl/SDMX_User_Guide.pdf>`_.

.. autoclass:: sdmx.source.ilo.Source
   :members:


.. _IMF:

``IMF``: International Monetary Fund's “SDMX Central” source
------------------------------------------------------------

SDMX-ML —
`Website <https://sdmxcentral.imf.org/>`__

- Subset of the data available on http://data.imf.org.
- Supports series-key-only and hence dataset-based key validation and construction.


``INEGI``: National Institute of Statistics and Geography (Mexico)
------------------------------------------------------------------

SDMX-ML —
`Website <https://sdmx.snieg.mx/infrastructure>`__.

- Spanish name: Instituto Nacional de Estadística y Geografía.


.. _INSEE:

``INSEE``: National Institute of Statistics and Economic Studies (France)
-------------------------------------------------------------------------

SDMX-ML —
`Website <http://www.bdm.insee.fr/bdm2/statique?page=sdmx>`__

- French name: Institut national de la statistique et des études économiques.

.. autoclass:: sdmx.source.insee.Source
   :members:


``ISTAT``: National Institute of Statistics (Italy)
---------------------------------------------------

SDMX-ML —
`Website <http://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1>`__

- Italian name: Istituto Nazionale di Statistica.
- Similar server platform to Eurostat, with similar capabilities.


.. _LSD:

``LSD``: National Institute of Statistics (Lithuania)
-----------------------------------------------------

SDMX-ML —
`Website <https://osp.stat.gov.lt/rdb-rest>`__

- Lithuanian name: Lietuvos statistikos.
- This web service returns the non-standard HTTP content-type "application/force-download"; :mod:`sdmx` replaces it with "application/xml".


``NB``: Norges Bank (Norway)
----------------------------

SDMX-ML —
`Website <https://www.norges-bank.no/en/topics/Statistics/open-data/>`__

- Few dataflows. So do not use categoryscheme.
- It is unknown whether NB supports series-keys-only.


.. _NBB:

``NBB``: National Bank of Belgium (Belgium)
-------------------------------------------

SDMX-JSON —
`Website <https://stat.nbb.be/>`__ —
API documentation `(en) <https://www.nbb.be/doc/dq/migratie_belgostat/en/nbb_stat-technical-manual.pdf>`__

- French name: Banque Nationale de Belgique.
- Dutch name: Nationale Bank van België.
- As of 2020-12-13, this web service (like STAT_EE) uses server software that serves SDMX-ML 2.0 or SDMX-JSON.
  Since :mod:`sdmx` does not support SDMX-ML 2.0, the package is configured to use the JSON endpoint.
- The web service returns a custom HTML error page rather than an SDMX error message for certain queries or an internal error.
  This appears as: ``ValueError: can't determine a SDMX reader for response content type 'text/html; charset=utf-8'``

``OECD``: Organisation for Economic Cooperation and Development
---------------------------------------------------------------

SDMX-JSON —
`Website <http://stats.oecd.org/SDMX-JSON/>`__


.. _SGR:

``SGR``: SDMX Global Registry
-----------------------------

SDMX-ML —
`Website <https://registry.sdmx.org/ws/rest>`__

.. autoclass:: sdmx.source.sgr.Source
   :members:


.. _STAT_EE:

``STAT_EE``: Statistics Estonia (Estonia)
-----------------------------------------

SDMX-JSON —
`Website <http://andmebaas.stat.ee>`__ (et) —
API documentation `(en) <https://www.stat.ee/sites/default/files/2020-09/API-instructions.pdf>`__, `(et) <https://www.stat.ee/sites/default/files/2020-09/API-juhend.pdf>`__

- Estonian name: Eesti Statistika.
- As of 2020-12-13, this web service (like NBB) uses server software that serves SDMX-ML 2.0 or SDMX-JSON.
  Since :mod:`sdmx` does not support SDMX-ML 2.0, the package is configured to use the JSON endpoint.


``UNSD``: United Nations Statistics Division
--------------------------------------------

SDMX-ML —
`Website <https://unstats.un.org/home/>`__

- Supports preview_data and series-key based key validation.


``UNESCO``: UN Educational, Scientific and Cultural Organization
----------------------------------------------------------------

SDMX-ML —
`Website <https://apiportal.uis.unesco.org/getting-started>`__

- Free registration required; user credentials must be provided either as parameter or HTTP header with each request.

.. warning:: An issue with structure-specific datasets has been reported.
   It seems that Series are not recognized due to some oddity in the XML format.


.. _UNICEF:

``UNICEF``: UN Children's Fund
------------------------------

SDMX-ML or SDMX-JSON —
`API documentation <https://data.unicef.org/sdmx-api-documentation/>`__ —
`Web interface <https://sdmx.data.unicef.org/>`__

- This source always returns structure-specific messages for SDMX-ML data queries; even when the HTTP header ``Accept: application/vnd.sdmx.genericdata+xml`` is given.
- The example query from the UNICEF API documentation (also used in the :mod:`sdmx` test suite) returns XML like:

  .. code-block:: xml

     <mes:Structure structureID="UNICEF_GLOBAL_DATAFLOW_1_0" namespace="urn:sdmx:org.sdmx.infomodel.datastructure.Dataflow=UNICEF:GLOBAL_DATAFLOW(1.0):ObsLevelDim:TIME_PERIOD" dimensionAtObservation="TIME_PERIOD">
       <com:StructureUsage>
         <Ref agencyID="UNICEF" id="GLOBAL_DATAFLOW" version="1.0"/>
       </com:StructureUsage>
     </mes:Structure>

  The corresponding DSD actually has the ID ``DSD_AGGREGATE``, which is not obvious from the message.
  To retrieve the DSD—which is necessary to parse a data message—first query this data *flow* by ID, and select the DSD from the returned message:

  .. ipython:: python

     import sdmx
     msg = sdmx.Request("UNICEF").dataflow("GLOBAL_DATAFLOW")
     msg
     dsd = msg.structure[0]

  The resulting object `dsd` can be passed as an argument to a :meth:`.Request.get` data query.
  See the `sdmx test suite <https://github.com/khaeru/sdmx/blob/master/sdmx/tests/test_sources.py>`_ for an example.


``WB``: World Bank Group “World Integrated Trade Solution”
----------------------------------------------------------

SDMX-ML —
`Website <wits.worldbank.org>`__


.. _WB_WDI:

``WB_WDI``: World Bank Group “World Development Indicators”
-----------------------------------------------------------

SDMX-ML —
`Website <https://datahelpdesk.worldbank.org/knowledgebase/articles/1886701-sdmx-api-queries>`__

- This web service also supports SDMX-JSON.
  To retrieve messages in this format, pass the HTTP ``Accept:`` header described on the service website.
