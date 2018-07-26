# -*- coding: utf-8 -*-

import six
import AllProtoMsg_pb2
import zlib
import zmq
from random import randint
from public.main_config import *
import pandas as pd


def strategy_state_change_request_msg(strategy_name, is_enable=False):
    context = zmq.Context().instance()
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, bytes(randint(10000000, 999999999)))
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(socket_connect_dict)

    msg = AllProtoMsg_pb2.StrategyStateChangeRequestMsg()
    msg.Name = strategy_name

    state_item = msg.State.add()
    state_item.Key = "BarNum"
    state_item.Value = "250"

    print msg
    # 序列化
    msg_str = msg.SerializeToString()
    msg_type = 26
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)

if __name__ == '__main__':
    strategy_name = 'VolumeBreakthrough.zn_5min_para1'
    strategy_state_change_request_msg(strategy_name)