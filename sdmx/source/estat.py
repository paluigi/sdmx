import logging
from tempfile import NamedTemporaryFile
from time import sleep
from urllib.parse import urlparse
from zipfile import ZipFile

import requests

from sdmx.rest import Resource
from sdmx.source import Source as BaseSource

log = logging.getLogger(__name__)


class Source(BaseSource):
    """Handle Eurostat's mechanism for large datasets and other quirks.

    For some requests, ESTAT returns a DataMessage that has no content except for a
    ``<footer:Footer>`` element containing a URL where the data will be made available
    as a ZIP file.

    To configure :meth:`finish_message`, pass its `get_footer_url` argument to
    :meth:`.Client.get`.

    .. versionadded:: 0.2.1

    See also
    --------
    :meth:`modify_request_args`
    """

    _id = "ESTAT"

    def modify_request_args(self, kwargs):
        """Modify arguments used to build query URL.

        For the "references" query parameter, ESTAT (as of 2022-11-13) only supports the
        values "children", "descendants", or "none". Other values—including the "all" or
        "parentsandsiblings" used as defaults by :class:`.Client` cause errors. Replace
        unsupported values with "none", and use "descendants" as default.

        See also
        --------
        :pull:`107`, :pull:`108`
        """
        super().modify_request_args(kwargs)

        kwargs.pop("get_footer_url", None)

        resource_type = kwargs.get("resource_type")

        # Handle the ?references= query parameter
        params = kwargs.setdefault("params", {})
        references = params.get("references")
        if references is None:
            # Client._request_from_args() sets "all" or "parentsandsiblings" by default.
            # Neither of these values is supported by ESTAT; use "descendants" instead.
            if (
                resource_type
                in (Resource.categoryscheme, Resource.dataflow, Resource.datastructure)
                and kwargs.get("resource_id")
            ) or kwargs.get("resource"):
                params["references"] = "descendants"
        elif references not in ("children", "descendants", "none"):
            log.info(f"Replace unsupported references={references!r} with 'none'")
            params["references"] = "none"

    def finish_message(self, message, request, get_footer_url=(30, 3), **kwargs):
        """Handle the initial response.

        This hook identifies the URL in the footer of the initial response,
        makes a second request (polling as indicated by *get_footer_url*), and
        returns a new DataMessage with the parsed content.

        Parameters
        ----------
        get_footer_url : (int, int)
            Tuple of the form (`seconds`, `attempts`), controlling the interval
            between attempts to retrieve the data from the URL, and the
            maximum number of attempts to make.
        """
        # Check the message footer for a text element that is a valid URL
        url = None
        for text in getattr(message.footer, "text", []):
            if urlparse(str(text)).scheme:
                url = str(text)
                break

        if not url:
            return message

        # Unpack arguments
        wait_seconds, attempts = get_footer_url

        # Create a temporary file to store the ZIP response
        ntf = NamedTemporaryFile(prefix="pandasdmx-")
        # Make a limited number of attempts to retrieve the file
        for a in range(attempts):
            sleep(wait_seconds)
            try:
                # This line succeeds if the file exists; the ZIP response
                # is stored to ntf, and then used by the
                # handle_response() hook below
                return request.get(url=url, tofile=ntf)
            except requests.HTTPError:
                raise
        ntf.close()
        raise RuntimeError("Maximum attempts exceeded")

    def handle_response(self, response, content):
        """Handle the polled response.

        The request for the indicated ZIP file URL returns an octet-stream;
        this handler saves it, opens it, and returns the content of the single
        contained XML file.
        """

        if response.headers["content-type"] != "application/octet-stream":
            return response, content

        # Read all the input, forcing it to be copied to
        # content.tee_filename
        while True:
            if len(content.read()) == 0:
                break

        # Open the zip archive
        with ZipFile(content.tee, mode="r") as zf:
            # The archive should contain only one file
            infolist = zf.infolist()
            assert len(infolist) == 1

            # Set the new content type
            response.headers["content-type"] = "application/xml"

            # Use the unzipped archive member as the response content
            return response, zf.open(infolist[0])
