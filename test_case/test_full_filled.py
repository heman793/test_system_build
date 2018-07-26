# -*- coding: utf-8 -*-

import unittest
from message.new_limit_order_msg import New_Order_Msg
import pandas as pd
from message.order_details import *

class TestFullFilled(unittest.TestCase,  New_Order_Msg):
    def setUp(self):
        New_Order_Msg.__init__(self)

    def send_order_msg(self, clientid):
        r = self.new_order_message(clientid)
        # print r

    def get_expect_result(self, clientid):
        test_type = 'all'
        filename = 'strategy_loader_%s.csv' % test_type
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         index_col="test_case_no")
        expect_result = df.at[clientid, 'expect_result']
        return expect_result

    def get_actual_result(self, clientid):
        order_list = query_order_by_clientid(clientid)
        for order in order_list:
            if order['TradeVol'] == order['OrdVol']:
                actual_result = "FullFilled"
            elif order['TradeVol'] < order['OrdVol'] and order['TradeVol'] > 0:
                actual_result = "PartialFilled"
            else:
                actual_result = 'NoFilled'
        return actual_result

    def genaral_test_xxx_testcase(self, clientid):
        expect = self.get_expect_result(clientid)
        actual = self.get_actual_result(clientid)
        print 'expect result is ' + expect
        print 'actual result is ' + actual
        self.assertEqual(actual, expect)


    def test_full_filled_future_buy_open(self):
        clientid = 'ts0001'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_future_sell_close(self):
        clientid = 'ts0002'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_future_sell_open(self):
        clientid = 'ts0003'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_future_buy_close(self):
        clientid = 'ts0004'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_stock_buy_normal(self):
        clientid = 'ts0005'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_stock_sell_normal(self):
        clientid = 'ts0006'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_etf_buy_normal(self):
        clientid = 'ts0007'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_etf_sell_normal(self):
        clientid = 'ts0008'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_mmf_buy_normal(self):
        clientid = 'ts0009'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_mmf_sell_normal(self):
        clientid = 'ts0010'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_sf_buy_normal(self):
        clientid = 'ts0011'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_full_filled_sf_sell_normal(self):
        clientid = 'ts0012'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
