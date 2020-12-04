from io import BufferedIOBase, BytesIO
from warnings import warn

import requests

try:
    from requests_cache import CachedSession as MaybeCachedSession
except ImportError:  # pragma: no cover
    warn(
        "optional dependency requests_cache is not installed; cache options "
        "to Session() have no effect",
        RuntimeWarning,
    )
    from requests import Session as MaybeCachedSession


class Session(MaybeCachedSession):
    """:class:`requests.Session` subclass with optional caching.

    If :mod:`requests_cache` is installed, this class caches responses.

    Parameters
    ----------
    timeout : float
        Timeout in seconds, used for every request.

    Other parameters
    ----------------
    kwargs :
        Values for any attributes of :class:`requests.Session`, e.g.
        :attr:`~requests.Session.proxies`,
        :attr:`~requests.Session.stream`, or
        :attr:`~requests.Session.verify`.
    """

    def __init__(self, timeout=30.1, **kwargs):

        if MaybeCachedSession is not requests.Session:
            # Using requests_cache.CachedSession

            # No cache keyword arguments supplied = don't use the cache
            disabled = set(kwargs.keys()) <= {"get_footer_url"}

            if disabled:
                # Avoid creating any file
                kwargs["backend"] = "memory"

            super(Session, self).__init__()

            # Overwrite value from requests_cache.CachedSession.__init__()
            self._is_cache_disabled = disabled
        elif len(kwargs):
            raise ValueError(
                "Cache arguments have no effect without "
                "requests_session: %s" % kwargs
            )
        else:
            # Plain requests.Session
            super(Session, self).__init__()

        # Store timeout; not a property of requests.Session
        self.timeout = timeout

        # Addition keyword arguments must match existing attributes of requests.Session
        for name, value in kwargs.items():
            if hasattr(self, name):
                setattr(self, name, value)


class ResponseIO(BufferedIOBase):
    """Buffered wrapper for :class:`requests.Response` with optional file output.

    :class:`ResponseIO` wraps a :class:`requests.Response` object's 'content'
    attribute, providing a file-like object from which bytes can be :meth:`read`
    incrementally.

    Parameters
    ----------
    response : :class:`requests.Response`
        HTTP response to wrap.
    tee : binary, writable :py:class:`io.BufferedIOBasè`, defaults to io.BytesIO()
        *tee* is exposed as *self.tee* and not closed explicitly.
    """

    def __init__(self, response, tee=None):
        self.response = response
        if tee is None:
            tee = BytesIO()
        # If tee is a file-like object or tempfile, then use it as cache
        if isinstance(tee, BufferedIOBase) or hasattr(tee, "file"):
            self.tee = tee
        else:
            # So tee must be str or os.FilePath
            self.tee = open(tee, "w+b")
        self.tee.write(response.content)
        self.tee.seek(0)

    def readable(self):
        return True

    def read(self, size=-1):
        """Read and return up to `size` bytes by calling ``self.tee.read()``."""
        return self.tee.read(size)
