# -*- coding: utf-8 -*-
import zmq
from tools.date_utils import DateUtils
from public.main_config import *
import logging.config
from random import randint

task_logger = logging.getLogger('task')
date_utils = DateUtils()


def socket_init():
    context = zmq.Context().instance()
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, bytes(randint(10000000, 999999999)))
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(socket_connect_dict)


if __name__ == '__main__':
    socket_init()