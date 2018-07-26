# -*- coding: utf-8 -*-

import six
import AllProtoMsg_pb2
import zlib
import zmq
from random import randint
from public.main_config import *
import pandas as pd
import sys
import types
import json
import re

def __strategy_info_request_msg():
    context = zmq.Context().instance()
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, bytes(randint(10000000, 999999999)))
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(socket_connect_dict)

    msg = AllProtoMsg_pb2.StrategyInfoRequestMsg()
    msg.IsFirstRequest = True

    # 序列化
    msg_str = msg.SerializeToString()
    msg_type = 14
    msg_list = [six.int2byte(msg_type), msg_str]

    # print "Send strategy Info Request Message."
    socket.send_multipart(msg_list)

    # 接收应答消息
    filename = 'AutoTestOrder.csv'
    df = pd.read_csv(os.path.join(future_strategy_para_path, filename),
                     index_col='order')
    num = len(df)

    # this message will receive several response, according to the process
    # StrategyLoad is the last order process
    for response in range(1, num+1):
        recv_message = socket.recv_multipart()
        strategy_info_response_msg = AllProtoMsg_pb2.StrategyInfoResponseMsg()
        strategy_info_response_msg.ParseFromString(zlib.decompress(recv_message[1]))
    # print strategy_info_response_msg
    return strategy_info_response_msg

    socket.close()
    context.term()

def query_strategy_status():
    strategy_status_dict = dict()
    strategy_info_response_msg = __strategy_info_request_msg()
    # print strategy_info_response_msg
    for strats_info in strategy_info_response_msg.Strats:
        strategy_status_dict['%s' % strats_info.Name] = strats_info.IsEnabled
    # print strategy_status_dict['BBreaker.rb_1min_para1']
    return strategy_status_dict

def query_strategy_parameters():
    strategy_parameter_dict = dict()
    strategy_info_response_msg = __strategy_info_request_msg()
    # print strategy_info_response_msg
    for strats_info in strategy_info_response_msg.Strats:
        strategy_parameter_dict['%s' % strats_info.Name] = strats_info.Parameter
    # print strategy_parameter_dict['BBreaker.rb_1min_para1']
    return strategy_parameter_dict

def query_strategy_variables():
    strategy_variable_dict = dict()
    strategy_info_response_msg = __strategy_info_request_msg()
    # print strategy_info_response_msg
    for strats_info in strategy_info_response_msg.Strats:
        strategy_variable_dict['%s' % strats_info.Name] = strats_info.Variable
    # print strategy_variable_dict
    return strategy_variable_dict

def query_strategy_states():
    strategy_state_dict = dict()
    strategy_info_response_msg = __strategy_info_request_msg()
    # print strategy_info_response_msg
    for strats_info in strategy_info_response_msg.Strats:
        strategy_state_dict['%s' % strats_info.Name] = strats_info.State
    # print type(strategy_state_dict)
    return strategy_state_dict

def query_strategy_static_info():
    strategy_static_info_dict = dict()
    strategy_info_response_msg = __strategy_info_request_msg()
    # print strategy_info_response_msg
    for strats_info in strategy_info_response_msg.Strats:
        strategy_static_info_dict['%s' % strats_info.Name] = strats_info.StaticInfo
    # print strategy_static_info_dict
    return strategy_static_info_dict

def get_dict_value(dict, objkey, default=None):
    tmp = dict
    for key, value in tmp.items():
        if key == objkey:
            return value
        else:
            if type(value) is types.DictType:
                ret = get_dict_value(value, objkey, default)
                if ret is not default:
                    return ret
    return default

if __name__ == '__main__':
    # strategy_name = 'HighLowBandADX.cu_15min_para1'
    # __strategy_info_request_msg()
    __strategy_info_request_msg()
    # strategy_parameter_dict = query_strategy_parameters()
    # ret = get_dict_value(strategy_parameter_dict, 'HighLowBandADX.cu_15min_para1',
    #                      default=None )
    #
    # data = str(ret)
    # print data