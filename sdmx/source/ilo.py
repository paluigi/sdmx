from . import Source as BaseSource


class Source(BaseSource):
    _id = "ILO"

    def modify_request_args(self, kwargs):
        """Handle limitations of ILO's REST service.

        1. Service returns SDMX-ML 2.0 by default, whereas :mod:`sdmx` only
           supports SDMX-ML 2.1. Set ``?format=generic_2_1`` query parameter.
        """
        super().modify_request_args(kwargs)

        kwargs.setdefault("params", {})
        kwargs["params"].setdefault("format", "generic_2_1")