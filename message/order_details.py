# -*- coding: utf-8 -*-

from message.order_info_request_msg import *
from model.eod_const import const, CustomEnumUtils
from tools.date_utils import DateUtils
from random import randint
import time

date_utils = DateUtils()

custom_enum_utils = CustomEnumUtils()
order_type_inversion_dict = custom_enum_utils.enum_to_dict(const.ORDER_TYPE_ENUMS, True)
hedgeflag_type_inversion_dict = custom_enum_utils.enum_to_dict(const.HEDGEFLAG_TYPE_ENUMS, True)
order_status_inversion_dict = custom_enum_utils.enum_to_dict(const.ORDER_STATUS_ENUMS, True)
operation_status_inversion_dict = custom_enum_utils.enum_to_dict(const.OPERATION_STATUS_ENUMS, True)
trade_type_inversion_dict = custom_enum_utils.enum_to_dict(const.TRADE_TYPE_ENUMS, True)
algo_status_inversion_dict = custom_enum_utils.enum_to_dict(const.ALGO_STATUS_ENUMS, True)

instrument_type_inversion_dict = custom_enum_utils.enum_to_dict(const.INSTRUMENT_TYPE_ENUMS, True)
market_status_inversion_dict = custom_enum_utils.enum_to_dict(const.MARKET_STATUS_ENUMS, True)
exchange_type_inversion_dict = custom_enum_utils.enum_to_dict(const.EXCHANGE_TYPE_ENUMS, True)

direction_dict = custom_enum_utils.enum_to_dict(const.DIRECTION_ENUMS)
trade_type_dict = custom_enum_utils.enum_to_dict(const.TRADE_TYPE_ENUMS)
io_type_dict = custom_enum_utils.enum_to_dict(const.IO_TYPE_ENUMS)

order_status_dict = {'-1': 'None', '0': 'New', '1': 'PartialFilled', '2':'Filled', '3':'DoneForDay',
                     '4':'Canceled',  '5':'Replace', '6':'PendingCancel', '7':'Stopped', '8':'Rejected',
                     '9':'Suspended', '10':'PendingNew', '11':'Calculated', '12':'Expired',
                     '13':'AcceptedForBidding', '14':'PendingReplace', '15':'EndAsSucceed',
                     '16':'Accepted', '17':'InternalRejected'}

operation_status_dict = {'-1':'None', '0':'New', '1':'PartialFilled', '2':'Filled', '3':'DoneForDay',
                         '4':'Canceled',  '5':'Replace', '6':'PendingCancel', '7':'Stopped',
                         '8':'Rejected', '9':'Suspended', '10':'PendingNew', '11':'Calculated',
                         '12':'Expired', '13':'Restated', '14':'PendingReplace', '15':'Accepted',
                         '16':'SubmitCancel', '17':'SubmitReplace', '18':'InternalRejected',
                         '-2':'RecoverFILL'}

order_type_dict = {'0': 'None', '1': 'LimitOrder', '2': 'SingleAlgo', '3': 'BasketAlgo',
                   '4': 'EnhancedLimitOrder', '5': 'SpecialLimitOrder', '14': 'SelfCross'}

direction_dict = {'1': 'BUY', '-1': 'SELL', '0': 'NORM'}

class OrderView:
    id = None
    ticker = None
    order_status = None
    operation_status = None
    qty = 0
    direction = None
    strategy_id = None
    user_id = None
    order_account = None
    creation_time = None
    transaction_time = None
    parent_order_id = None
    order_type = 0
    cliordid = None
    algo_status = None

def __init__(self):
    pass

def __query_order_list():
    query_order_list = []
    order_msg_dict = order_info_request_msg(None)
    for (ID, order_msg) in order_msg_dict.items():
        order_item_dict = dict()
        order_item_dict['Type'] = order_msg.Order.TypeWire
        order_item_dict['Strategy'] = order_msg.Order.StrategyID
        order_item_dict['Symbol'] = order_msg.Symbol
        order_item_dict['HedgeType'] = order_msg.Order.HedgeTypeWire
        order_item_dict['Status'] = order_msg.Order.StatusWire
        order_item_dict['OpStatus'] = order_msg.Order.OperationStatusWire
        order_item_dict['AlgoStatus'] = order_msg.Order.AlgoStatus
        order_item_dict['Price'] = order_msg.Order.Price
        order_item_dict['OrdVol'] = order_msg.Order.Qty
        order_item_dict['ExQty'] = order_msg.Order.ExQty
        order_item_dict['TradeVol'] = order_msg.Order.ExQty
        order_item_dict['ExPrice'] = order_msg.Order.ExAvgPrice
        order_item_dict['CreationT'] = order_msg.Order.CreationTime
        order_item_dict['TransactionT'] = order_msg.Order.TransactionTime
        order_item_dict['Note'] = order_msg.Order.Note
        order_item_dict['Account'] = order_msg.Order.OrderAccount
        order_item_dict['OrderID'] = order_msg.Order.ID
        order_item_dict['ParentOrderID'] = order_msg.Order.ParentOrderID
        order_item_dict['SysOrderID'] = order_msg.Order.SysID
        order_item_dict['CliOrdID'] = order_msg.Order.CliOrdID
        order_item_dict['TradeType'] = order_msg.Order.TradeTypeWire
        order_item_dict['NominalTradeType'] = order_msg.Order.NominalTradeTypeWire
        query_order_list.append(order_item_dict)
    return query_order_list


def query_order_by_clientid(clientid=None):
    order_list = __query_order_list()
    order_client_list = []
    for order_item in order_list:
        if order_item['CliOrdID'] == clientid:
            order_client_list.append(order_item)
        else:
            exit
    # print order_client_list
    return order_client_list

def query_orderid_by_clientid(clientid=None):
    order_list = __query_order_list()
    for order_item in order_list:
        if order_item['CliOrdID'] == clientid:
            order_id = order_item['OrderID']
        else:
            exit
    return order_id

def query_orderid_by_parentid(clientid=None):
    order_list = __query_order_list()
    for order_item in order_list:
        if order_item['CliOrdID'] == clientid:
            parent_order_id = order_item['ParentOrderID']
        else:
            exit
    return parent_order_id

def query_need_cancel_orders():
    order_list = __query_order_list()
    need_cancel_list = []
    for order_item in order_list:
        if order_item['Status'] not in (2, 4, 8):
            need_cancel_list.append(order_item)
    return need_cancel_list

def cancel_order_msg(clientid=None):
    context = zmq.Context().instance()
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, bytes(randint(10000000, 999999999)))
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(socket_connect_dict)

    msg = AllProtoMsg_pb2.CancelOrderMsg()
    msg.SysOrdID = query_orderid_by_clientid(clientid)
    msg_str = msg.SerializeToString()
    msg_type = 5
    msg_list = [six.int2byte(msg_type), msg_str]
    socket.send_multipart(msg_list)
    time.sleep(1)
    socket.close()
    context.term()

def cancel_all_msg():
    need_cancel_list = query_need_cancel_orders()
    for order_item in need_cancel_list:
        cancel_order_msg(order_item['CliOrdID'])

if __name__ == '__main__':
    clientid = 'ts0005'
    order_view = OrderView()
    # cancel_order_msg(clientid)
    # order_list = query_order_by_clientid(clientid)
    # order_id = query_orderid_by_clientid(clientid)
    # cancel_all_msg(self='self')
    # query_need_cancel_orders()
    query_order_by_clientid(clientid)
    # query_orderid_by_parentid(clientid)