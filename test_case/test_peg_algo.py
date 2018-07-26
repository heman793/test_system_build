# -*- coding: utf-8 -*-

import unittest
from message.new_peg_algo_order_msg import New_Order_Msg
import pandas as pd
from message.order_details import *
# from message.socket_init import socket_init
import time
from random import randint

class TestPegAlgo(unittest.TestCase,  New_Order_Msg):
    def setUp(self):
        New_Order_Msg.__init__(self)
        self.context = zmq.Context().instance()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, bytes(randint(10000000, 999999999)))
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(socket_connect_dict)

    def send_order_msg(self, clientid, account_type):
        msg_list = self.new_order_message(clientid, account_type)
        self.socket.send_multipart(msg_list)
        time.sleep(5)

    def get_expect_result(self, clientid, account_type):
        test_type = 'all'
        filename = '%s_%s_peg.csv' % (account_type, strategy)
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         index_col="clientid")
        expect_result = df.at[clientid, 'expect_result']
        symbol = df.at[clientid, 'target']
        Qty = df.at[clientid, 'order_qty']
        print "OrderInfo is symbol:%s, Qty:%s, clientid:%s" % (
        symbol, Qty, clientid)
        return expect_result

    def get_actual_result(self, clientid):
        order_list = query_order_by_clientid(clientid)
        actual_result = False
        for order in order_list:
            print "order id: %s, client id: %s" % (order['OrderID'],
                                                   order['CliOrdID'])
            if order['AlgoStatus'] == 2 and order['Status'] != 8:
                actual_result = True
            elif order['AlgoStatus'] == 0 and order['TradeVol'] > 0:
                actual_result = True
            else:
                actual_result = False
                print order['Note']
        return actual_result

    def genaral_test_xxx_testcase(self, clientid, account_type):
        expect = self.get_expect_result(clientid, account_type)
        actual = self.get_actual_result(clientid)
        print 'expect result is: %s, actual result is: %s' % (expect, actual)
        self.assertEqual(expect, actual)


    def test_peg_algo_stock_buy(self):
        clientid = 'peg0001'
        account_type = stock_account
        self.send_order_msg(clientid, account_type)
        self.genaral_test_xxx_testcase(clientid,account_type)

    def test_peg_algo_stock_sell(self):
        clientid = 'peg0002'
        account_type = stock_account
        self.send_order_msg(clientid, account_type)
        self.genaral_test_xxx_testcase(clientid, account_type)

    def test_peg_algo_future_buy(self):
        clientid = 'peg0003'
        account_type = future_account
        self.send_order_msg(clientid, account_type)
        self.genaral_test_xxx_testcase(clientid,account_type)

    def test_peg_algo_future_sell(self):
        clientid = 'peg0004'
        account_type = future_account
        self.send_order_msg(clientid, account_type)
        self.genaral_test_xxx_testcase(clientid, account_type)

    def tearDown(self):
        self.socket.close()
        self.context.term()

if __name__ == '__main__':
    unittest.main()
