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

    def new_order_message(self, clientid):
        context = zmq.Context().instance()
        # print "Connecting to server"
        socket = context.socket(zmq.DEALER)
        socket.setsockopt(zmq.IDENTITY, b'127.0.0.1_real')
        socket.connect(socket_connect_dict)

        # TradeTypeWire字段定义
        # Normal = 0, Short = 1, Open = 2, Close = 3, CloseYesterday = 4,
        # RedPur = 5, MergeSplit = 6, NA = 7, Exercise = 8, Merge = 9, Split = 10, Creation = 11, Redemption = 12
        # DirectionWire字段定义
        # Buy = 1, Sell = -1, Creation = 2, Redemption = 3
        test_type = 'all'
        filename = 'strategy_loader_%s.csv' % test_type
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         index_col="test_case_no")
        msg_order = AllProtoMsg_pb2.Order()
        msg_order.TradeTypeWire = df.at[clientid, 'trade_type']
        msg_order.TypeWire = 1
        msg_order.PropertyWire = 0
        msg_order.Qty = df.at[clientid, 'order_qty']
        msg_order.Price = df.at[clientid, 'pre_prc']
        msg_order.DirectionWire = df.at[clientid, 'direction']
        msg_order.StatusWire = -1
        msg_order.OperationStatusWire = -1
        msg_order.OrderAccount = df.at[clientid, 'account']
        msg_order.UserID = df.at[clientid, 'user_id']
        msg_order.StrategyID = df.at[clientid, 'strategy_account']
        msg_order.CliOrdID = clientid
        msg = AllProtoMsg_pb2.NewOrderMsg()
        msg.TargetID = random.randint(1, 99)
        msg.Order.CopyFrom(msg_order)
        msg.Location = '4'
        msg.Symbol = df.at[clientid, 'target']
        # print msg

        msg_str = msg.SerializeToString()
        msg_type = 4
        msg_list = [six.int2byte(msg_type), msg_str]
        socket.send_multipart(msg_list)

        # print "Send New Order Message."

        time.sleep(2)
        socket.close()

if __name__ == "__main__":
    clientid = 'ts0002'
    new_msg = New_Order_Msg()
    new_msg.new_order_message(clientid)