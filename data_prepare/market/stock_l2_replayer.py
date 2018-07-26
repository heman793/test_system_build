import pandas as pd
import shutil
from public.main_config import *
from data_prepare.common.config_common import ConfigCommon
import sys
from data_prepare.init_sql.strategy_para_stock import Strategy_para

# strategy_loader_header_name
dll_loading_module_name_var = 'dynamic_load_module'
instance_name_var = 'instance_name'
strategy_name_var = 'strategy_name'  # use for strategy_parameter table's NAME

class DataPrepare_L2(ConfigCommon):
    def __init__(self):
        ConfigCommon.__init__(self)
        self.ini_input_dict = self.get_ini_input_dict()

    @staticmethod
    def write_config_ini_from_template(ini_name, input_dict):
        src_file_path = os.path.join(config_template_path, ini_name)
        # print src_file_path
        des_file_path = os.path.join(platform_path, ini_name)
        # print des_file_path
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

    def write_strategy_parameter_list_str(self, test_type):
        df = self.get_strategy_loader_df(test_type=test_type)

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

    def write_all_component_config(self, component_list, test_type,
                                   control_port=control_port_num):
        config_file_template = 'config.%s.txt'
        startup_dict = {}
        dict_ = self.get_ini_input_dict()

        for component in component_list:
            config_file_name = config_file_template % component
            if component == 'hfcalculator':
                df = self.get_strategy_loader_df(test_type)
                ticker_list = [x for x in df['target'].values]
                ticker_list = list(set(ticker_list))
                dict_['Instruments'] = ','.join(ticker_list)
            elif component == 'mainframe':
                dict_['ControlPort'] = str(control_port)
            elif component == 'mktdtcenter':
                if test_type == 'stock':
                    dict_['ConfigPath'] = './config_mktcenter.ini'
                else:
                    dict_['ConfigPath'] = './config_mktcenter_all.ini'
            elif component in ['mktcsv', 'mktudpsvr', 'ordudp',
                               'strategyloader']:
                pass

            config_file_path = self.write_config_ini_from_template(config_file_name, dict_)
            if component == 'strategyloader':
                file_ = file(os.path.join(platform_path, config_file_name), 'a+')
                file_.write(self.write_strategy_parameter_list_str(test_type))
                file_.close()

            startup_dict[component] = config_file_path
        return startup_dict

    def copy_algo_test_config(self):
        pass

    # ================================== main process ====================================================
    def start_stock_data_preparation(self, date, component_list):
        test_type = 'stock'
        # write component config
        self.write_all_component_config(component_list, test_type)
        # return

        # get_high_low_limited.csv
        high_low_limited_file = self.get_high_low_limited_csv(date, test_data_path)
        file_logger.info(high_low_limited_file)

        # get_volume_profile soft link
        df = self.get_strategy_loader_df(test_type)
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

        # insert strategy_parameters
        Strategy_para().start_init_process(test_type='stock')

if __name__ == '__main__':
    # day = '20180713'
    data_prepare = DataPrepare_L2()
    # data_prepare.start_stock_data_preparation(day, {'mktdtcenter',
    #                                                 'strategyloader',
    #                                                 'hfcalculator'})
    data_prepare.start_stock_data_preparation(sys.argv[1], sys.argv[2])