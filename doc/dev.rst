Development
***********

This page describes the development of :mod:`sdmx`.
Contributions are welcome!

- For current development priorities, see the list of `GitHub milestones <https://github.com/khaeru/sdmx/milestones>`_ and issues/PRs targeted to each.
- For wishlist features, see issues on GitHub tagged `‘enh’ <https://github.com/khaeru/sdmx/labels/enh>`_ or `‘wishlist’ <https://github.com/khaeru/sdmx/labels/wishlist>`_.

.. contents::
   :local:
   :backlinks: none

Code style
==========

- Apply the following to new or modified code::

    isort -rc . && black . && mypy . && flake8

  Respectively, these:

  - **isort**: sort import lines at the top of code files in a consistent way, using `isort <https://pypi.org/project/isort/>`_.
  - **black**: apply `black <https://black.readthedocs.io>`_ code style.
  - **mypy**: check typing using `mypy <https://mypy.readthedocs.io>`_.
  - **flake8**: check code style against `PEP 8 <https://www.python.org/dev/peps/pep-0008>`_ using `flake8 <https://flake8.pycqa.org>`_.

- Follow `the 7 rules of a great Git commit message <https://chris.beams.io/posts/git-commit/#seven-rules>`_.
- Write docstrings in the `numpydoc <https://numpydoc.readthedocs.io/en/latest/format.html>`_ style.

.. _testing:

Test specimens
==============

.. versionadded:: 2.0

A variety of *specimens*—example files from real web services, or published with the standards—are used to test that :mod:`sdmx` correctly reads and writes the different SDMX message formats.
Since v2.0, specimens are stored in the separate `sdmx-test-data <https://github.com/khaeru/sdmx-test-data>`_ repository.

Running the test suite requires these files.
To retrieve them, use one of the following methods:

1. Obtain the files by one of two methods:

   a. Clone ``khaeru/sdmx-test-data``::

       $ git clone git@github.com:khaeru/sdmx-test-data.git

   b. Download https://github.com/khaeru/sdmx-test-data/archive/master.zip

2. Indicate where pytest can find the files, by one of two methods:

   a. Set the `SDMX_TEST_DATA` environment variable::

       # Set the variable only for one command
       $ SDMX_TEST_DATA=/path/to/files pytest

       # Export the variable to the environment
       $ export SDMX_TEST_DATA
       $ pytest

   b. Give the option ``--sdmx-test-data=<PATH>`` when invoking pytest::

       $ pytest --sdmx-test-data=/path/to/files

The files are:

- Arranged in directories with names matching particular sources in :file:`sources.json`.
- Named with:

  - Certain keywords:

    - ``-structure``: a structure message, often associated with a file with a similar name containing a data message.
    - ``ts``: time-series data, i.e. with a TimeDimensions at the level of individual Observations.
    - ``xs``: cross-sectional data arranged in other ways.
    - ``flat``: flat DataSets with all Dimensions at the Observation level.
    - ``ss``: structure-specific data messages.

  - In some cases, the query string or data flow/structure ID as the file name.
  - Hyphens ``-`` instead of underscores ``_``.


Releasing
=========

Before releasing, check:

- https://github.com/khaeru/sdmx/actions?query=workflow:pytest+branch:master to
  ensure that the push and scheduled builds are passing.
- https://readthedocs.org/projects/sdmx1/builds/ to ensure that the docs build
  is passing.

Address any failures before releasing.

1. Edit :file:`doc/whatsnew.rst` to replace "Next release" with the version number and date.
   Make a commit with a message like "Mark vX.Y.Z in whatsnew.rst".

2. Tag the version as a release candidate, e.g.::

    $ git tag v1.2.3rc1

3. Test-build and check the source and binary packages::

    $ rm -rf build dist
    $ python setup.py bdist_wheel sdist
    $ twine check dist/*

   Address any warnings or errors that appear.
   If needed, make a new commit and go back to step (2).

4. Upload the packages to the PyPI test repository::

    $ twine upload -r testpypi dist/*

5. Check at https://test.pypi.org/project/sdmx1/ that:

   - The package can be downloaded, installed and run.
   - The README is rendered correctly.
   - Links to the documentation go to the correct version.

   If not, modify the code and go back to step (2).

6. Tag the release::

    $ git tag v1.2.3

   If this is the same commit as the release candidate tag, delete that tag.

7. Built and upload to both PyPI and the test repo (to supersede the RC)::

    $ rm -rf build dist
    $ python setup.py bdist_wheel sdist
    $ twine check dist/*
    $ twine upload dist/*
    $ twine upload -r testpypi dist/*

8. Edit :file:`doc/whatsnew.rst` to add a new heading for the next release.
   Make a commit with a message like "Reset whatsnew.rst to development state".

9. Push the commits and tag to GitHub::

    $ git push --tags

   Visit https://github.com/khaeru/sdmx/releases and mark the new release using the pushed tag.


Internal code reference
=======================

``testing``: Testing utilities
------------------------------

.. automodule:: sdmx.testing
   :members:
   :undoc-members:
   :show-inheritance:

``util``: Utilities
-------------------
.. automodule:: sdmx.util
   :noindex:
   :members: BaseModel, summarize_dictlike, validate_dictlike
   :undoc-members:
   :show-inheritance:


Inline TODOs
============

.. todolist::
