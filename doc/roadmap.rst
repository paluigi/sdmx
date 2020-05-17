Development
***********

This page gives development guidelines and some possible future enhancements to :mod:`sdmx`.
For current development priorities, see the list of `GitHub milestones <https://github.com/khaeru/sdmx/milestones>`_ and issues/PRs targeted to each.
Contributions are welcome!

Code style
==========

- Apply the following to new or modified code::

    isort -rc . && black . && mypy . && flake8

  Respectively, these:

  - **isort**: sort import lines at the top of code files in a consistent way, using `isort <https://pypi.org/project/isort/>`_.
  - **black**: apply `black <https://black.readthedocs.io>`_ code style.
  - **mypy**: check typing using `mypy <https://mypy.readthedocs.io>`_.
  - **flake8**: check code style against `PEP 8 <https://www.python.org/dev/peps/pep-0008>`_ using `flake8 <https://flake8.pycqa.org>`_.

- Write docstrings in the `numpydoc <https://numpydoc.readthedocs.io/en/latest/format.html>`_ style.

Roadmap
=======

SDMX features & miscellaneous
-----------------------------

- Serialize :class:`Message` objects as SDMX-CSV (simplest), -JSON, or -ML (most complex).

- Parse SDMX-JSON structure messages.

- Selective/partial parsing of SDMX-ML messages.

- sdmx.api.Request._resources only contains a subset of: https://ec.europa.eu/eurostat/web/sdmx-web-services/rest-sdmx-2.1 (see "NOT SUPPORTED OPERATIONS"); provide the rest.

- Get a set of API keys for testing UNESCO and encrypt them for use in CI: https://docs.travis-ci.com/user/encryption-keys/

- Use the `XML Schema <https://en.wikipedia.org/wiki/XML_Schema_(W3C)>`_ definitions of SDMX-ML to validate messages and snippets.

- Implement SOAP web service APIs.
  This would allow access to, e.g., a broader set of :ref:`IMF` data.

- Support SDMX-ML 2.0.
  Several data providers still exist which only return SDMX-ML 2.0 messages.

- Performance.
  Parsing some messages can be slow.
  Install pytest-profiling_ and run, for instance::

      $ py.test --profile --profile-svg -k xml_structure_insee
      $ python3 -m pstats prof/combined.prof
      % sort cumulative
      % stats


Use pd.DataFrame for internal storage
-------------------------------------

:mod:`sdmx` handles :class:`Observations <sdmx.model.Observation>` as individual object instances.
An alternative is to use :mod:`pandas` or other data structures internally.
See:

- sdmx/experimental.py for a partial mock-up of such code, and
- tests/test_experimental.py for tests.

Choosing either the current or experimental DataSet as a default should be based on detailed performance (memory and time) evaluation under a variety of use-cases.
To that end, note that the experimental DataSet involves three conversions:

1. a reader parses the XML or JSON source, creates Observation instances, and adds them using DataSet.add_obs()
2. experimental.DataSet.add_obs() populates a pd.DataFrame from these Observations, but discards them.
3. experimental.DataSet.obs() creates new Observation instances.

For a fair comparison, the API between the readers and DataSet could be changed to eliminate the round trip in #1/#2, but *without* sacrificing the data model consistency provided by pydantic on Observation instances.

Inline TODOs
------------

.. todolist::

.. _pytest-profiling: https://pypi.org/project/pytest-profiling/
