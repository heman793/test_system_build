# -*- coding: utf-8 -*-

from message.order_info_algo_request_msg import *
from model.eod_const import const, CustomEnumUtils
from tools.date_utils import DateUtils
from message.instrument_info_request_msg import *
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
    order_qty = 0
    trade_qty = 0
    ext_qty = 0
    ord_prc = 0.0
    ext_prc = 0.0
    direction = None
    algo_status = None
    strategy_id = None
    user_id = None
    order_account = None
    creation_time = None
    transaction_time = None
    parent_order_id = None
    order_type = 0
    trade_type = 0
    nominal_type = 0
    cliordid = None


def __init__(self):
    pass

def __query_order_list(clientid):
    # instrument_dict, market_dict = instrument_info_request_msg()
    order_msg_list = order_info_request_msg()
    # print order_msg_list

    query_order_list = []
    for order_info in order_msg_list:
        # ticker = None
        # if order_info.TargetID in instrument_dict:
        #     ticker = instrument_dict[order_info.TargetID].ticker

        order_view = OrderView()
        order_view.order_type = order_info.Order.TypeWire
        order_view.strategy_id = order_info.Order.StrategyID
        order_view.ticker = order_info.Symbol
        order_view.order_status = order_info.Order.StatusWire
        order_view.operation_status = order_info.Order.OperationStatusWire
        order_view.algo_status = order_info.Order.AlgoStatus
        order_view.ord_prc = order_info.Order.Price
        order_view.order_qty = order_info.Order.Qty
        order_view.ext_qty = order_info.Order.ExQty
        order_view.trade_qty = order_info.Order.ExQty
        order_view.ext_prc = order_info.Order.ExAvgPrice
        order_view.creation_time = order_info.Order.CreationTime
        order_view.transaction_time = order_info.Order.TransactionTime
        order_view.order_account = order_info.Order.OrderAccount
        order_view.id = order_info.Order.ID
        order_view.parent_order_id = order_info.Order.ParentOrderID
        order_view.cliordid = clientid
        order_view.trade_type = order_info.Order.TradeTypeWire
        order_view.nominal_type = order_info.Order.NominalTradeTypeWire
        query_order_list.append(order_view)
    return query_order_list

def query_order_list(clientid):
    order_view_list = __query_order_list(clientid)
    parent_view_list = []
    child1_view_list = []
    child2_view_list = []
    for order_view in order_view_list:
        if order_view.parent_order_id.strip() == "" and order_view.order_type\
                == 3:
            parent_view_list = parent_view_list.append(order_view)
            # print '*** parent_view_list is %s' % order_view.id
        elif order_view.order_type == 2:
            child1_view_list.append(order_view)
            # print '--- child1_view_list is %s' % order_view.id
        else:
            child2_view_list.append(order_view)
            # print '--- child2_view_list is %s' % order_view.id
    print parent_view_list, child1_view_list, child2_view_list
    return parent_view_list, child1_view_list, child2_view_list


def query_parent_id_by_clientid(clientid):
    parent_view_list = __query_order_list(clientid)
    parent_id_listA = []
    for order_view in parent_view_list:
        if order_view.parent_order_id.strip() != "" and order_view.order_type\
                != 2:
            parentid = order_view.parent_order_id
            parent_id_listA.append(parentid)
    parent_id_listB = list(set(parent_id_listA))
    print parent_id_listB
    return parent_id_listB

def query_child_list_by_parentid(parentid):
    child2_view_list = __query_order_list(clientid)
    trade_qty = 0

    for order_view in child2_view_list:
        if order_view.parent_order_id == parentid:
            ticker = order_view.ticker
            trade_qty += order_view.ext_qty
    print trade_qty, ticker, parentid
    return trade_qty

# def query_all_child_trade_qty(clientid):
#     parentid_list = query_parent_id_by_clientid(clientid)
#     for parentid in parentid_list:
#         trade_qty = query_child_list_by_parentid(parentid)
#         if trade_qty == order_view.order_qty:




if __name__ == '__main__':
    clientid = 'ag0003'
    parentid = 'DbG00001'
    order_view = OrderView()
    # query_order_list(clientid)
    # order_id = query_orderid_by_clientid(clientid='ts0001')
    # cancel_all_msg(self='self')
    # query_need_cancel_orders()
    query_child_list_by_parentid(parentid)
    # query_parent_id_by_clientid(clientid)
    # calculator_child_list_trade_qty(clientid)