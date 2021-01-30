import json
import logging
import re
from io import BytesIO

import pandas as pd
import pytest

import sdmx


def test_deprecated_request(caplog):
    message = "Request class will be removed in v3.0; use Client(…)"
    with pytest.warns(DeprecationWarning, match=re.escape(message)):
        sdmx.Request("ECB")

    assert caplog.record_tuples == [("sdmx.client", logging.WARNING, message)]


def test_read_sdmx(tmp_path, specimen):
    # Copy the file to a temporary file with an urecognizable suffix
    target = tmp_path / "foo.badsuffix"
    with specimen("flat.json", opened=False) as original:
        target.open("w").write(original.read_text())

    # With unknown file extension, read_sdmx() peeks at the file content
    sdmx.read_sdmx(target)

    # Format can be inferred from an already-open file without extension
    with specimen("flat.json") as f:
        sdmx.read_sdmx(f)

    # Exception raised when the file contents don't allow to guess the format
    bad_file = BytesIO(b"#! neither XML nor JSON")
    exc = (
        "cannot infer SDMX message format from path None, format={}, or content "
        "'#! ne..'"
    )
    with pytest.raises(RuntimeError, match=exc.format("None")):
        sdmx.read_sdmx(bad_file)

    # Using the format= argument forces a certain reader to be used
    with pytest.raises(json.JSONDecodeError):
        sdmx.read_sdmx(bad_file, format="JSON")


def test_Client():
    # Constructor
    with pytest.warns(
        DeprecationWarning, match=re.escape("Client(…, log_level=…) parameter")
    ):
        r = sdmx.Client(log_level=logging.ERROR)

    # Invalid source name raise an exception
    with pytest.raises(ValueError):
        sdmx.Client("noagency")

    # Regular methods
    r.clear_cache()

    r.timeout = 300
    assert r.timeout == 300

    # dir() includes convenience methods for resource endpoints
    expected = {
        "cache",
        "clear_cache",
        "get",
        "preview_data",
        "series_keys",
        "session",
        "source",
        "timeout",
    }
    expected |= set(ep.name for ep in sdmx.Resource)
    assert set(filter(lambda s: not s.startswith("_"), dir(r))) == expected


def test_request_get_exceptions():
    """Tests of Client.get() that don't require remote data."""
    ESTAT = sdmx.Client("ESTAT")

    # Exception is raised on unrecognized arguments
    exc = "unrecognized arguments: {'foo': 'bar'}"
    with pytest.raises(ValueError, match=exc):
        ESTAT.get("datastructure", foo="bar")

    exc = r"{'foo': 'bar'} supplied with get\(url=...\)"
    with pytest.raises(ValueError, match=exc):
        sdmx.read_url("https://example.com", foo="bar")


@pytest.mark.network
def test_request_get_args():
    ESTAT = sdmx.Client("ESTAT")

    # Client._make_key accepts '+'-separated values
    args = dict(
        resource_id="une_rt_a",
        key={"GEO": "EL+ES+IE"},
        params={"startPeriod": "2007"},
        dry_run=True,
        use_cache=True,
    )
    # Store the URL
    url = ESTAT.data(**args).url

    # Using an iterable of key values gives the same URL
    args["key"] = {"GEO": ["EL", "ES", "IE"]}
    assert ESTAT.data(**args).url == url

    # Using a direct string for a key gives the same URL
    args["key"] = "....EL+ES+IE"  # No specified values for first 4 dimensions
    assert ESTAT.data(**args).url == url

    # Giving 'provider' is redundant for a data request, causes a warning
    with pytest.warns(UserWarning, match="'provider' argument is redundant"):
        ESTAT.data(
            "une_rt_a",
            key={"GEO": "EL+ES+IE"},
            params={"startPeriod": "2007"},
            provider="ESTAT",
        )

    # Using an unknown endpoint is an exception
    with pytest.raises(ValueError):
        ESTAT.get("badendpoint", "id")

    # TODO test Client.get(obj) with IdentifiableArtefact subclasses


@pytest.mark.network
def test_read_url():
    # URL can be queried without instantiating Client
    sdmx.read_url(
        "https://sdw-wsrest.ecb.europa.eu/service/datastructure/ECB/ECB_EXR1/latest?"
        "references=all"
    )


@pytest.mark.network
def test_request_preview_data():
    ECB = sdmx.Client("ECB")

    # List of keys can be retrieved
    keys = ECB.preview_data("EXR")
    assert isinstance(keys, list)

    # Count of keys can be determined
    assert len(keys) > 1000

    # A filter can be provided, resulting in fewer keys
    keys = ECB.preview_data("EXR", {"CURRENCY": "CAD+CHF+CNY"})
    assert len(keys) == 24

    # Result can be converted to pandas object
    keys_pd = sdmx.to_pandas(keys)
    assert isinstance(keys_pd, pd.DataFrame)
    assert len(keys_pd) == 24
