# -*- coding: utf-8 -*-

import six
import AllProtoMsg_pb2
from socket_init import socket_init

def position_risk_request():
    socket = socket_init()

    # 拼消息
    msg_position_risk_request = AllProtoMsg_pb2.PositionRiskRequestMsg()

    # 序列化
    msg_str = msg_position_risk_request.SerializeToString()
    msg_type = 19
    msg_list = [six.int2byte(msg_type), msg_str]

    print "Send Position Risk Request Message."
    socket.send_multipart(msg_list)

    receive_message = socket.recv_multipart()
    print "Receive Message Success."
    position_risk_msg = AllProtoMsg_pb2.PositionRiskResponseMsg()
    position_risk_msg.ParseFromString((position_risk_msg.Holdings))
    print (receive_message[1])

    instrument_info_msg = AllProtoMsg_pb2.InstrumentInfoResponseMsg()
    instrument_info_msg.ParseFromString(instrument_info_msg.Targets)

    targets_msg_dict = dict()
    for instrument_msg in instrument_info_msg.Targets:
        targets_msg_dict[instrument_msg.id] = instrument_msg
    # for market_msg in instrument_info_msg.Infos:
    #     instrument_info = targets_msg_dict[market_msg.ID]
    return targets_msg_dict
    # print(targets_msg_dict)

    risk_msg_list = position_risk_msg(socket)
    for risk_item in risk_msg_list:
        account_name = risk_item.Key
        for position_item in risk_item.Value:
            instrument_msg = instrument_dict[position_item.Key]
            market_msg = market_dict[position_item.Key]
            risk_view = RiskView(instrument_msg, market_msg, position_item.Value, account_name)
            risk_view.print_info()
    # for market_msg in instrument_info_msg.Infos:
    #     instrument_info = targets_msg_dict[market_msg.ID]
    #     print(targets_msg_dict)
    return targets_msg_dict


if __name__ == '__main__':
    position_risk_request()