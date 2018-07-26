import pandas as pd
import numpy as np
import time
import sys

import multiprocessing
from xmlrpclib import ServerProxy
from tools.time_unit import DatetimeUtil
from public.main_config import *
from init_sql.fund_position_sql import DataBaseUnit
from market.stock_l2_replayer import DataPrepare_L2
from market.all_ticker_l1_replayer import DataPrepare_L1
from market.cta_only_replayer import DataPrepare_cta

# connect to windows program
windows_connect = ServerProxy('http://%s:%d' % (windows_ip, windows_port))

# strategy_loader_header_name
dll_loading_module_name_var = 'dynamic_load_module'
instance_name_var = 'instance_name'
strategy_name_var = 'strategy_name'  # use for strategy_parameter table's NAME

class AutoTestUnit(object):

    def __init__(self):
        pass

    @staticmethod
    def get_running_order(test_type, filename='AutoTestOrder.csv'):
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename))
        # for [app_name, platform_id] in order_list:
        #     print app_name, platform_id
        return df

    @staticmethod
    def get_terminal_content(cmd):
        terminal = os.popen(cmd)
        content = terminal.read()
        terminal.close()
        return content

    @staticmethod
    def get_component_file_list(app_name):
        physical_date = DatetimeUtil().get_today()
        if app_name == 'AlgoFrame':
            app_name = 'Algo'
        elif app_name == 'IndexArbStrategy':
            app_name = 'IndexArb'
        log_name_str = 'screenlog_%s_%s' % (app_name.lower(), physical_date)
        all_file_list = os.listdir(platform_log_path)
        component_file_list = filter(lambda x: x.lower().startswith(log_name_str), all_file_list)
        component_file_list.sort()
        return component_file_list

    def start_tradplat_cmd(self, app_name):

        component = app_name.lower()
        cmd_template = './script/%s'
        sh_file = 'start.%s.sh' % component
        cmd = cmd_template % sh_file
        os.chdir(platform_path)

        if not check_if_exist(os.path.join(platform_path, 'script', sh_file)):
            platform_logger.error('lack file: %s' % sh_file)
            return

        os.system(cmd)
        time.sleep(5)

        content = ''
        component_file_list = self.get_component_file_list(app_name)
        if len(component_file_list) > 0:
            read_log_cmd = 'tail -10 %s' % os.path.join(platform_log_path, component_file_list[-1])
            content = self.get_terminal_content(read_log_cmd)

        while 'TradingFramework start command loop now.' not in content and component != 'mktdtcenter':
            time.sleep(5)
            component_file_list = self.get_component_file_list(app_name)
            if len(component_file_list) > 0:
                read_log_cmd = 'tail -10 %s' % os.path.join(platform_log_path, component_file_list[-1])
                content = self.get_terminal_content(read_log_cmd)

    @staticmethod
    def start_windows_trade_monitor():
        pool.apply_async(windows_connect.run_trade_monitor())
        # process = multiprocessing.Process(target=windows_connect.run_trade_monitor())
        # process.start()
        # windows_connect.run_exe('TradeMonitor')
        # windows_connect.run_trade_monitor()

    @staticmethod
    def start_windows_virtual_exchange():
        pool.apply_async(windows_connect.run_virtual_exchange())
        # process = multiprocessing.Process(target=windows_connect.run_virtual_exchange())
        # process.start()
        # windows_connect.run_exe('VirtualExchange')

    def start_up_component(self, test_type):
        global pool
        pool = multiprocessing.Pool(processes=3)

        df_run_order = self.get_running_order(test_type)
        order_list = np.array(df_run_order[['platform', 'app_name']]).tolist()

        for [platform_id, app_name] in order_list:

            platform_logger.info('Starting up %s' % app_name)

            if platform_id == 'Linux':
                # continue
                self.start_tradplat_cmd(app_name)

            else:  # Windows
                if app_name == 'Virtual_Exchange':
                    platform_logger.warning('please start Virtual Exchange manually, program waits 20s')
                    time.sleep(20)
                    # self.start_windows_virtual_exchange()

                elif app_name == 'TradeMonitor':
                    platform_logger.warning('please input account/password on windows client')
                    platform_logger.warning('your windows client ip is :%s' % windows_ip)
                    self.start_windows_trade_monitor()
                    time.sleep(30)

            platform_logger.info('%s starts successfully!' % app_name)

        pool.close()

    def start_run(self, date, test_type):
        df_run_order = self.get_running_order(test_type)
        df_linux = df_run_order[df_run_order['platform'] == 'Linux']
        component_list = [x.lower() for x in df_linux['app_name']]
        write_script_from_template()
        # udpate database initial information
        DataBaseUnit().start_init_process(date, test_type)

        # data preparation
        if test_type == 'all':
            DataPrepare_L1().start_all_data_preparation(date, component_list)
        elif test_type == 'stock':
            DataPrepare_L2().start_stock_data_preparation(date, component_list)
        else:
            DataPrepare_cta().start_future_data_preparation(date, component_list)

        # start each component
        self.start_up_component(test_type)


if __name__ == '__main__':
        # date = '20180713'
        # test_type = 'future'
        db_unit = DataBaseUnit()
        db_prepare = DataPrepare_L1()
        start_run = AutoTestUnit()
        start_run.start_run(sys.argv[1], sys.argv[2])
        # start_run.start_run(date, test_type)
        # start_run.start_up_component()