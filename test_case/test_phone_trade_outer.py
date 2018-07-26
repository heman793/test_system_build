# -*- coding: utf-8 -*-

import unittest
from message.phone_trade_msg import PhoneTrade
import pandas as pd
from message.order_details import *
from random import randint
import time

IOType = 'outer'
class TestPhoneTrade(unittest.TestCase, PhoneTrade):
    def setUp(self):
        PhoneTrade.__init__(self)
        self.context = zmq.Context().instance()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, bytes(randint(10000000, 999999999)))
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(socket_connect_dict)

    def get_expect_result(self, IOType, clientid):
        filename = 'phone_trade_%s.csv' % IOType
        strategy_config_path = os.path.join(version_path, 'all_Config')
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         index_col="clientid")
        expect_result = df.at[clientid, 'expect_result']
        symbol = df.at[clientid, 'symbol']
        Qty = df.at[clientid, 'ex_qty']
        print "OrderInfo is symbol:%s, Qty:%s, clientid:%s" % (
        symbol, Qty, clientid)
        return expect_result

    def get_actual_result(self, clientid):
        actual_result = True
        # order_list = query_order_by_clientid(clientid)

        # for order in order_list:
        #     print "order id is %s" % order['OrderID']
        #     print "client id is %s" % order['CliOrdID']
        #     if order['TradeVol'] == order['OrdVol']:
        #         actual_result = True
        #     else:
        #         actual_result = False
        #         print order['Note']
            # print actual_result
        return actual_result

    def genaral_test_xxx_testcase(self, IOType, clientid):
        self.phone_trade_message(IOType, clientid)
        expect = self.get_expect_result(IOType, clientid)
        actual = self.get_actual_result(clientid)
        print 'expect result is: %s, actual result is: %s' % (expect, actual)
        self.assertEqual(actual, expect)

    def test_outer_stock_buy_normal(self):
        clientid = 'pto10'
        self.genaral_test_xxx_testcase(IOType, clientid)

    def test_outer_stock_sell_normal(self):
        clientid = 'pto20'
        self.genaral_test_xxx_testcase(IOType, clientid)

    def test_outer_future_buy_open(self):
        clientid = 'pto30'
        self.genaral_test_xxx_testcase(IOType, clientid)

    def test_outer_future_sell_close(self):
        clientid = 'pto40'
        self.genaral_test_xxx_testcase(IOType, clientid)

    def test_outer_future_sell_open(self):
        clientid = 'pto50'
        self.genaral_test_xxx_testcase(IOType, clientid)

    def test_outer_future_buy_close(self):
        clientid = 'pto60'
        self.genaral_test_xxx_testcase(IOType, clientid)


    def test_outer_option_buy_open(self):
        clientid = 'pto70'
        self.genaral_test_xxx_testcase(IOType, clientid)
    #
    def test_outer_option_sell_close(self):
        clientid = 'pto80'
        self.genaral_test_xxx_testcase(IOType, clientid)

    def test_outer_option_sell_open(self):
        clientid = 'pto90'
        self.genaral_test_xxx_testcase(IOType, clientid)

    def test_outer_option_buy_close(self):
        clientid = 'pto100'
        self.genaral_test_xxx_testcase(IOType, clientid)

    def tearDown(self):
        self.socket.close()
        self.context.term()

if __name__ == '__main__':
    unittest.main()
