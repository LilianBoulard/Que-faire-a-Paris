import sys
import logging

from .database import Database
from .event import Event

__all__ = ['Database', 'Event']


###########
# LOGGING #
###########


logging_level = logging.DEBUG

logger = logging.getLogger()
logger.setLevel(logging_level)

formatter = logging.Formatter('%(asctime)s - [%(levelname)s | %(module)s] %(message)s')
formatter.datefmt = '%m/%d/%Y %H:%M:%S'

# fh = logging.FileHandler(filename='C:/Temp/qfap.log', mode='w')
# fh.setLevel(logging_level)
# h.setFormatter(formatter)

sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging_level)
sh.setFormatter(formatter)

# logger.addHandler(fh)
logger.addHandler(sh)
