# -*- coding: utf-8 -*-

import unittest
from message.new_sigmavwap_algo_order_msg import New_Order_Msg
import pandas as pd
from message.order_algo_details import *

class TestSigmaVWAPAlgo(unittest.TestCase,  New_Order_Msg):
    def setUp(self):
        New_Order_Msg.__init__(self)

    def send_order_msg(self):
        r = self.new_order_message()
        # print r

    def get_expect_result(self, clientid):
        pass

    def get_actual_result(self, clientid):
        pass


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

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
