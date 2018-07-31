# -*- coding: utf-8 -*-

import unittest
from message.strategy_para_change_response_msg import *
from message.strategy_info_request_msg import *
import pytest


class TestStockIntradayStrategy(unittest.TestCase):
    def setUp(self):
        pass

    def get_strategy_name(self, test_case_no):
        test_type = 'stock'
        filename = 'account_%s.csv' % test_type
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         index_col="test_case_no")
        strategy_name_1 = df.at[test_case_no, 'dynamic_load_module']
        instance_name = df.at[test_case_no, 'instance_name']
        strategy_name = '%s.%s' % (strategy_name_1, instance_name)
        return strategy_name

    def start_strategy(self, test_case_no):
        strategy_name = self.get_strategy_name(test_case_no)
        strategy_para_change_info_request_msg(strategy_name, is_enable=True)

    def get_expect_result(self):
        return True

    def get_actual_result(self, test_case_no):
        test_type = 'stock'
        app_name = 'StrategyLoader'
        strategy_name = self.get_strategy_name(test_case_no)
        strategy_status_dict = query_strategy_status(test_type, app_name)
        for key, value in strategy_status_dict.items():
            if strategy_name == key:
                return value
            else:
                exit
        return value

    def genaral_test_xxx_testcase(self, test_case_no):
        expect = self.get_expect_result()
        actual = self.get_actual_result(test_case_no)
        print 'expect result is: %s, actual result is: %s' % (expect, actual)
        self.assertEqual(actual, expect)

    @pytest.mark.Stkintraday
    def test_Stkintraday_strategy_start(self):
        test_case_no = 'str0001'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
