# import numpy as np
import pandas as pd
import shutil
import numpy as np
import json
import time

import multiprocessing
import paramiko
from xmlrpclib import ServerProxy

from ysdata.data_info import get_stock_summary_df, get_future_summary_df
from ysdata.TimeUnit import DatetimeUtil
from main_config import *
from instrument_update import InstrumentUpdate

# connect to windows program
windows_connect = ServerProxy('http://%s:%d' % (windows_ip, windows_port))

# strategy_loader_header_name
dll_loading_module_name_var = 'dynamic_load_module'
instance_name_var = 'instance_name'
strategy_name_var = 'strategy_name'  # use for strategy_parameter table's NAME


class ConfigCommon(object):

    def __init__(self):
        self.parameter_title, self.parameter_dict = self.get_parameter_title_and_dict(parameter_dict_filepath=None)

    @staticmethod
    def get_parameter_title_and_dict(parameter_dict_filepath=None):
        """
        Suggest set up a only one parameter_dict.csv, so that reduce maintenance work once file changes
        :param parameter_dict_filepath: filepath
        :return: parameter_title and parameter_dict
        """
        parameter_dict = dict()
        if parameter_dict_filepath is None:
            parameter_dict_filepath = parameter_dict_filepath_default
            # parameter_dict_filepath = os.path.join(strategy_config_path, 'parameter_dict.csv')
        input_file = open(parameter_dict_filepath)
        file_items = input_file.readlines()
        parameter_title_list = file_items[0].replace('\n', '').split(',')
        for i in range(1, len(file_items)):
            param_set_index = file_items[i].split(',')[0]
            parameter_dict[param_set_index] = file_items[i].replace('\n', '')
        return parameter_title_list, parameter_dict

    @staticmethod
    def get_strategy_loader_df(target_type):
        """
        you should prepare strategy_loader config file on strategy_config_path, with such format
        'strategy_loader_%s.csv' % target_type
        :param target_type: 'stock', 'future' and 'option'
        :return:
        """
        filename = 'strategy_loader_%s.csv' % target_type
        df = pd.read_csv(os.path.join(strategy_config_path, filename), dtype={'target': str})
        if target_type == 'stock':
            df['target'] = df['target'].apply(lambda x: x.zfill(6))
        return df

    @staticmethod
    def get_strategy_so_df():
        """
        not sure whether this function is useful or not, serve for
        :return:
        """
        return
        try:
            conn = get_conn_db('strategy')
            sql = "select * from strategy_so"
            df = pd.read_sql(sql, conn)
            conn.close()

        except Exception:
            file_path = os.path.join(strategy_config_path, 'strategy_so.csv')
            if not check_if_exist(file_path):
                platform_logger.error('lack strategy_so map')
                raise IOError
            df = pd.read_csv(file_path)
        df['so_name'] = df['so_name'].apply(lambda x: x.split('.')[0])
        df[strategy_name] = df[strategy_name].apply(lambda x: x.replace('Strategy', '_strategy'))
        df[strategy_name] = df[strategy_name].apply(lambda x: '_'.join(x.split('_')[:-1]))
        return df

    @staticmethod
    def get_ini_input_dict():
        dict_ = {
            'database_address': sql_server,
            'database_username': sql_user,
            'database_password': sql_password,
            'SqlAddress': sql_server,
            'SqlUser': sql_user,
            'SqlPassword': sql_password,
            # 'Instruments': '002746,000004', # hfcalculator
            # 'ControlPort': 17103   # mainframe
            # 'import_file': '',  # pre_capture(with dat), rebuild(with dat), hh_alpha(with dat)
            # 'export_filename': '',  # pre_capture(no dat), rebuild(no dat), hh_alpha(no output)
            # 'instument_filename': '',  # rebuild(high_low_limited.csv)
            # 'interested_instruments': '',  # pre_capture(ticker_list,)
        }
        return dict_


