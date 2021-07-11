import logging
import os
from collections import ChainMap
from contextlib import contextmanager
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import pytest

from sdmx.exceptions import HTTPError
from sdmx.rest import Resource
from sdmx.source import DataContentType, add_source, sources

log = logging.getLogger(__name__)


# Expected to_pandas() results for data files; see expected_data()
# - Keys are the file name (above) with '.' -> '-': 'foo.xml' -> 'foo-xml'
# - Data is stored in expected/{KEY}.txt
# - Values are either argument to pd.read_csv(); or a dict(use='other-key'),
#   in which case the info for other-key is used instead.
EXPECTED = {
    "ng-flat-xml": dict(index_col=[0, 1, 2, 3, 4, 5]),
    "ng-ts-gf-xml": dict(use="ng-flat-xml"),
    "ng-ts-xml": dict(use="ng-flat-xml"),
    "ng-xs-xml": dict(index_col=[0, 1, 2, 3, 4, 5]),
    # Excluded: this file contains two DataSets, and expected_data() currently
    # only supports specimens with one DataSet
    # 'action-delete-json': dict(header=[0, 1, 2, 3, 4]),
    "xs-json": dict(index_col=[0, 1, 2, 3, 4, 5]),
    "flat-json": dict(index_col=[0, 1, 2, 3, 4, 5]),
    "ts-json": dict(use="flat-json"),
}


def assert_pd_equal(left, right, **kwargs):
    """Assert equality of two pandas objects."""
    if left is None:
        return
    method = {
        pd.Series: pd.testing.assert_series_equal,
        pd.DataFrame: pd.testing.assert_frame_equal,
        np.ndarray: np.testing.assert_array_equal,
    }[left.__class__]
    method(left, right, **kwargs)


def pytest_addoption(parser):
    """Add the ``--sdmx-test-data`` command-line option to pytest."""
    parser.addoption(
        "--sdmx-test-data",
        # Use the environment variable value by default
        default=os.environ.get("SDMX_TEST_DATA", None),
        help="path to SDMX test specimens",
    )


def pytest_configure(config):
    """Handle the ``--sdmx-test-data`` command-line option."""
    # Register "parametrize_specimens" as a known mark to suppress warnings from pytest
    config.addinivalue_line(
        "markers", "parametrize_specimens: (for internal use by sdmx.testing)"
    )

    # Check the value can be converted to a path, and exists
    message = "Give --sdmx-test-data=… or set the SDMX_TEST_DATA environment variable"
    try:
        sdmx_test_data = Path(config.option.sdmx_test_data)
    except TypeError:  # pragma: no cover
        raise RuntimeError(message) from None
    else:  # pragma: no cover
        if not sdmx_test_data.exists():  # pragma: no cover
            # Cannot proceed further; this exception kills the test session
            raise FileNotFoundError(f"SDMX test data in {sdmx_test_data}\n{message}")

    setattr(config, "sdmx_test_data", sdmx_test_data)
    setattr(config, "sdmx_specimens", SpecimenCollection(sdmx_test_data))


def pytest_generate_tests(metafunc):
    """Generate tests.

    Calls both :func:`parametrize_specimens` and :func:`generate_endpoint_tests`.
    """
    parametrize_specimens(metafunc)
    generate_endpoint_tests(metafunc)


def parametrize_specimens(metafunc):
    """Handle ``@pytest.mark.parametrize_specimens(…)``."""
    try:
        mark = next(metafunc.definition.iter_markers("parametrize_specimens"))
    except StopIteration:
        return

    metafunc.parametrize(
        mark.args[0], metafunc.config.sdmx_specimens.as_params(**mark.kwargs)
    )


#: This exception is raised by client.Client._request_from_args
#:
#: .. todo:: parametrize force=True to query these endpoints anyway; then XPASS will
#:    reveal when data sources change their support for endpoints
unsupported = pytest.mark.xfail(
    strict=True, reason="Known non-supported endpoint.", raises=NotImplementedError
)

_503 = pytest.mark.xfail(
    raises=HTTPError, reason="503 Server Error: Service Unavailable"
)


def generate_endpoint_tests(metafunc):
    """pytest hook for parametrizing tests that need an "endpoint" fixture."""
    if "endpoint" not in metafunc.fixturenames:
        return  # Don't need to parametrize this metafunc

    # Arguments to parametrize()
    params = []

    # Use the test class' source_id attr to look up the Source class
    source = sources[metafunc.cls.source_id]

    # Merge "common" and subclass-specific xfails
    xfails = ChainMap(metafunc.cls.xfail, metafunc.cls.xfail_common)

    # Iterate over all known endpoints
    for ep in Resource:
        # Accumulate multiple marks; first takes precedence
        marks = []

        # Check if the associated source supports the endpoint
        supported = source.supports[ep]
        if source.data_content_type == DataContentType.JSON and ep is not Resource.data:
            # SDMX-JSON sources only support data queries
            continue
        elif not supported:
            marks.append(unsupported)

        # Check if the test function's class contains an expected failure for `endpoint`
        exc_class = xfails.get(ep.name, None)
        if exc_class:
            # Mark the test as expected to fail
            marks.append(pytest.mark.xfail(strict=True, raises=exc_class))

            if not supported:  # pragma: no cover
                log.info(
                    f"tests for {repr(metafunc.cls.source_id)} mention unsupported "
                    f"endpoint {repr(ep.name)}"
                )

        # Tolerate 503 errors
        if metafunc.cls.tolerate_503:
            marks.append(_503)

        # Get any keyword arguments for this endpoint
        args = metafunc.cls.endpoint_args.get(ep.name, dict())
        if ep is Resource.data and not len(args):
            # args must be specified for a data query; no args → no test
            continue

        params.append(pytest.param(ep, args, id=ep.name, marks=marks))

    if len(params):
        # Run the test function once for each endpoint
        metafunc.parametrize("endpoint, args", params)
    else:
        pytest.skip("No endpoints to be tested")


