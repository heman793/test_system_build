# -*- coding: utf-8 -*-

import unittest
from message.new_market_algo_order_msg import New_Order_Msg
from message.order_details import *
import time
from random import randint
import pytest

class TestMktBasketAlgo(unittest.TestCase,  New_Order_Msg):
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

    def get_expect_result(self):
        expect_result = True
        return expect_result

    def get_actual_result(self, clientid):
        order_list = query_order_by_clientid(clientid)
        actual_result = False
        for order in order_list:
            print "order id: %s, client id: %s" % (order['OrderID'],
                                                   order['CliOrdID'])
            if order['AlgoStatus'] == 2 and order['Status'] != 8:
                actual_result = True
            elif order['AlgoStatus'] == 0 and order['Status'] != -1:
                actual_result = True
            else:
                actual_result = False
                print order['Note']
        return actual_result

    def genaral_test_xxx_testcase(self, clientid):
        expect = self.get_expect_result()
        actual = self.get_actual_result(clientid)
        print 'expect result is: %s, actual result is: %s' % (expect, actual)
        self.assertEqual(expect, actual)

    @pytest.mark.AlgoOrder
    def test_mkt_basket_algo_sigma(self):
        clientid = 'mkt0001'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    @pytest.mark.AlgoOrder
    def test_mkt_basket_algo_sigma3(self):
        clientid = 'mkt0002'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    @pytest.mark.AlgoOrder
    def test_mkt_basket_algo_smart(self):
        clientid = 'mkt0003'
        self.send_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def tearDown(self):
        self.socket.close()
        self.context.term()

if __name__ == '__main__':
    unittest.main()
