# -*- coding: utf-8 -*-
import six
import zmq
import AllProtoMsg_pb2
import zlib
from model.eod_const import const
from tools.date_utils import DateUtils
from model.server_constans import ServerConstant
import logging.config
from public.main_config import *
from random import randrange

task_logger = logging.getLogger('task')
date_utils = DateUtils()
server_constant = ServerConstant()


def socket_init():
    context = zmq.Context().instance()
    task_logger.info("Connecting to server:%s", socket_connect_dict)
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, randrange(1, 100000))
    socket.connect(socket_connect_dict)
    return socket


def send_login_msg(socket):
    msg = AllProtoMsg_pb2.LoginMsg()
    msg.UserName = 'yansheng'

    task_logger.info("Send LoginMsg")
    msg_str = msg.SerializeToString()
    msg_type = const.MSG_TYPEID_ENUMS.Login
    msg_list = [six.int2byte(msg_type), msg_str]
    socket.send_multipart(msg_list)

    recv_message = socket.recv_multipart()
    print recv_message


def send_instrument_info_request_msg(socket):
    msg = AllProtoMsg_pb2.InstrumentInfoRequestMsg()
    msg.IsAll = True
    msg.IncludeStaticInfo = True
    task_logger.info("Send InstrumentInfoRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 2
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv InstrumentInfoResponseMsg.")
    instrument_info_msg = AllProtoMsg_pb2.InstrumentInfoResponseMsg()
    instrument_info_msg.ParseFromString(zlib.decompress(recv_message[1]))

    instrument_msg_dict = dict()
    for instrument_msg in instrument_info_msg.Targets:
        instrument_msg_dict[instrument_msg.id] = instrument_msg

    market_msg_dict = dict()
    for market_msg in instrument_info_msg.Infos:
        market_msg_dict[market_msg.ID] = market_msg
    return instrument_msg_dict, market_msg_dict


def send_instrument_info_request_msg2(socket, last_update=None):
    msg = AllProtoMsg_pb2.InstrumentInfoRequestMsg()
    if last_update is not None:
        msg.IsAll = False
        msg.IncludeStaticInfo = True
        msg.LastUpdate.scale = last_update.scale
        msg.LastUpdate.value = last_update.value
    else:
        msg.IsAll = True
        msg.IncludeStaticInfo = True
    task_logger.info("Send InstrumentInfoRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 2
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv InstrumentInfoResponseMsg.")
    instrument_info_msg = AllProtoMsg_pb2.InstrumentInfoResponseMsg()
    instrument_info_msg.ParseFromString(zlib.decompress(recv_message[1]))
    return instrument_info_msg


def send_position_risk_request_msg(socket, result_type=1):
    msg = AllProtoMsg_pb2.PositionRiskRequestMsg()
    task_logger.info("Send PositionRiskRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 19
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv PositionRiskResponseMsg.")
    position_risk_msg = AllProtoMsg_pb2.PositionRiskResponseMsg()
    position_risk_msg.ParseFromString(zlib.decompress(recv_message[1]))

    if result_type == 1:
        risk_msg_list = []
        for holding_item in position_risk_msg.Holdings:
            risk_msg_list.append(holding_item)
        return risk_msg_list
    elif result_type == 2:
        position_msg_list = []
        for holding_item in position_risk_msg.Holdings2:
            position_msg_list.append(holding_item)
        return position_msg_list


def send_position_risk_request_msg2(socket):
    msg = AllProtoMsg_pb2.PositionRiskRequestMsg()
    task_logger.info("Send PositionRiskRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 19
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv PositionRiskResponseMsg.")
    position_risk_msg = AllProtoMsg_pb2.PositionRiskResponseMsg()
    position_risk_msg.ParseFromString(zlib.decompress(recv_message[1]))
    return position_risk_msg


def send_order_info_request_msg(socket):
    msg = AllProtoMsg_pb2.OrderInfoRequestMsg()
    msg.IsAll = False
    task_logger.info("Send OrderInfoRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 7
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv OrderInfoResponseMsg.")
    orderinfo_msg = AllProtoMsg_pb2.OrderInfoResponseMsg()
    orderinfo_msg.ParseFromString(zlib.decompress(recv_message[1]))

    order_msg_list = []
    for order_info in orderinfo_msg.Orders:
        order_msg_list.append(order_info)
        # print order_msg_list
    return order_msg_list


def send_order_info_request_msg2(socket, last_update=None):
    msg = AllProtoMsg_pb2.OrderInfoRequestMsg()
    if last_update is not None:
        msg.IsAll = False
        msg.LastUpdateTime.scale = last_update.scale
        msg.LastUpdateTime.value = last_update.value
    else:
        msg.IsAll = True

    task_logger.info("Send OrderInfoRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 7
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv OrderInfoResponseMsg.")
    orderinfo_msg = AllProtoMsg_pb2.OrderInfoResponseMsg()
    orderinfo_msg.ParseFromString(zlib.decompress(recv_message[1]))
    return orderinfo_msg


def send_cancel_order_msg(socket, order_id):
    msg = AllProtoMsg_pb2.CancelOrderMsg()
    msg.SysOrdID = order_id
    # A: mark as canceled
    msg.MarkAsCanceled = True
    # B: mark as fill canceled
    # msg.MarkAsFillCanceled = True

    task_logger.info("Send CancelOrderMsg:%s" % msg)
    msg_str = msg.SerializeToString()
    msg_type = 5
    msg_list = [six.int2byte(msg_type), msg_str]
    socket.send_multipart(msg_list)


def send_trade_info_request_msg(socket):
    msg = AllProtoMsg_pb2.TradeInfoRequestMsg()
    task_logger.info("Send TradeInfoRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 17
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv TradeInfoResponseMsg.")
    tradeinfo_msg = AllProtoMsg_pb2.TradeInfoResponseMsg()
    tradeinfo_msg.ParseFromString(zlib.decompress(recv_message[1]))

    trade_msg_list = []
    for trade_info in tradeinfo_msg.Trades:
        trade_msg_list.append(trade_info)
    return trade_msg_list


def send_trade_info_request_msg2(socket, last_update=None):
    msg = AllProtoMsg_pb2.TradeInfoRequestMsg()
    if last_update is not None:
        msg.LastUpdateTime.scale = last_update.scale
        msg.LastUpdateTime.value = last_update.value
    task_logger.info("Send TradeInfoRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 17
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv TradeInfoResponseMsg.")
    tradeinfo_msg = AllProtoMsg_pb2.TradeInfoResponseMsg()
    tradeinfo_msg.ParseFromString(zlib.decompress(recv_message[1]))
    return tradeinfo_msg


def send_strategy_parameter_change_request_msg(socket, strategy_name, control_flag):
    msg = AllProtoMsg_pb2.StrategyParameterChangeRequestMsg()
    msg.Name = strategy_name
    msg.IsEnable = control_flag
    task_logger.info("Send StrategyParameterChangeRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 16
    msg_list = [six.int2byte(msg_type), msg_str]
    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv Msg.")
    recv_result = six.byte2int(recv_message[0])
    print recv_result
    return recv_result


# 修改策略的Used Fund
def send_strategy_account_change_request_msg(socket, strategy_name):
    msg = AllProtoMsg_pb2.StrategyParameterChangeRequestMsg()
    msg.Name = strategy_name
    # msg.Parameter.append('{"Account": "steady_return"}')
    parameter_item = msg.Parameter.add()
    parameter_item.Key = "Account"
    parameter_item.Value = "steady_return;huize01;hongyuan01"

    task_logger.info("Send StrategyParameterChangeRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 16
    msg_list = [six.int2byte(msg_type), msg_str]
    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv Msg.")
    recv_result = six.byte2int(recv_message[0])
    print recv_result
    return recv_result


def send_serverinfo_request_msg(socket):
    msg = AllProtoMsg_pb2.ServerInfoRequestMsg()

    task_logger.info("Send ServerInfoRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 11
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv ServerInfoResponseMsg.")
    serverinfo_msg = AllProtoMsg_pb2.ServerInfoResponseMsg()
    serverinfo_msg.ParseFromString(zlib.decompress(recv_message[1]))
    return serverinfo_msg


def send_phone_trade_request_msg(socket, phone_trade_list):
    msg = AllProtoMsg_pb2.PhoneTradeRequestMsg()

    for phone_trade_info in phone_trade_list:
        phone_trade_item = msg.Trades.add()
        phone_trade_item.Fund = phone_trade_info.fund
        phone_trade_item.Strategy1 = phone_trade_info.strategy1
        phone_trade_item.Strategy2 = phone_trade_info.strategy2
        phone_trade_item.Symbol = phone_trade_info.symbol
        phone_trade_item.Direction = phone_trade_info.direction
        phone_trade_item.TradeType = phone_trade_info.tradetype
        phone_trade_item.HedgeFlag = phone_trade_info.hedgeflag
        phone_trade_item.ExPrice = float(phone_trade_info.exprice)
        phone_trade_item.ExQty = int(phone_trade_info.exqty)
        phone_trade_item.IOType = phone_trade_info.iotype

    task_logger.info("Send PhoneTradeItem")
    msg_str = msg.SerializeToString()
    msg_type = 29
    msg_list = [six.int2byte(msg_type), msg_str]
    socket.send_multipart(msg_list)


def send_tradeserverinfo_request_msg(socket):
    msg = AllProtoMsg_pb2.TradeServerInfoRequestMsg()
    task_logger.info("Send TradeServerInfoRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 21
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv TradeServerInfoResponseMsg.")
    tradeserverinfo_msg = AllProtoMsg_pb2.TradeServerInfoResponseMsg()
    tradeserverinfo_msg.ParseFromString(zlib.decompress(recv_message[1]))
    return tradeserverinfo_msg


def send_subscribetradeserverinfo_request_msg(socket, tradeserver_info_list):
    msg = AllProtoMsg_pb2.SubscribeTradeServerInfoRequestMsg()

    # msg.TradeServerInfo = tradeserver_info_list
    for tradeserver_info in tradeserver_info_list:
        msg.TradeServerInfo.append(tradeserver_info)

    task_logger.info("Send SubscribeTradeServerInfoRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 23
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv SubscribeTradeServerInfoResponseMsg.")
    subscribetradeserverinfo_msg = AllProtoMsg_pb2.SubscribeTradeServerInfoResponseMsg()
    subscribetradeserverinfo_msg.ParseFromString(zlib.decompress(recv_message[1]))
    return subscribetradeserverinfo_msg


def send_strategy_info_request_msg(socket):
    msg = AllProtoMsg_pb2.StrategyInfoRequestMsg()
    task_logger.info("Send StrategyInfoRequestMsg")
    msg_str = msg.SerializeToString()
    msg_type = 14
    msg_list = [six.int2byte(msg_type), msg_str]

    socket.send_multipart(msg_list)
    recv_message = socket.recv_multipart()
    task_logger.info("Recv StrategyInfoResponseMsg.")
    strategy_info_response_msg = AllProtoMsg_pb2.StrategyInfoResponseMsg()
    strategy_info_response_msg.ParseFromString(zlib.decompress(recv_message[1]))
    return strategy_info_response_msg


if __name__ == '__main__':
    socket = socket_init('test4')
    send_order_info_request_msg(socket)
    # reject_order_query(('600064',), '198800888077-TS-xhhm02-')
    # none_order_cancel_tools('test', 'balance01')
    # reject_order_query('guoxin')

    # send_strategy_parameter_change_request_msg(socket, 'BollingerBandReversion.rb_5min_para1', False)
    # tradeserverinfo_msg = send_strategy_account_change_request_msg(socket, 'AMACD.al_5min_para2_2')
    # tradeserverinfo_msg = send_strategy_account_change_request_msg(socket, 'CalendarSpread.SU')