class DataPreareUnit(ConfigCommon):

    def __init__(self):
        ConfigCommon.__init__(self)
        self.ini_input_dict = self.get_ini_input_dict()

    @staticmethod
    def write_config_ini_from_template(ini_name, input_dict):
        src_file_path = os.path.join(config_template_path, ini_name)
        des_file_path = os.path.join(platform_path, ini_name)
        file_read = file(src_file_path, 'rb')
        file_write = file(des_file_path, 'wb')

        while True:
            line = file_read.readline()
            if line:
                line = line.replace('\n', '')
                line = line.replace('\r', '')
                if '%s' in line:
                    key = line.split('=')[0]
                    line = line % input_dict[key]
                file_write.write(line+'\n')
            else:
                break
        file_read.close()
        file_write.close()
        return des_file_path

    def write_all_data_ini_process(self, data_dat_list, ticker_list, high_low_limited_file):
        [src_data_dat, pre_capture_dat, rebuild_dat] = data_dat_list
        dict_ = self.ini_input_dict
        # pre_capture
        dict_['interested_instruments'] = ','.join(ticker_list)
        dict_['import_file'] = src_data_dat
        dict_['export_filename'] = pre_capture_dat[:-4]
        if check_if_exist(pre_capture_dat):
            os.remove(pre_capture_dat)
        pre_capture_ini = self.write_config_ini_from_template('config_pre_capture.ini', dict_)

        # rebuild
        dict_['instrument_filename'] = high_low_limited_file
        dict_['import_file'] = pre_capture_dat
        dict_['export_filename'] = rebuild_dat[:-4]
        if check_if_exist(rebuild_dat):
            os.remove(rebuild_dat)
        build_ini = self.write_config_ini_from_template('config_rebuild.ini', dict_)
        # hh_alpha
        dict_['import_file'] = rebuild_dat
        hh_alpha_ini = self.write_config_ini_from_template('config_mktcenter.ini', dict_)
        return pre_capture_ini, build_ini, hh_alpha_ini

    @staticmethod
    def run_ini_create_program(ini_file):
        os.chdir(platform_path)
        component_log_path = os.path.join(test_log_path, component_log_name)
        cmd = './%s -uc=false --cfg=%s > %s 2>&1' % \
              ('build64_release/libatp.mktdt/MktdtSvr', ini_file, component_log_path)
        platform_logger.info(cmd)
        os.system(cmd)

    # ================================= data process =========================================================
    @staticmethod
    def get_high_low_limited_csv(date, output_path):
        make_dir(output_path)
        df = pd.read_csv(os.path.join(stock_path, date, 'market_data', 'summary.csv'))
        df = df[['symbol', 'high_limited', 'low_limited']]
        df['symbol'] = df['symbol'].astype('str').apply(lambda x: x.zfill(6))
        df = df[['symbol', 'high_limited', 'low_limited']]
        df.columns = ['TICKER', 'UPLIMIT', 'DOWNLIMIT']
        exchange_map = {'0': 19, '3': 19, '6': 18}
        df['temp'] = df['TICKER'].apply(lambda x: x[0])
        b1 = df['temp'].astype('int') % 3 == 0
        df = df[b1]
        df['EXCHANGE_ID'] = df['temp'].apply(lambda x: exchange_map[x[0]])
        df['TYPE_ID'] = 4
        df['TICK_SIZE_TABLE'] = '0:0.01'
        ins_header = ['TICKER', 'EXCHANGE_ID', 'TYPE_ID', 'UPLIMIT', 'DOWNLIMIT', 'TICK_SIZE_TABLE']
        df = df[ins_header]
        final_name = '%s_high_low_limited.csv' % date
        high_low_limited_csv = os.path.join(output_path, final_name)
        file_ = file(high_low_limited_csv, 'w')

        df.to_csv(os.path.join(output_path, '1.csv'), index=False)
        fi = file(os.path.join(output_path, '1.csv'), 'r')
        line = fi.readline()
        file_.write(line)
        while True:
            line = fi.readline()
            if line:
                line = line.split('\n')[0]
                file_.write(line + ',\n')
            else:
                break

        file_.close()
        os.remove(os.path.join(output_path, '1.csv'))
        return high_low_limited_csv

    @staticmethod
    def get_lts_data_from_package(date):
        filename = 'hb_mktdt_lts_l2_2_tcp_%s.dat.tar.gz' % date
        src_data_path = os.path.join(lts_data_path, filename)
        src_data_dat = os.path.join(test_data_path, filename[:-7])
        if check_if_exist(src_data_dat):
            platform_logger.warning('file exists: %s' % src_data_dat)
            return src_data_dat

        if not check_if_exist(src_data_path):
            platform_logger.error('lack file %s' % src_data_path)
            raise IOError

        shutil.copyfile(src_data_path, os.path.join(test_data_path, filename))
        file_logger.info(os.path.join(test_data_path, filename))
        os.chdir(test_data_path)
        cmd = 'tar zxvf %s' % os.path.join(test_data_path, filename)
        os.system(cmd)

        file_logger.info(src_data_dat)
        return src_data_dat

    @staticmethod
    def remove_transition_file():
        file_path = os.path.join(test_log_path, file_log_name)
        file_ = file(file_path, 'rb')
        file_list = []
        while True:
            line = file_.readline()
            if line:
                file_path = line.replace('\n', '').split(' ')[-1]
                file_list.append(file_path)
            else:
                break
        file_.close()
        file_list = list(set(file_list))
        map(lambda x: remove_file_path(x), file_list)
        # return file_list

    # ================================== write config template ============================================
    @staticmethod
    def get_para_list():
        return ''

    @staticmethod
    def get_volume_profile(date, ticker_list):
        shutil.rmtree(volume_profile_path)
        make_dir(volume_profile_path)
        src_path = os.path.join(src_volume_profile_path, date)
        for ticker in ticker_list:
            filename = '%s.csv' % ticker
            src_file_path = os.path.join(src_path, filename)
            if not check_if_exist(src_file_path):
                platform_logger.warning('lack file: %s' % src_file_path)
                continue
            des_file_path = os.path.join(volume_profile_path, filename)
            cmd = 'ln -s %s %s' % (src_file_path, des_file_path)
            os.system(cmd)

    def write_strategy_parameter_list_str(self, target_type):
        df = self.get_strategy_loader_df(target_type=target_type)

        df['parameter_header'] = map(lambda a, b: '%s.%s' % (a, b),
                                     df[dll_loading_module_name_var], df[instance_name_var])
        group = df.groupby('parameter_header')
        parameter_str = ''
        title_template = '[Strategy.%s.%s]'
        for parameter, data in group:
            so_name = data['so_name'].iloc[0]
            header = title_template % (so_name, parameter)
            ticker_list = [x for x in data['target'].values]
            ticker_list = list(set(ticker_list))
            watch_list = 'WatchList=%s' % ';'.join(ticker_list)
            para_list = 'ParaList=%s' % self.get_para_list()
            parameter_str += '\n'.join([header, watch_list, para_list]) + '\n'

        return parameter_str

    def write_all_component_config(self, component_list, target_type, control_port=control_port_num):
        config_file_template = 'config.%s.txt'
        startup_dict = {}
        dict_ = self.get_ini_input_dict()

        for component in component_list:
            config_file_name = config_file_template % component
            if component == 'hfcalculator':
                df = self.get_strategy_loader_df(target_type)
                ticker_list = [x for x in df['target'].values]
                ticker_list = list(set(ticker_list))

                dict_['Instruments'] = ','.join(ticker_list)

            elif component == 'mainframe':
                dict_['ControlPort'] = str(control_port)

            elif component in ['mktdtcenter', 'mktudpsvr', 'ordudp', 'strategyloader']:
                pass

            config_file_path = self.write_config_ini_from_template(config_file_name, dict_)
            if component == 'strategyloader':
                file_ = file(os.path.join(platform_path, config_file_name), 'a+')
                file_.write(self.write_strategy_parameter_list_str(target_type))
                file_.close()

            startup_dict[component] = config_file_path
        return startup_dict

    def copy_algo_test_config(self):
        pass

    # ================================== main process ====================================================
    def start_stock_data_preparation(self, date, component_list):
        target_type = 'stock'
        # write component config
        self.write_all_component_config(component_list, target_type)
        # return

        # get_high_low_limited.csv
        high_low_limited_file = self.get_high_low_limited_csv(date, test_data_path)
        file_logger.info(high_low_limited_file)

        # get_volume_profile soft link
        df = self.get_strategy_loader_df(target_type)
        ticker_list = [x for x in df['target'].values]
        self.get_volume_profile(date, ticker_list)

        # write pre_capture_ini, build_ini, hh_alpha_ini
        src_data_dat = self.get_lts_data_from_package(date)
        pre_capture_dat = os.path.join(test_data_path, 'pre_capture_%s.dat' % date)
        rebuild_dat = os.path.join(test_data_path, 'rebuild_%s.dat' % date)
        data_dat_list = [src_data_dat, pre_capture_dat, rebuild_dat]
        pre_capture_ini, build_ini, hh_alpha_ini = self.write_all_data_ini_process(data_dat_list, ticker_list,
                                                                                   high_low_limited_file)
        # start pre_capture, rebuild, replay_data
        self.run_ini_create_program(pre_capture_ini)
        self.run_ini_create_program(build_ini)
        map(lambda file_path: file_logger.info(file_path), data_dat_list)


