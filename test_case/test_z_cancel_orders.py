# -*- coding: utf-8 -*-

import unittest
from message.order_details import *
from random import randint

class TestCancelOrders(unittest.TestCase, OrderView):
    def setUp(self):
        pass

    def get_expect_result(self):
        expect_result = 'Canceled'
        return expect_result

    def get_actual_result(self, clientid):
        order_list = query_order_by_clientid(clientid)
        for order in order_list:
            print "order id: %s, client id: %s" % (order['OrderID'],
                                                   order['CliOrdID'])
            if order['Status'] == 4:
                actual_result = "Canceled"
            elif order['Status'] == -1:
                actual_result = "None"
            elif order['Status'] == 0:
                actual_result = "New"
            elif order['Status'] == 1:
                actual_result = "PartialFilled"
            elif order['Status'] == 2:
                actual_result = "Filled"
            elif order['Status'] == 8:
                actual_result = "Rejected"
            else:
                actual_result = 'Other Status'
        return actual_result

    def get_actual_result_all(self):
        need_cancel_list = query_need_cancel_orders()
        actual_result = 'False'
        if need_cancel_list:
            actual_result = 'Canceled'
        else:
            actual_result = 'NoneCanceled'
        return actual_result

    def genaral_test_xxx_testcase(self, clientid):
        expect = self.get_expect_result()
        actual = self.get_actual_result(clientid)
        print 'expect result is: %s, actual result is: %s' % (expect, actual)
        self.assertEqual(actual, expect)


    def test_cancel(self):
        clientid = 'ts0013'
        cancel_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_cancel_partial_filled(self):
        clientid = 'ts0023'
        cancel_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_cancel_new(self):
        clientid = 'ts0015'
        cancel_order_msg(clientid)
        self.genaral_test_xxx_testcase(clientid)

    # def test_cancel_algo_smart(self):
    #     clientid = 'smart0001'
    #     cancel_order_msg(clientid)
    #     self.genaral_test_xxx_testcase(clientid)
    #
    # def test_cancel_algo_sigma(self):
    #     clientid = 'sigma0001'
    #     cancel_order_msg(clientid)
    #     self.genaral_test_xxx_testcase(clientid)

    def test_cancel_all(self):
        query_need_cancel_orders()
        cancel_all_msg()
        self.get_expect_result()
        self.get_actual_result_all()

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
