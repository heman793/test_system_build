# -*- coding: utf-8 -*-

import six
import AllProtoMsg_pb2
import zlib
from socket_init import socket_init

def instrument_info_request_msg():
    socket = socket_init()
    # 拼消息
    msg_instrument_info_request = AllProtoMsg_pb2.InstrumentInfoRequestMsg()
    msg_instrument_info_request.IsAll = True
    msg_instrument_info_request.IncludeStaticInfo = True

    # 序列化
    msg_str = msg_instrument_info_request.SerializeToString()
    msg_type = 2
    msg_list = [six.int2byte(msg_type), msg_str]

    # print "Send Instrument Info Request Message."
    socket.send_multipart(msg_list)
    # print msg_list

    # 接收应答消息
    receive_message = socket.recv_multipart()
    # print "receive Instrument Info Response Message."
    msg_instrument_info_response = AllProtoMsg_pb2.InstrumentInfoResponseMsg()
    msg_instrument_info_response.ParseFromString(zlib.decompress(receive_message[1]))

    instrument_msg_dict = dict()
    for instrument_msg in msg_instrument_info_response.Targets:
        instrument_msg_dict[instrument_msg.id] = instrument_msg
        # print (instrument_msg_dict)

    market_msg_dict = dict()
    for market_msg in msg_instrument_info_response.Infos:
        market_msg_dict[market_msg.ID] = market_msg
        # print (market_msg_dict)
    return instrument_msg_dict, market_msg_dict

if __name__ == '__main__':
    instrument_info_request_msg()