class MessageTest:
    """Base class for tests of specific specimen files."""

    directory: Union[str, Path] = Path(".")
    filename: str

    @pytest.fixture(scope="class")
    def path(self, test_data_path):
        yield test_data_path / self.directory

    @pytest.fixture(scope="class")
    def msg(self, path):
        import sdmx

        return sdmx.read_sdmx(path / self.filename)


class SpecimenCollection:
    """Collection of test specimens."""

    def __init__(self, base_path):
        self.base_path = base_path

        specimens = [
            (base_path / "INSEE" / "CNA-2010-CONSO-SI-A17.xml", "xml", "data"),
            (base_path / "INSEE" / "IPI-2010-A21.xml", "xml", "data"),
        ]

        # XML data files for the ECB exchange rate data flow
        for path in (base_path / "ECB_EXR").rglob("*.xml"):
            kind = "data"
            if "structure" in path.name or "common" in path.name:
                kind = "structure"
            specimens.append((path, "xml", kind))

        # JSON data files for the ECB exchange rate data flow
        for fp in (base_path / "ECB_EXR").rglob("*.json"):
            specimens.append((fp, "json", "data"))
        for fp in (base_path / "OECD").rglob("*.json"):
            specimens.append((fp, "json", "data"))

        # Miscellaneous XML data files
        specimens.append((base_path / "ESTAT" / "footer.xml", "xml", "data"))

        # Miscellaneous XML structure files
        specimens.extend(
            (base_path.joinpath(*parts), "xml", "structure")
            for parts in [
                ("ECB", "orgscheme.xml"),
                ("ESTAT", "apro_mk_cola-structure.xml"),
                # Manually reduced subset of the response for this DSD. Test for
                # <str:CubeRegion> containing both <com:KeyValue> and <com:Attribute>
                ("IMF", "ECOFIN_DSD-structure.xml"),
                ("INSEE", "CNA-2010-CONSO-SI-A17-structure.xml"),
                ("INSEE", "dataflow.xml"),
                ("INSEE", "IPI-2010-A21-structure.xml"),
                ("ISTAT", "47_850-structure.xml"),
                ("UNSD", "codelist_partial.xml"),
                ("SGR", "common-structure.xml"),
            ]
        )

        self.specimens = specimens

    @contextmanager
    def __call__(self, pattern="", opened=True):
        """Open the test specimen file with `pattern` in the name."""
        for path, f, k in self.specimens:
            if path.match("*" + pattern + "*"):
                yield open(path, "br") if opened else path
                return
        raise ValueError(pattern)  # pragma: no cover

    def as_params(self, format=None, kind=None, marks=dict()):
        """Generate :func:`pytest.param` from specimens.

        One :func:`~.pytest.param` is generated for each specimen that matches the
        `format` and `kind` arguments (if any). Marks are attached to each param from
        `marks`, wherein the keys are partial paths.
        """
        for path, f, k in self.specimens:
            if (format and format != f) or (kind and kind != k):
                continue
            yield pytest.param(
                path,
                id=str(path.relative_to(self.base_path)),
                marks=marks.get(path, tuple()),
            )

    def expected_data(self, path):
        """Return the expected :func:`.to_pandas()` result for the specimen `path`."""
        try:
            key = path.name.replace(".", "-")
            info = EXPECTED[key]
            if "use" in info:
                # Use the same expected data as another file
                key = info["use"]
                info = EXPECTED[key]
        except KeyError:
            return None

        args = dict(sep=r"\s+", index_col=[0], header=[0])
        args.update(info)

        result = pd.read_csv(
            self.base_path.joinpath("expected", key).with_suffix(".txt"), **args
        )

        # A series; unwrap
        if set(result.columns) == {"value"}:
            result = result["value"]

        return result


@pytest.fixture(scope="session")
def test_data_path(pytestconfig):
    """Fixture: the :py:class:`.Path` given as --sdmx-test-data."""
    yield pytestconfig.sdmx_test_data


@pytest.fixture(scope="session")
def specimen(pytestconfig):
    """Fixture: the :class:`SpecimenCollection`."""
    yield pytestconfig.sdmx_specimens


@pytest.fixture(scope="class")
def testsource():
    """Fixture: the :attr:`.Source.id` of a non-existent data source."""
    id = "TEST"
    add_source(dict(id=id, name="Test source", url="https://example.com/sdmx-rest"))

    try:
        yield id
    finally:
        sources.pop(id)
