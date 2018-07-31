# -*- coding: utf-8 -*-

import unittest
from message.new_sigmavwap3_algo_order_msg import New_Order_Msg
import pandas as pd
from message.order_details import *
from message.socket_init import socket_init
from random import randint
import time
import pytest

class TestSigmaVWAP3Algo(unittest.TestCase,  New_Order_Msg):
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
        time.sleep(10)

    def get_expect_result(self, clientid):
        test_type = 'all'
        filename = '%s_%s_sigmavwap3.csv' % (stock_account, strategy)
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

    def genaral_test_xxx_testcase(self, clientid):
        expect = self.get_expect_result(clientid)
        actual = self.get_actual_result(clientid)
        print 'expect result is: %s, actual result is: %s' % (expect, actual)
        self.assertEqual(expect, actual)

    @pytest.mark.AlgoOrder
    def test_sigma_algo_stock_buy(self):
        clientid = 'sigma30001'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    @pytest.mark.AlgoOrder
    def test_sigma_algo_stock_sell(self):
        clientid = 'sigma30002'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def tearDown(self):
        self.socket.close()
        self.context.term()

if __name__ == '__main__':
    unittest.main()
