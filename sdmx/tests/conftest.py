import logging

import sdmx


sdmx.logger.setLevel(logging.INFO)

sdmx.writer.DEFAULT_RTYPE = 'rows'
