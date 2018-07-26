# -*- coding: utf-8 -*-
import six
import AllProtoMsg_pb2
from public.main_config import *
import pandas as pd

class PhoneTrade():
    def __init__(self):
        pass

    def phone_trade_message(self, IOType, clientid):
        filename = 'phone_trade_%s.csv' % IOType
        test_type = 'all'
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         dtype={'symbol':str, 'ex_price':float, 'clientid':str},
                         index_col='clientid')

        msg = AllProtoMsg_pb2.PhoneTradeRequestMsg()

        # for test_id in df.index.values:
        phone_trade_item = msg.Trades.add()
        phone_trade_item.Fund = df.at[clientid, "fund"]
        phone_trade_item.Strategy1 = df.at[clientid, "strategy1"]
        phone_trade_item.Strategy2 = df.at[clientid, "strategy2"]
        phone_trade_item.Symbol = df.at[clientid, "symbol"]
        phone_trade_item.Direction = df.at[clientid, "direction"]
        phone_trade_item.TradeType = df.at[clientid, "trade_type"]
        phone_trade_item.HedgeFlag = df.at[clientid, "hedge_flag"]
        phone_trade_item.ExPrice = df.at[clientid, "ex_price"]
        phone_trade_item.ExQty = df.at[clientid, "ex_qty"]
        phone_trade_item.IOType = df.at[clientid, "io_type"]

        msg.Location = df.at[clientid, "connect_address"]

        print "Send PhoneTradeItem"
        msg_str = msg.SerializeToString()
        msg_type = 29
        msg_list = [six.int2byte(msg_type), msg_str]
        return msg_list

if __name__ == "__main__":
    IOType = 'inner1'
    clientid = 'pt1'
    phone_trade = PhoneTrade()
    phone_trade.phone_trade_message(IOType, clientid)