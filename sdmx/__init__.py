import logging

import pkg_resources

from sdmx.api import Request, read_url
from sdmx.reader import read_sdmx
from sdmx.source import add_source, list_sources
from sdmx.util import Resource
from sdmx.writer import to_pandas, to_xml

__all__ = [
    "Request",
    "Resource",
    "add_source",
    "list_sources",
    "logger",
    "read_sdmx",
    "read_url",
    "to_pandas",
    "to_xml",
]


try:
    __version__ = pkg_resources.get_distribution("sdmx").version
except Exception:
    # Local copy or not installed with setuptools
    __version__ = "999"


#: Top-level logger.
logger = logging.getLogger(__name__)


def _init_logger():
    handler = logging.StreamHandler()
    fmt = "{asctime} {name} - {levelname}: {message}"
    handler.setFormatter(logging.Formatter(fmt, style="{"))
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)


_init_logger()
