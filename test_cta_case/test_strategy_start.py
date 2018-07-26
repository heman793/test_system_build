# -*- coding: utf-8 -*-

import unittest
import pandas as pd
import time
from message.strategy_para_change_response_msg import *
from tools.log_check import check_strategy_start_log
from message.strategy_info_request_msg import *
import types

class TestCtaStrategy(unittest.TestCase):
    def setUp(self):
        pass

    def get_strategy_name(self, test_case_no):
        test_type = 'future'
        filename = 'test_data_%s.csv' % test_type
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

    def get_expect_result(self, test_case_no):
        return True

    def get_actual_result(self, test_case_no):
        strategy_name = self.get_strategy_name(test_case_no)
        strategy_status_dict = query_strategy_status()
        for key, value in strategy_status_dict.items():
            if strategy_name == key:
                return value
            else:
                exit
        return value

    def genaral_test_xxx_testcase(self, test_case_no):
        expect = self.get_expect_result(test_case_no)
        actual = self.get_actual_result(test_case_no)
        print 'expect result is: %s, actual result is: %s' % (expect, actual)
        self.assertEqual(actual, expect)


    def test_BBreaker_strategy_start(self):
        test_case_no = 'cta0001'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_BollingerBandReversion_strategy_start(self):
        test_case_no = 'cta0002'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_BreakBandDync_strategy_start(self):
        test_case_no = 'cta0003'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_CCIMktRecg_strategy_start(self):
        test_case_no = 'cta0004'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_CCIOsc_strategy_start(self):
        test_case_no = 'cta0005'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_CCIRvs_strategy_start(self):
        test_case_no = 'cta0006'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_Donchian_strategy_start(self):
        test_case_no = 'cta0007'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_FollowTrendDync_strategy_start(self):
        test_case_no = 'cta0008'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_Hans_strategy_start(self):
        test_case_no = 'cta0009'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_HighLowBandADX_strategy_start(self):
        test_case_no = 'cta0010'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_PriceVolRatio_strategy_start(self):
        test_case_no = 'cta0011'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def test_VolumeBreakthrough_strategy_start(self):
        test_case_no = 'cta0012'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
