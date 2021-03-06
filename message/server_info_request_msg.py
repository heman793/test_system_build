# -*- coding: utf-8 -*-

import six
import AllProtoMsg_pb2
import zlib
from socket_init import socket_init

def server_info_request_msg():
    socket = socket_init(self='self')
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

    data_source_list = []
    for server_info in msg_server_info_response.DataSources:
        data_source_list.append(server_info)
        print data_source_list

    order_route_list = []
    for server_info in msg_server_info_response.OrderRoutes:
        order_route_list.append(server_info)
        print order_route_list
    return data_source_list, order_route_list

if __name__ == '__main__':
    server_info_request_msg()