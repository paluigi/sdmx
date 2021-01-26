import importlib
from distutils import version

import pytest


# thanks to xarray
def _importorskip(modname, minversion=None):
    try:
        mod = importlib.import_module(modname)
        has = True
        if minversion is not None:
            if LooseVersion(mod.__version__) < LooseVersion(minversion):
                raise ImportError("Minimum version not satisfied")
    except ImportError:
        has = False
    func = pytest.mark.skipif(not has, reason="requires {}".format(modname))
    return has, func


def LooseVersion(vstring):
    # When the development version is something like '0.10.9+aac7bfc', this
    # function will just discard the git commit id.
    vstring = vstring.split("+")[0]
    return version.LooseVersion(vstring)


has_requests_cache, requires_requests_cache = _importorskip("requests_cache")
