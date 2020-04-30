API reference
=============

See also the :doc:`implementation`.

.. contents::
   :local:
   :backlinks: none

Top-level methods and classes
-----------------------------
.. automodule:: sdmx
   :members:
   :exclude-members: logger

.. autodata:: logger

   By default, messages at the :ref:`log level <py:levels>` ``ERROR`` or
   greater are printed to :obj:`sys.stderr`.
   These include the web service query details (URL and headers) used by :class:`.Request`.

   To debug requets to web services, set to a more permissive level::

       import logging

       sdmx.logger.setLevel(logging.DEBUG)

   .. versionadded:: 0.4


``message``: SDMX messages
--------------------------
.. automodule:: sdmx.message
   :members:
   :undoc-members:
   :show-inheritance:

.. _api-model:

``model``: SDMX Information Model
---------------------------------

.. automodule:: sdmx.model
   :members:
   :undoc-members:
   :show-inheritance:

``reader``: Parsers for SDMX file formats
-----------------------------------------

SDMX-ML
:::::::
.. currentmodule:: sdmx.reader.sdmxml

:mod:`sdmx` supports the several types of SDMX-ML messages.

.. autoclass:: sdmx.reader.sdmxml.Reader
    :members:
    :undoc-members:

SDMX-JSON
:::::::::

.. currentmodule:: sdmx.reader.sdmxjson

.. autoclass:: sdmx.reader.sdmxjson.Reader
    :members:
    :undoc-members:


``writer``: Convert SDMX to pandas objects
------------------------------------------
.. versionchanged:: 1.0

   :meth:`sdmx.to_pandas` (via :meth:`write <sdmx.writer.write>`)
   handles all types of objects, replacing the earlier, separate
   ``data2pandas`` and ``structure2pd`` writers.

.. automodule:: sdmx.writer
   :members:
   :exclude-members: write

   .. automethod:: sdmx.writer.write

      .. autosummary::
         write_component
         write_datamessage
         write_dataset
         write_dict
         write_dimensiondescriptor
         write_itemscheme
         write_list
         write_membervalue
         write_nameableartefact
         write_serieskeys
         write_structuremessage

.. autodata:: DEFAULT_RTYPE
   :noindex:

.. todo::
   Support selection of language for conversion of
   :class:`InternationalString <sdmx.model.InternationalString>`.


``remote``: Access SDMX REST web services
-----------------------------------------
.. autoclass:: sdmx.remote.Session
.. autoclass:: sdmx.remote.ResponseIO


``source``: Features of SDMX data sources
-----------------------------------------

This module defines :class:`Source <sdmx.source.Source>` and some utility functions.
For built-in subclasses of Source used to provide :mod:`sdmx`'s built-in support
for certain data sources, see :doc:`sources`.

.. autoclass:: sdmx.source.Source
   :members:

.. automodule:: sdmx.source
   :members: add_source, list_sources, load_package_sources


``util``: Utilities
-------------------
.. automodule:: sdmx.util
   :members:
   :undoc-members:
   :show-inheritance:
