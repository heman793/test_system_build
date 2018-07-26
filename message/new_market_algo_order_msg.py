# -*- coding: utf-8 -*-

import six
import AllProtoMsg_pb2
import time
from public.main_config import *
from data_prepare.common.config_common import ConfigCommon
import random
import pandas as pd

class New_Order_Msg(ConfigCommon):
    def __init__(self):
        ConfigCommon.__init__(self)
        self.ini_input_dict = self.get_ini_input_dict()

    def new_order_message(self, clientid):
        test_type = 'all'
        file = '%s_%s_%s_market.csv' % (clientid, stock_account, strategy)
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, file),
                         dtype={'target': str})

        msg_algo = AllProtoMsg_pb2.AlgoParameter()
        msg_algo.AlgoNameWired = 3

        msg_child_algo0 = AllProtoMsg_pb2.AlgoParameter()
        msg_child_algo0.AlgoNameWired = df.at[0, 'algo_type']


        msg_child_algo1 = AllProtoMsg_pb2.AlgoParameter()
        msg_child_algo1.AlgoNameWired = df.at[1, 'algo_type']

        msg_child_algo2 = AllProtoMsg_pb2.AlgoParameter()
        msg_child_algo2.AlgoNameWired = df.at[2, 'algo_type']



        msg_child0 = AllProtoMsg_pb2.Order()
        msg_child0.TradeTypeWire = df.at[0, 'trade_type']
        msg_child0.TypeWire = df.at[0, 'type']
        msg_child0.Qty = df.at[0, 'order_qty']
        msg_child0.Price = self.get_target_pre_price(df.at[0,'target'])
        msg_child0.DirectionWire = df.at[0, 'direction']
        msg_child0.CliOrdID = df.at[0, 'clientid']
        msg_child0.ParentOrderID = clientid
        msg_child0.Parameters.CopyFrom(msg_child_algo0)

        msg_child1 = AllProtoMsg_pb2.Order()
        msg_child1.TradeTypeWire = df.at[1, 'trade_type']
        msg_child1.TypeWire = df.at[1, 'type']
        msg_child1.Qty = df.at[1, 'order_qty']
        msg_child1.Price = self.get_target_pre_price(df.at[1, 'target'])
        msg_child1.DirectionWire = df.at[1, 'direction']
        msg_child1.CliOrdID = df.at[1, 'clientid']
        msg_child1.ParentOrderID = clientid
        msg_child1.Parameters.CopyFrom(msg_child_algo1)

        msg_child2 = AllProtoMsg_pb2.Order()
        msg_child2.TradeTypeWire = df.at[2, 'trade_type']
        msg_child2.TypeWire = df.at[2, 'type']
        msg_child2.Qty = df.at[2, 'order_qty']
        msg_child2.Price = self.get_target_pre_price(df.at[2, 'target'])
        msg_child2.DirectionWire = df.at[2, 'direction']
        msg_child2.CliOrdID = df.at[2, 'clientid']
        msg_child2.ParentOrderID = clientid
        msg_child2.Parameters.CopyFrom(msg_child_algo0)

        msg_child3 = AllProtoMsg_pb2.Order()
        msg_child3.TradeTypeWire = df.at[3, 'trade_type']
        msg_child3.TypeWire = df.at[3, 'type']
        msg_child3.Qty = df.at[3, 'order_qty']
        msg_child3.Price = self.get_target_pre_price(df.at[3, 'target'])
        msg_child3.DirectionWire = df.at[3, 'direction']
        msg_child3.CliOrdID = df.at[3, 'clientid']
        msg_child3.ParentOrderID = clientid
        msg_child3.Parameters.CopyFrom(msg_child_algo1)

        msg_order = AllProtoMsg_pb2.Order()
        msg_order.TradeTypeWire = 0
        msg_order.TypeWire = 3
        msg_order.OrderAccount = stock_account
        msg_order.UserID = fund_name
        msg_order.StrategyID = strategy
        msg_order.CliOrdID = clientid
        msg_order.Parameters.CopyFrom(msg_algo)

        msg = AllProtoMsg_pb2.NewOrderMsg()
        msg_child_0 = AllProtoMsg_pb2.NewOrderMsg()
        msg_child_0 = msg.childOrdersWire.add()
        msg_child_0.TargetID = random.randint(0, 99)
        msg_child_0.Order.MergeFrom(msg_child0)
        msg_child_0.Symbol = df.at[0, 'target']

        msg_child_1 = AllProtoMsg_pb2.NewOrderMsg()
        msg_child_1 = msg.childOrdersWire.add()
        msg_child_1.TargetID = random.randint(0, 99)
        msg_child_1.Order.MergeFrom(msg_child1)
        msg_child_1.Symbol = df.at[1, 'target']

        msg_child_2 = AllProtoMsg_pb2.NewOrderMsg()
        msg_child_2 = msg.childOrdersWire.add()
        msg_child_2.TargetID = random.randint(0, 99)
        msg_child_2.Order.MergeFrom(msg_child1)
        msg_child_2.Symbol = df.at[2, 'target']

        msg_child_3 = AllProtoMsg_pb2.NewOrderMsg()
        msg_child_3 = msg.childOrdersWire.add()
        msg_child_3.TargetID = random.randint(0, 99)
        msg_child_3.Order.MergeFrom(msg_child1)
        msg_child_3.Symbol = df.at[3, 'target']

        msg.TargetID = 0
        msg.Order.MergeFrom(msg_order)
        msg.Symbol = df.at[1, 'target']

        msg_str = msg.SerializeToString()
        msg_type = 4
        msg_list = [six.int2byte(msg_type), msg_str]
        return msg_list

if __name__ == "__main__":
    parentid = 'mkt0001'
    new_msg = New_Order_Msg()
    new_msg.new_order_message(parentid)