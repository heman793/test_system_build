# -*- coding: utf-8 -*-

import six
import zmq
import AllProtoMsg_pb2
import time
from public.main_config import *
from data_prepare.common.config_common import ConfigCommon
import random
import pandas as pd
import socket_init

class New_Order_Msg(ConfigCommon):
    def __init__(self):
        ConfigCommon.__init__(self)
        self.ini_input_dict = self.get_ini_input_dict()

    def new_order_message(self):
        context = zmq.Context().instance()
        # print "Connecting to server"
        socket = context.socket(zmq.DEALER)
        socket.setsockopt(zmq.IDENTITY, b'127.0.0.1_real')
        socket.connect(socket_connect_dict)

        file = '%s_%s_%s_sigmavwap.csv' % (clientid, stock_account, strategy)
        df = pd.read_csv(os.path.join(strategy_config_path, file),
                         dtype={'target': str})

        msg_algo = AllProtoMsg_pb2.AlgoParameter()
        msg_algo.AlgoNameWired = 3

        msg_child_algo = AllProtoMsg_pb2.AlgoParameter()
        msg_child_algo.AlgoNameWired = 16

        for ind in df.index.values:
            msg_child1 = AllProtoMsg_pb2.Order()
            msg_child1.TradeTypeWire = df.at[0, 'trade_type']
            msg_child1.TypeWire = df.at[0, 'type']
            msg_child1.PropertyWire = 0
            msg_child1.Qty = df.at[0, 'order_qty']
            msg_child1.Price = df.at[0, 'pre_prc']
            msg_child1.DirectionWire = df.at[0, 'direction']
            msg_child1.StatusWire = -1
            msg_child1.OperationStatusWire = -1
            msg_child1.OrderAccount = stock_account
            msg_child1.UserID = algo_fund
            msg_child1.StrategyID = strategy
            msg_child1.CliOrdID = clientid
            msg_child1.Parameters.CopyFrom(msg_child_algo)

            msg_child2 = AllProtoMsg_pb2.Order()
            msg_child2.TradeTypeWire = df.at[1, 'trade_type']
            msg_child2.TypeWire = df.at[1, 'type']
            msg_child2.PropertyWire = 0
            msg_child2.Qty = df.at[1, 'order_qty']
            msg_child2.Price = df.at[1, 'pre_prc']
            msg_child2.DirectionWire = df.at[1, 'direction']
            msg_child2.StatusWire = -1
            msg_child2.OperationStatusWire = -1
            msg_child2.OrderAccount = stock_account
            msg_child2.UserID = algo_fund
            msg_child2.StrategyID = strategy
            msg_child2.CliOrdID = clientid
            msg_child2.Parameters.CopyFrom(msg_child_algo)

            msg_order = AllProtoMsg_pb2.Order()
            msg_order.TradeTypeWire = 0
            msg_order.TypeWire = 3
            msg_order.PropertyWire = 0
            msg_order.Qty = df.at[ind, 'order_qty']
            msg_order.Price = df.at[ind, 'pre_prc']
            msg_order.DirectionWire = 1
            msg_order.StatusWire = -1
            msg_order.OperationStatusWire = -1
            msg_order.OrderAccount = stock_account
            msg_order.UserID = algo_fund
            msg_order.StrategyID = strategy
            msg_order.CliOrdID = clientid
            msg_order.Parameters.CopyFrom(msg_algo)

            msg = AllProtoMsg_pb2.NewOrderMsg()
            msg_child_1 = AllProtoMsg_pb2.NewOrderMsg()
            msg_child_1 = msg.childOrdersWire.add()
            msg_child_1.TargetID = random.randint(0, 99)
            msg_child_1.Order.MergeFrom(msg_child1)
            msg_child_1.Symbol = df.at[0, 'target']

            msg_child_2 = AllProtoMsg_pb2.NewOrderMsg()
            msg_child_2 = msg.childOrdersWire.add()
            msg_child_2.TargetID = random.randint(0, 99)
            msg_child_2.Order.MergeFrom(msg_child2)
            msg_child_2.Symbol = df.at[1, 'target']

            msg.TargetID = 0
            msg.Order.MergeFrom(msg_order)
            msg.Symbol = df.at[ind, 'target']

        print msg
        msg_str = msg.SerializeToString()
        msg_type = 4
        msg_list = [six.int2byte(msg_type), msg_str]
        # print msg_list

        socket.send_multipart(msg_list)

        print "Send New Order Message."

        time.sleep(2)
        socket.close()

if __name__ == "__main__":
    clientid = 'ag0003'
    new_msg = New_Order_Msg()
    new_msg.new_order_message()