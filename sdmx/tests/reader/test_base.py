import pytest

from sdmx.reader.base import BaseReader


class TestBaseReader:
    @pytest.fixture
    def MinimalReader(self):
        """A reader that implements the minimum abstract methods."""

        class cls(BaseReader):
            content_types = ["application/foo; bar=baz"]

            def read_message(self, source, dsd=None):
                pass  # pragma: no cover

        return cls

    def test_detect(self, MinimalReader):
        assert False is MinimalReader.detect(b"foo")

    def test_supports_content_type(self, caplog, MinimalReader):
        """:meth:`.support_content_type` matches even when params differ, but logs."""
        assert True is MinimalReader.supports_content_type("application/foo; bar=qux")
        assert (
            "Match application/foo with params {'bar': 'qux'}; expected {'bar': 'baz'}"
            in caplog.messages
        )
