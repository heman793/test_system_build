import shutil
from public.main_config import *
from data_prepare.common.config_common import ConfigCommon
from ysdata.future_info import get_platform_name
from ysdata.data_info import FutureData
from tools.date_utils import *
import sys
from data_prepare.init_sql.strategy_para_all import Strategy_para

class DataPrepare_L1(ConfigCommon):
    def __init__(self):
        ConfigCommon.__init__(self)
        self.ini_input_dict = self.get_ini_input_dict()

    def get_level1_data_from_nas(self, date):
        filename = 'security_mktdt_%s.dat.tar.gz' % date
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
        print src_data_dat
        return src_data_dat

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

    def write_all_data_ini_process(self, data_dat_list):
        [secur_dat] = data_dat_list
        print [secur_dat]
        dict_ = self.ini_input_dict
       # mktcenter_all_ini
        dict_['import_file'] = secur_dat
        mktcenter_all_ini = self.write_config_ini_from_template(
            'config_mktcenter_all.ini', dict_)
        return  mktcenter_all_ini


    def write_all_component_config(self, date, component_list, test_type,
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
            # elif component == 'indexarb':
            #     component == 'indexarbstrategy'
            elif component == 'mktcsv':
                df = self.get_strategy_loader_df(test_type='future')
                ticker_list = [x for x in df['target'].values]
                contract_list = []
                for symbol in ticker_list:
                    df = FutureData().get_future_type_adj_table(symbol)
                    contract = df['symbol'].iloc[-1]
                    contract_str = get_platform_name(contract, 'quote')
                    contract_list.append(contract_str)
                dict_['Instruments'] = ','.join(contract_list)
                date2 = datetime.datetime.strptime(date,'%Y%m%d').strftime('%F')
                dict_['StartTime'] = date2
                dict_['EndTime'] = date2

            elif component == 'mainframe':
                dict_['ControlPort'] = str(control_port)
            elif component == 'mktdtcenter':
                if test_type == 'stock':
                    dict_['ConfigPath'] = './config_mktcenter.ini'
                    dict_['ReceiveFrom'] = 'mg1'
                    dict_['ReceiveFromExt'] = 'rp1'
                else:
                    dict_['ConfigPath'] = './config_mktcenter_all.ini'
                    dict_['ReceiveFrom'] = 'rp1'
                    dict_['ReceiveFromExt'] = ''
            elif component in [ 'mktudpsvr', 'ordudp', 'strategyloader']:
                pass

            config_file_path = self.write_config_ini_from_template(config_file_name, dict_)
            if component == 'strategyloader':
                file_ = file(os.path.join(platform_path, config_file_name), 'a+')
                file_.write(self.write_strategy_parameter_list_str(test_type))
                file_.close()

            startup_dict[component] = config_file_path
        return startup_dict

    def start_all_data_preparation(self, date, component_list):
        test_type = 'all'
        self.get_level1_data_from_nas(date)
        self.write_all_component_config(date, component_list, test_type)

        # write congif_mktcenter_all.ini
        src_data_dat = self.get_level1_data_from_nas(date)
        secur_dat = os.path.join(test_data_path, 'security_mktdt_%s.dat' %
                                   date)
        data_dat_list = [secur_dat]
        self.write_all_data_ini_process(data_dat_list)

        # insert atp strategy parameters
        Strategy_para().start_init_process()

if __name__ == "__main__":
    # date = '20180713'
    data_prepare = DataPrepare_L1()
    data_prepare.start_all_data_preparation(sys.argv[1], sys.argv[2])