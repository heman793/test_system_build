# -*- coding: utf-8 -*-

import six
import zmq
import AllProtoMsg_pb2
from public.main_config import *
import zlib

def server_info_request_msg():
    context = zmq.Context().instance()
    print "Connecting to server"
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, b'127.0.0.1_real')
    socket.connect(socket_connect_dict)
    # 发送请求
    msg_server_info_request = AllProtoMsg_pb2.ServerInfoRequestMsg()

    # 序列化
    msg_str = msg_server_info_request.SerializeToString()
    msg_type = 11
    msg_list = [six.int2byte(msg_type), msg_str]

    print "Send Server Info Request Message."
    socket.send_multipart(msg_list)
    # print msg_list

    # 接收应答消息
    receive_message = socket.recv_multipart()
    print "receive Server Info Response Message."
    msg_server_info_response = AllProtoMsg_pb2.ServerInfoResponseMsg()
    msg_server_info_response.ParseFromString(zlib.decompress(receive_message[1]))
    print receive_message[1]



if __name__ == '__main__':
    server_info_request_msg()