class DataBaseUnit(ConfigCommon):

    def __init__(self):
        ConfigCommon.__init__(self)
        self.physical_date = DatetimeUtil().get_today('%Y-%m-%d')
        self.physical_datetime = DatetimeUtil().get_today('%Y-%m-%d %H:%M:%S')
        self.real_account_type_map = {
            'stock': stock_account_id,
            'future': future_account_id,
            'option': option_account_id
        }
        # may be not correct
        self.pf_account_type_map = {
            'long': pf_long_account_id,
            'short': pf_short_account_id
        }

    @staticmethod
    def get_sql_template(table):
        """
        return insert sql template string
        :param table:
                portfolio: 'account_position', 'pf_position',
                strategy: 'strategy_parameter'
        :return: template_str
        """
        if table == 'account_position':
            sql = "insert into account_position values " \
                  "('%s', '%s', '%s', '0', '%f', '%f', '%f', '0', '0', '%f', '%f', '%f', '0', '0'" \
                  ",'0', null, null, null, null, null, null, null, '0', '0', '0', '0', '%f', '0', '0', '%s');"

        elif table == 'pf_position':
            sql = "insert into pf_position values " \
                  "('%s', '%s', '%s', '0', '%f', '%f', '%f', '0', '0', '%f', '%f', '%f', '0', '0', '0',null, null, '1'," \
                  " '0', '0', '0', '0', '0', '0', '0', '0', '%f', '0', '0', '0', null);"
        elif table == 'strategy_parameter':
            sql = "insert into strategy_parameter values ('%s', '%s', '%s')"

        else:
            platform_logger.error("input wrong table '%s'" % table)
            return ''

        return sql

    @staticmethod
    def execute_db_sql(db, sql_list, conn=None, sql_recorder=sql_logger):
        if conn is None:
            conn = get_conn_db(db)
        cur = conn.cursor()
        map(lambda sql: cur.execute(sql), sql_list)
        sql_list = map(lambda x: '%s / %s' % (x, db), sql_list)
        map(lambda sql: sql_recorder.info(sql), sql_list)
        cur.close()
        conn.commit()
        conn.close()

    @staticmethod
    def get_target_pre_price(date, target, target_type):
        summary_df_dict = {'stock': get_stock_summary_df, 'future': get_future_summary_df}
        df_summary = summary_df_dict[target_type](date)
        pre_prc_field = {'stock': 'prev_close', 'future': 'prev_settlement'}
        return df_summary.at[target, pre_prc_field[target_type]]

    def get_strategy_parameter_string(self, ticker_param_set_list):
        parameter_value_dict = dict()
        parameter_value_dict['Account'] = fund_name
        for [ticker, param_set] in ticker_param_set_list:
            parameter_list = self.parameter_dict[str(param_set)].split(',')
            for ind in range(len(parameter_list)):
                key = '%s_%s' % (ticker, self.parameter_title[ind])
                parameter_value_dict[key] = parameter_list[ind]
        return json.dumps(parameter_value_dict)

    # =================== clear database before insert ======================
    def clear_db_om(self):
        delete_table_list = ['order_broker', 'order_history', 'trade2', 'trade2_broker', 'trade2_history']
        sql_list = []
        delete_sql = "delete from %s"
        map(lambda table: sql_list.append(delete_sql % table), delete_table_list)
        self.execute_db_sql(db='om', sql_list=sql_list)

    def clear_db_portfolio(self, date):
        sql_list = []
        delete_sql = "delete from %s where DATE = '%s'"
        delete_table_list = ['pf_position', 'account_position']
        map(lambda table: sql_list.append(delete_sql % (table, date)), delete_table_list)
        self.execute_db_sql('portfolio', sql_list)

    def insert_stock_strategy(self, target_type):
        df = self.get_strategy_loader_df(target_type)
        strategy_name_field = 'strategy_parameter_name'
        df[strategy_name_field] = map(lambda a, b: '%s.%s' % (a, b), df[strategy_name_var], df[instance_name_var])
        group = df.groupby(strategy_name_field)
        sql_list = []
        strategy_sql_template = self.get_sql_template('strategy_parameter')
        for strategy_name, data in group:
            ticker_param_set_list = np.array(data[['target', 'param_set']]).tolist()
            parameter_dict_json = self.get_strategy_parameter_string(ticker_param_set_list)
            sql = strategy_sql_template % (self.physical_datetime, strategy_name, parameter_dict_json)
            sql_list.append(sql)
        # print sql_list
        self.execute_db_sql('strategy', sql_list)

    # =================== insert parameter into db ==========================
    def insert_db_strategy(self, date, target_type):
        if target_type == 'stock':
            self.insert_stock_strategy(target_type)

    @staticmethod
    def insert_db_common(date):
        InstrumentUpdate().update_instrument_day(date)

    def insert_db_portfolio(self, date, target_type):
        df = self.get_strategy_loader_df(target_type)
        sql_list = []
        sql_account_sql_template = self.get_sql_template('account_position')
        sql_pf_sql_template = self.get_sql_template('pf_position')
        account_id = self.real_account_type_map[target_type]

        for ind in df.index.values:
            target = df.at[ind, 'target']
            pre_prc = self.get_target_pre_price(date, target, target_type)
            long_amount = df.at[ind, 'long']
            long_cost = long_amount * pre_prc
            short_amount = df.at[ind, 'short']
            short_cost = short_amount * pre_prc
            prev_net = abs(long_amount - short_amount)

            sql_account = sql_account_sql_template % \
                          (self.physical_date, account_id, target, long_amount, long_cost, long_amount,
                           short_amount, short_cost, short_amount, prev_net, self.physical_datetime)
            sql_pf_long = sql_pf_sql_template % \
                          (self.physical_date, pf_long_account_id, target, long_amount, long_cost, long_amount,
                           0, 0, 0, long_amount)
            sql_pf_short = sql_pf_sql_template % \
                           (self.physical_date, pf_short_account_id, target, 0, 0, 0,
                            short_amount, short_cost, short_amount, short_amount)

            sql_list.append(sql_account)
            if long_amount > 0:
                sql_list.append(sql_pf_long)
            if short_amount > 0:
                sql_list.append(sql_pf_short)

        self.execute_db_sql('portfolio', sql_list)

    def insert_portfolio_cny(self):
        sql_list = []
        cash_num = 1000000000.000000
        for id_num in [stock_account_id, future_account_id, option_account_id]:
            sql_template = self.get_sql_template('account_position')
            sql_account = sql_template % (self.physical_date, str(id_num), 'CNY',
                                          cash_num, 0, cash_num, 0, 0, 0, 0, self.physical_datetime)
            sql_list.append(sql_account)
        self.execute_db_sql('portfolio', sql_list)

    def start_init_process(self, date, target_type='stock'):
        self.clear_db_om()
        self.clear_db_portfolio(self.physical_date)

        self.insert_db_common(date)
        self.insert_db_strategy(date, target_type)
        self.insert_portfolio_cny()
        self.insert_db_portfolio(date, target_type)


