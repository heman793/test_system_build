# -*- coding: utf-8 -*-
import zmq
from tools.date_utils import DateUtils
from public.main_config import *
import logging.config
import time

task_logger = logging.getLogger('task')
date_utils = DateUtils()

def socket_init():
    context = zmq.Context()
    task_logger.info("Connecting to server:%s", socket_connect_dict)
    socket = context.socket(zmq.REP)
    socket.connect(socket_connect_dict)

    while True:
        message = socket.recv()
        print 'receive request: ', message
        time.sleep(1)
        if message == 'hello':
            socket.send('World')
        else:
            socket.send('success')

if __name__ == '__main__':
    socket_init()