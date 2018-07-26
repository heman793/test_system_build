# -*- coding: utf-8 -*-

import unittest
from message.order_details import *
from message.cancel_order_msg import *

class TestCancelOrders(unittest.TestCase, OrderView):
    def setUp(self):
        pass

    def cancel_orders_by_cliendid(self, clientid):
        order_id = query_orderid_by_clientid(clientid)
        cancel_order_message(self, order_id)

    def get_expect_result(self):
        expect_result = 'Canceled'
        return expect_result

    def get_actual_result(self, clientid):
        order_list = query_order_by_clientid(clientid)
        for order in order_list:
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
            else:
                actual_result = 'Other Status'
        return actual_result

    def get_actual_result_all(self):
        need_cancel_list = query_need_cancel_orders()
        if need_cancel_list:
            actual_result = 'Canceled'
        else:
            actual_result = 'NoneCanceled'
        return actual_result

    def genaral_test_xxx_testcase(self, clientid):
        expect = self.get_expect_result()
        actual = self.get_actual_result(clientid)
        print 'expect result is ' + expect
        print 'actual result is ' + actual
        self.assertEqual(actual, expect)


    def test_cancel_filled(self):
        clientid = 'ts0013'
        self.cancel_orders_by_cliendid(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_cancel_partial_filled(self):
        clientid = 'ts0023'
        self.cancel_orders_by_cliendid(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_cancel_new(self):
        clientid = 'ts0015'
        self.cancel_orders_by_cliendid(clientid)
        self.genaral_test_xxx_testcase(clientid)

    def test_cancel_all(self):
        query_need_cancel_orders()
        cancel_all_msg(self)
        self.get_expect_result()
        self.get_actual_result_all()

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
