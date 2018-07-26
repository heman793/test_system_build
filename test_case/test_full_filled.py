# -*- coding: utf-8 -*-

import unittest
from message.new_limit_order_msg import New_Order_Msg
import pandas as pd
from message.order_details import *
from random import randint
# from message.socket_init import *
import time

class TestFullFilled(unittest.TestCase,  New_Order_Msg):
    def setUp(self):
        New_Order_Msg.__init__(self)
        self.context = zmq.Context().instance()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, bytes(randint(10000000, 999999999)))
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(socket_connect_dict)

    def send_order_msg(self, clientid):
        msg_list = self.new_order_message(clientid)
        self.socket.send_multipart(msg_list)
        time.sleep(8)

    def get_expect_result(self, clientid):
        test_type = 'all'
        filename = 'test_data_%s.csv' % test_type
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         index_col="test_case_no")
        expect_result = df.at[clientid, 'expect_result']
        symbol = df.at[clientid, 'target']
        Qty = df.at[clientid, 'order_qty']
        print "OrderInfo is symbol:%s, Qty:%s, clientid:%s" % (
        symbol, Qty, clientid)
        return expect_result

    def get_actual_result(self, clientid):
        order_list = query_order_by_clientid(clientid)
        # actual_result = False
        for order in order_list:
            print "order id: %s, client id: %s" % (order['OrderID'],
                                                   order['CliOrdID'])
            if order['Status'] == 2:
                actual_result = "FullFilled"
            elif order['Status'] == 0:
                actual_result = "New"
            elif order['Status'] == 1:
                actual_result = "PartialFilled"
            elif order['Status'] == 4:
                actual_result = "Canceled"
            elif order['Status'] == 8:
                actual_result = 'Rejected'
                print order['Note']
            else:
                actual_result = "NoFilled"
        return actual_result

    def genaral_test_xxx_testcase(self, clientid):
        expect = self.get_expect_result(clientid)
        actual = self.get_actual_result(clientid)
        print 'expect result is: %s, actual result is: %s' % (expect, actual)
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
        self.socket.close()
        self.context.term()


if __name__ == '__main__':
    unittest.main()
