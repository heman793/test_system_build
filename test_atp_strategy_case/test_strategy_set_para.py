# -*- coding: utf-8 -*-

import unittest
from message.strategy_para_change_response_with_para import *
from message.strategy_info_request_msg import *
import pytest


class TestATPStrategy(unittest.TestCase):
    def setUp(self):
        pass

    def get_strategy_name(self, test_case_no):
        test_type = 'all'
        filename = 'account_%s.csv' % test_type
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         index_col="test_case_no")
        strategy_name_1 = df.at[test_case_no, 'dynamic_load_module']
        instance_name = df.at[test_case_no, 'instance_name']
        strategy_name = '%s.%s' % (strategy_name_1, instance_name)
        return strategy_name


    def set_strategy_para(self, test_case_no):
        strategy_name = self.get_strategy_name(test_case_no)
        strategy_para_change_info_request_msg(strategy_name, is_enable=False)

    def get_expect_result(self, test_case_no):
       return True

    def get_actual_result(self, test_case_no, app_name):
        test_type = 'all'
        strategy_name = self.get_strategy_name(test_case_no)
        strategy_parameter_dict = query_strategy_parameters(test_type, app_name)
        ret = get_dict_value(strategy_parameter_dict, strategy_name, default=None)
        if ret is not None:
            print ret
            acture_result = True
        else:
            acture_result = False
        return acture_result

    def genaral_test_xxx_testcase(self, test_case_no, app_name):
        expect = self.get_expect_result(test_case_no)
        actual = self.get_actual_result(test_case_no, app_name)
        print 'expect result is: %s, actual result is: %s' % (expect, actual)
        self.assertEqual(actual, expect)

    @pytest.mark.CalendarMA
    def test_CalendarMA_SU_strategy_set_para(self):
        test_case_no = 'st0002'
        app_name = 'CalendarMA'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.CalendarMA
    def test_CalendarMA_Transfer_strategy_set_para(self):
        test_case_no = 'st0003'
        app_name = 'CalendarMA'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.CalendarSpread
    def test_CalendarSpread_SU_strategy_set_para(self):
        test_case_no = 'st0004'
        app_name = 'CalendarSpread'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.ETFStrategy
    def test_ETFArb_illiquid_strategy_set_para(self):
        test_case_no = 'st0005'
        app_name = 'ETFStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.ETFStrategy
    def test_ETFArb_liquid_strategy_set_para(self):
        test_case_no = 'st0006'
        app_name = 'ETFStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.SFStrategy
    def test_SHSFArbMerge_default_strategy_set_para(self):
        test_case_no = 'st0007'
        app_name = 'SFStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.SFStrategy
    def test_SHSFArbRedPur_default_strategy_set_para(self):
        test_case_no = 'st0008'
        app_name = 'SFStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.SFStrategy
    def test_SHSFArbSplit_default_strategy_set_para(self):
        test_case_no = 'st0009'
        app_name = 'SFStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.IndexArbStrategy
    def test_IndexArb_SH000905_strategy_set_para(self):
        test_case_no = 'st0010'
        app_name = 'IndexArbStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.IndexArbStrategy
    def test_IndexArb_SHSZ300_strategy_set_para(self):
        test_case_no = 'st0011'
        app_name = 'IndexArbStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.IndexArbStrategy
    def test_IndexArb_SSE50_strategy_set_para(self):
        test_case_no = 'st0012'
        app_name = 'IndexArbStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.IndexArbStrategy
    def test_IndexArbETF_SH000905_strategy_set_para(self):
        test_case_no = 'st0013'
        app_name = 'IndexArbStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.IndexArbStrategy
    def test_IndexArbETF_SHSZ300_strategy_set_para(self):
        test_case_no = 'st0014'
        app_name = 'IndexArbStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.IndexArbStrategy
    def test_IndexArbETF_SSE50_strategy_set_para(self):
        test_case_no = 'st0015'
        app_name = 'IndexArbStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.OptionStrategy
    def test_MarketMaking1_SR_strategy_set_para(self):
        test_case_no = 'st0016'
        app_name = 'OptionStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.OptionStrategy
    def test_MarketMaking1_SSE50_strategy_set_para(self):
        test_case_no = 'st0017'
        app_name = 'OptionStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.OptionStrategy
    def test_MarketMaking1_m_strategy_set_para(self):
        test_case_no = 'st0018'
        app_name = 'OptionStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.OptionStrategy
    def test_PutCallParity_SR_strategy_set_para(self):
        test_case_no = 'st0019'
        app_name = 'OptionStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.OptionStrategy
    def test_PutCallParity_SSE50_strategy_set_para(self):
        test_case_no = 'st0020'
        app_name = 'OptionStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.OptionStrategy
    def test_PutCallParity_m_strategy_set_para(self):
        test_case_no = 'st0021'
        app_name = 'OptionStrategy'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    @pytest.mark.CloseLockedPosition
    def test_CloseLockedPosition_SU_strategy_set_para(self):
        test_case_no = 'st0022'
        app_name = 'CloseLockedPosition'
        self.set_strategy_para(test_case_no)
        self.genaral_test_xxx_testcase(test_case_no, app_name)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
