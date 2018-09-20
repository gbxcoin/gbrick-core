import logging, os, time, coloredlogs
from logging.handlers import TimedRotatingFileHandler
from gbrick.property import *

class Glogger:

    def __init__(self, log_file_name: str = "BaseClientComm"):
        log_path = LOG_PATH
        if not log_path.endswith('/'):
            log_path = log_path + '/'

        try:
            if not os.path.exists(log_path):
                os.makedirs(log_path)
        except OSError:
            log_path = './'
            self.logger.error('Error: Creating directory. ' + log_path)

        log_file_name = log_path + log_file_name + ".log"

        # 로깅 샘플 : 포맷터 참고 - https://docs.python.org/3/library/logging.html#logrecord-attributes
        self.logger = logging.getLogger('DbClientComm')
        fomatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s]%(asctime)s > %(message)s')

        fileHandler = TimedRotatingFileHandler(log_file_name, when="midnight", interval=1)
        fileHandler.setFormatter(fomatter)
        fileHandler.suffix = "%Y%m%d"
        self.logger.addHandler(fileHandler)

        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(fomatter)
        self.logger.addHandler(streamHandler)

        self.logger.setLevel(logging.WARNING)


DEBUG_FORMAT = '%(asctime)s %(process)d %(levelname)s %(message)s'
FILE_FORMAT = '%(asctime)s %(levelname)s %(message)s'

class Glog:
    def __init__(self):
        self.log_path = LOG_PATH +'/'
        try:
            if not os.path.exists(self.log_path):
                os.makedirs(self.log_path)
        except IsADirectoryError:
            pass
        self.glogger = logging.getLogger('gbrick')
        self.glogger.setLevel(logging.DEBUG)
        filename = self.log_path + 'gbrick' + time.strftime('%y%m%d')+'.log'
        coloredlogs.install(level='DEBUG',
                            fmt=DEBUG_FORMAT,
                            isatty=True,
                            )

        fh = logging.FileHandler(filename)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter(FILE_FORMAT))
        self.glogger.addHandler(fh)


    def debug(self, s):
        self.glogger.debug(s)

    def info(self, s):
        self.glogger.info(s)

    def warning(self, s):
        self.glogger.warning(s)

    def error(self, s):
        self.glogger.error(s)

    def critical(self, s):
        self.glogger.critical(s)

glogger = Glog()