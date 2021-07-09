import pytest

from sdmx.reader.base import BaseReader


class TestBaseReader:
    @pytest.fixture
    def MinimalReader(self):
        """A reader that implements the minimum abstract methods."""

        class cls(BaseReader):
            def read_message(self, source, dsd=None):
                pass

        return cls

    def test_detect(self, MinimalReader):
        assert False is MinimalReader.detect(b"foo")
