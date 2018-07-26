# -*- coding: utf-8 -*-
import os
import logging
from common_unit import make_dir

log_format = logging.Formatter('%(levelname)s %(asctime)s %(filename)s[line:%(lineno)d] %('
                               'message)s', '%Y-%m-%d %H:%M:%S')


class LogUnit(object):

    def __init__(self):
        pass

    @staticmethod
    def create_logger(log_folder, log_name, logging_level=logging.INFO, to_stream=True,
                      to_file=True):
        if log_folder is not None:
            make_dir(log_folder)
        logger = logging.getLogger(log_name)  # base.log => base.test.log
        logger.setLevel(logging_level)
        # file writer
        if to_file:
            fh = logging.FileHandler(os.path.join(log_folder, log_name))
            fh.setFormatter(log_format)
            logger.addHandler(fh)

        # stream writer
        if to_stream:
            sh = logging.StreamHandler()
            sh.setFormatter(log_format)
            logger.addHandler(sh)
        return logger


def get_log_rate():
    rate_list = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARN,
        'error': logging.ERROR,
        'fatal': logging.FATAL
    }
    return rate_list

if __name__ == '__main__':
    output_folder = '/data/log'
    log_filename = 'test.log'
    log_unit = LogUnit().create_logger(log_folder=output_folder, log_name=log_filename,
                                       logging_level=logging.INFO, to_file=True)
    log_unit.info('hello')
