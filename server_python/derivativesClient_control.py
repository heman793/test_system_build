# -*- coding: utf-8 -*-
import os
from tools.loggingUtils import loggingUtils

logger = loggingUtils('dailyjob_0905.log')
derivativesClient_path = '/home/trader/dailyjob/DerivativesClient'
eod_python_path = '/home/trader/dailyjob/eod_aps'


def update_position():
    logger.info('start update position!')
    os.chdir(derivativesClient_path)
    output = os.popen('./build64_release/DerivativesClient/DerivativesClient_position')
    logger.info(output.read())

    os.chdir(eod_python_path)
    output = os.popen('python ./server/ctp_position_analysis.py')
    logger.info(output.read())


def update_price():
    logger.info('start update position!')
    os.chdir(derivativesClient_path)
    output = os.popen('./build64_release/DerivativesClient/DerivativesClient_price')
    logger.info(output.read())

    os.chdir(eod_python_path)
    output = os.popen('python ./server/ctp_price_analysis.py')
    logger.info(output.read())


if __name__ == '__main__':
    update_position()
    update_price()
