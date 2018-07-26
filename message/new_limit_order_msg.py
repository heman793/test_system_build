# -*- coding: utf-8 -*-

import six
import AllProtoMsg_pb2
from public.main_config import *
from data_prepare.common.config_common import ConfigCommon
import random
import pandas as pd


class New_Order_Msg(ConfigCommon):
    def __init__(self):
        ConfigCommon.__init__(self)
        self.ini_input_dict = self.get_ini_input_dict()

    def get_target_pre_price(self, ticker):
        sql_command = "select prev_close, ticker from instrument "
        df = pd.read_sql_query(sql_command, con=get_conn_db("common"),
                            index_col='ticker')
        pre_close = df.at[ticker, 'prev_close']
        return pre_close

    def new_order_message(self, clientid):
        test_type = 'all'
        filename = 'test_data_%s.csv' % test_type
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         index_col="test_case_no")

        msg_order = AllProtoMsg_pb2.Order()
        msg_order.TradeTypeWire = df.at[clientid, 'trade_type']
        msg_order.TypeWire = 1
        msg_order.PropertyWire = 0
        msg_order.Qty = df.at[clientid, 'order_qty']
        msg_order.Price = self.get_target_pre_price(df.at[clientid, 'target'])
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

        msg_str = msg.SerializeToString()
        msg_type = 4
        msg_list = [six.int2byte(msg_type), msg_str]
        return msg_list

if __name__ == "__main__":
    clientid = 'ts0002'
    new_msg = New_Order_Msg()
    new_msg.new_order_message(clientid)