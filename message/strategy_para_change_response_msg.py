# -*- coding: utf-8 -*-

import six
import AllProtoMsg_pb2
import zlib
import zmq
from random import randint
from public.main_config import *


def strategy_para_change_info_request_msg(strategy_name, is_enable=False):
    context = zmq.Context().instance()
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, bytes(randint(10000000, 999999999)))
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(socket_connect_dict)

    msg = AllProtoMsg_pb2.StrategyParameterChangeRequestMsg()
    msg.Name = strategy_name
    msg.IsEnable = is_enable

    # parameter_item = msg.Parameter.add()
    # parameter_item.Key = "Account"
    # parameter_item.Value = "steady_return"


    # 序列化
    msg_str = msg.SerializeToString()
    msg_type = 16
    msg_list = [six.int2byte(msg_type), msg_str]

    # print "Send strategy parameter change Info Request Message."
    socket.send_multipart(msg_list)
    # print msg_list

    # 接收应答消息
    recv_msg = socket.recv_multipart()
    # print recv_msg
    recv_result = six.byte2int(recv_msg[0])
    # print recv_result
    return recv_result

if __name__ == '__main__':
    strategy_name = 'Hans.i_15min_para1'
    strategy_para_change_info_request_msg(strategy_name)