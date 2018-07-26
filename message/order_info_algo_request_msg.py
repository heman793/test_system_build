# -*- coding: utf-8 -*-

import six
import zmq
import AllProtoMsg_pb2
from public.main_config import *
import zlib
from socket_init import socket_init

def order_info_request_msg(last_update=None):
    socket = socket_init()

    # 拼消息
    msg_order_info_request = AllProtoMsg_pb2.OrderInfoRequestMsg()
    if last_update is not None:
        msg_order_info_request.IsAll = False
        msg_order_info_request.LastUpdateTime.scale = last_update.scale
        msg_order_info_request.LastUpdateTime.value = last_update.value
        print last_update
    else:
        msg_order_info_request.IsAll = True

    # 序列化
    msg_str = msg_order_info_request.SerializeToString()
    msg_type = 7
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)

    # 接收应答消息
    receive_message = socket.recv_multipart()
    # print "receive Order Info Response Message."
    msg_order_info_response = AllProtoMsg_pb2.OrderInfoResponseMsg()
    msg_order_info_response.ParseFromString(zlib.decompress(receive_message[1]))

    orders = msg_order_info_response.Orders
    order_msg_list = []
    for order_info in orders:
        order_msg_list.append(order_info)
    return order_msg_list

    # socket.close()

if __name__ == '__main__':
    order_info_request_msg()