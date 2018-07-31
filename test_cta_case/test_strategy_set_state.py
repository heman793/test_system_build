# -*- coding: utf-8 -*-

import unittest
from message.strategy_para_change_response_with_para import *
from message.strategy_info_request_msg import *
import pytest


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
        strategy_para_change_info_request_msg(strategy_name, is_enable=False)

    def get_expect_result(self, test_case_no):
        test_type = 'future'
        filename = 'test_data_%s.csv' % test_type
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         index_col="test_case_no")
        expect_result = df.at[test_case_no, 'expect_result']
        return expect_result

    def get_actual_result(self, test_case_no):
        test_type = 'future'
        app_name = 'StrategyLoader'
        strategy_name = self.get_strategy_name(test_case_no)
        strategy_state_dict = query_strategy_states(test_type, app_name)
        ret = get_dict_value(strategy_state_dict, strategy_name, default=None)
        if ret is not None:
            print ret
            acture_result = True
        else:
            acture_result = False
        return acture_result


    def genaral_test_xxx_testcase(self, test_case_no):
        expect = self.get_expect_result(test_case_no)
        actual = self.get_actual_result(test_case_no)
        print 'expect result is: %s, actual result is: %s' % (expect, actual)
        self.assertEqual(actual, expect)


    # def test_BBreaker_strategy_set_state(self):
    #     test_case_no = 'cta0001'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    #
    # def test_BollingerBandReversion_strategy_set_state(self):
    #     test_case_no = 'cta0002'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    #
    # def test_BreakBandDync_strategy_set_state(self):
    #     test_case_no = 'cta0003'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    #
    # def test_CCIMktRecg_strategy_set_state(self):
    #     test_case_no = 'cta0004'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    #
    # def test_CCIOsc_strategy_set_state(self):
    #     test_case_no = 'cta0005'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    #
    # def test_CCIRvs_strategy_set_state(self):
    #     test_case_no = 'cta0006'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    #
    # def test_Donchian_strategy_set_state(self):
    #     test_case_no = 'cta0007'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    #
    # def test_FollowTrendDync_strategy_set_state(self):
    #     test_case_no = 'cta0008'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    #
    # def test_Hans_strategy_set_state(self):
    #     test_case_no = 'cta0009'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    #
    # def test_HighLowBandADX_strategy_set_state(self):
    #     test_case_no = 'cta0010'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    #
    # def test_PriceVolRatio_strategy_set_state(self):
    #     test_case_no = 'cta0011'
    #     self.start_strategy(test_case_no)
    #     self.genaral_test_xxx_testcase(test_case_no)
    @pytest.mark.VolumeBreakthrough
    def test_VolumeBreakthrough_strategy_set_state(self):
        test_case_no = 'cta0012'
        self.start_strategy(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
