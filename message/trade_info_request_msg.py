# -*- coding: utf-8 -*-

import six
import zmq
import AllProtoMsg_pb2
from public.main_config import *
import zlib

def trade_info_request_msg():
    context = zmq.Context().instance()
    print "Connecting to server"
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, b'127.0.0.1_real')
    socket.connect(socket_connect_dict)
    # 发请求
    msg_trade_info_request = AllProtoMsg_pb2.TradeInfoRequestMsg()

    # 序列化
    msg_str = msg_trade_info_request.SerializeToString()
    msg_type = 17
    msg_list = [six.int2byte(msg_type), msg_str]

    print "Send Order Info Request Message."
    socket.send_multipart(msg_list)
    # print msg_list

    # 接收应答消息
    receive_message = socket.recv_multipart()
    print "receive Order Info Response Message."
    msg_trade_info_response = AllProtoMsg_pb2.TradeInfoResponseMsg()
    msg_trade_info_response.ParseFromString(zlib.decompress(receive_message[1]))

    trade_msg_list = []
    for trade_info in msg_trade_info_response.Trades:
        trade_msg_list.append(trade_info)
        print trade_msg_list
    return trade_msg_list


if __name__ == '__main__':
    trade_info_request_msg()