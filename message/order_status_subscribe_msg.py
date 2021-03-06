# -*- coding: utf-8 -*-

import six
import zmq
import AllProtoMsg_pb2
from public.main_config import *
import zlib
from socket_init import socket_init

def order_status_subscribe_msg():
    socket = socket_init()
    # 拼消息
    msg_order_info_request = AllProtoMsg_pb2.OrderInfoRequestMsg()
    msg_order_info_request.IsAll = False

    # 序列化
    msg_str = msg_order_info_request.SerializeToString()
    msg_type = 7
    msg_list = [six.int2byte(msg_type), msg_str]

    print "Send Order Info Request Message."
    socket.send_multipart(msg_list)
    # print msg_list

    # 接收应答消息
    receive_message = socket.recv_multipart()
    print "receive Order Info Response Message."
    msg_order_info_response = AllProtoMsg_pb2.OrderInfoResponseMsg()
    msg_order_info_response.ParseFromString(zlib.decompress(receive_message[1]))

    order_msg_list = []
    for order_info in msg_order_info_response.Orders:
        order_msg_list.append(order_info)
        # print order_msg_list
    return order_msg_list


if __name__ == '__main__':
    order_status_subscribe_msg()