class ServerUnit(object):

    def __init__(self, ip):
        self.ip = ip

    @staticmethod
    def get_account_passwd_from_ip(ip):
        if ip == '172.16.12.178':
            return 22, '', ''  # port, username, password
        else:
            raise Exception

    def run_sever_cmd(self, cmd_str):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        port, username, password = self.get_account_passwd_from_ip(self.ip)
        for m in cmd_str:
            ssh.connect(self.ip, port, username, password, timeout=30)
            stdin, stdout, stderr = ssh.exec_command(m)
            cmd_result = stderr.readlines()
            for item in cmd_result:
                print 'Stderr Info:%s' % (item,)
            cmd_result = stdout.readlines()
            for item in cmd_result:
                print 'Stdout Info:%s' % (item,)
            print 'IP:%s, CMD:%s Run Over!' % (self.ip, m)


class AutoTestUnit(object):

    def __init__(self):
        pass

    @staticmethod
    def get_running_order(filename='AutoTestOrder.csv'):
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

    def start_up_component(self):
        global pool
        pool = multiprocessing.Pool(processes=3)

        df_run_order = self.get_running_order()
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

    def start_run(self, date):

        df_run_order = self.get_running_order()
        df_linux = df_run_order[df_run_order['platform'] == 'Linux']
        component_list = [x.lower() for x in df_linux['app_name']]
        write_script_from_template()
        # udpate database initial information
        DataBaseUnit().start_init_process(date, 'stock')

        # data preparation
        DataPreareUnit().start_stock_data_preparation(date, component_list)

        # start each component
        self.start_up_component()

        # start backtest


if __name__ == '__main__':
    day = '20180130'
    auto_test = AutoTestUnit()
    db_unit = DataBaseUnit()
    #auto_test.start_up_component()
    # db_unit.insert_portfolio_cny()
    # db_unit.insert_stock_strategy('stock')
    # db_unit.start_init_process(day, target_type='stock')
    # datapre_unit = DataPreareUnit().start_stock_data_preparation(day)
    auto_test.start_run(day)

