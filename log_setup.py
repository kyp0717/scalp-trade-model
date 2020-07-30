import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('spam')
logfile = logging.FileHandler("test.log")
logger.addHandler(logfile)
