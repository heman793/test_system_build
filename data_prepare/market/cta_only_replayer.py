import shutil
from public.main_config import *
from data_prepare.common.config_common import ConfigCommon
from ysdata.future_info import get_platform_name
from tools.date_utils import *

from ysdata.data_info import FutureData

# strategy_loader_header_name
dll_loading_module_name_var = 'dynamic_load_module'
instance_name_var = 'instance_name'
strategy_name_var = 'strategy_name'  # use for strategy_parameter table's NAME

class DataPrepare_cta(ConfigCommon):
    def __init__(self):
        ConfigCommon.__init__(self)
        self.ini_input_dict = self.get_ini_input_dict()

    def get_future_data_from_nas(self, date, test_type):
        df = self.get_strategy_loader_df(test_type)
        ticker_list = [x for x in df['target'].values]
        ticker_list = list(set(ticker_list))
        # print ticker_list
        filename = '%s.csv' % date
        # contract_data likes CFFIC1805
        for symbol in ticker_list:
            df = FutureData().get_future_type_adj_table(symbol)
            contract = df['symbol'].iloc[-1]
            # print contract
            contract_data = get_platform_name(contract, 'quote')
            src_data_path = os.path.join(future_data_path, contract_data)
            src_data_csv = os.path.join(src_data_path, filename)
            des_data_path = os.path.join(future_quote_data_path, contract_data)
            des_data_csv = os.path.join(des_data_path, filename)
            if check_if_exist(des_data_csv):
                platform_logger.warning('file exists: %s' % des_data_csv)
            else:
                platform_logger.info('lack file %s' % des_data_csv)
                os.chdir(future_quote_data_path)
                if not os.path.exists(contract_data):
                    os.mkdir(contract_data)
                shutil.copyfile(src_data_csv, des_data_csv)
                file_logger.info(os.path.join(des_data_path, filename))
                os.chdir(des_data_path)
        return des_data_csv

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

            elif component in ['mktdtcenter', 'mktudpsvr', 'ordudp', 'strategyloader']:
                pass

            config_file_path = self.write_config_ini_from_template(config_file_name, dict_)
            if component == 'strategyloader':
                pass
                # file_ = file(os.path.join(platform_path, config_file_name), 'a+')
                # file_.write(self.write_strategy_parameter_list_str(test_type))
                # file_.close()

            startup_dict[component] = config_file_path
        return startup_dict

    # ================================== main process ====================================================
    def start_future_data_preparation(self, date, component_list):
        test_type = 'future'
        self.get_future_data_from_nas(date,test_type)

        # write component config
        self.write_all_component_config(date, component_list, test_type)

        return

if __name__ == '__main__':
    date = '20180323'
    data_prepare = DataPrepare_cta()
    data_prepare.start_future_data_preparation(date,component_list={'mktcsv'})