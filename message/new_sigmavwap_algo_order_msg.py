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

        # TradeTypeWire字段定义
        # Normal = 0, Short = 1, Open = 2, Close = 3, CloseYesterday = 4,
        # RedPur = 5, MergeSplit = 6, NA = 7, Exercise = 8, Merge = 9, Split = 10, Creation = 11, Redemption = 12
        # DirectionWire字段定义
        # Buy = 1, Sell = -1, Creation = 2, Redemption = 3
        # PeggedLevel:SameSide = 100 OppsiteSide = -100

        file = '%s_%s_sigmavwap.csv' % (stock_account, strategy)
        test_type = 'all'
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, file),
                         dtype={'target': str}, index_col='clientid')
        # print df

        msg_algo = AllProtoMsg_pb2.AlgoParameter()
        msg_algo.AlgoNameWired = 16

        msg = AllProtoMsg_pb2.NewOrderMsg()


        msg_order_child = AllProtoMsg_pb2.Order()
        msg_order_child.TradeTypeWire = df.at[clientid, 'trade_type']
        msg_order_child.TypeWire = df.at[clientid, 'type']
        msg_order_child.PropertyWire = 0
        msg_order_child.Qty = df.at[clientid, 'order_qty']
        msg_order_child.Price = self.get_target_pre_price(df.at[clientid,
                                                                    'target'])
        msg_order_child.DirectionWire = df.at[clientid, 'direction']
        msg_order_child.StatusWire = -1
        msg_order_child.OperationStatusWire = -1
        msg_order_child.OrderAccount = stock_account
        msg_order_child.UserID = fund_name
        msg_order_child.StrategyID = strategy
        msg_order_child.CliOrdID = clientid
        msg_order_child.Parameters.CopyFrom(msg_algo)

        msg_child = AllProtoMsg_pb2.NewOrderMsg()
        msg_child = msg.childOrdersWire.add()
        msg_child.TargetID = random.randint(0, 99)
        msg_child.Order.CopyFrom(msg_order_child)
        msg_child.Symbol = df.at[clientid, 'target']


        msg.TargetID = 0
        msg.Order.CopyFrom(msg_order_child)
        msg.Symbol = df.at[clientid, 'target']
        # print msg

        msg_str = msg.SerializeToString()
        msg_type = 4
        msg_list = [six.int2byte(msg_type), msg_str]
        return msg_list

if __name__ == "__main__":
    clientid = 'sigma0001'
    new_msg = New_Order_Msg()
    new_msg.new_order_message(clientid)