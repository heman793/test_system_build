import pandas as pd
from public.main_config import *


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
    def get_strategy_loader_df(test_type):
        """
        you should prepare strategy_loader config file on strategy_config_path, with such format
        'strategy_loader_%s.csv' % target_type
        :param target_type: 'stock', 'future' and 'option'
        :return:
        """
        filename = 'test_data_%s.csv' % test_type
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         dtype={'target': str,'account_id': str,
                                'pf_account_id': str}, index_col='test_case_no')
        if test_type == 'stock':
            df['target'] = df['target'].apply(lambda x: x.zfill(6))
            return df

        elif test_type == 'future':
            return df

        elif test_type == 'all':
            return df

    def get_target_pre_price(self, ticker):
        sql_command = "select prev_close, ticker from instrument "
        df = pd.read_sql_query(sql_command, con=get_conn_db("common"),
                            index_col='ticker')
        pre_close = df.at[ticker, 'prev_close']
        return pre_close

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

if __name__ =='__main__':
    common_cfg = ConfigCommon()
    data = common_cfg.get_strategy_loader_df(test_type='future')
    # print data