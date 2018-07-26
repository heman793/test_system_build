import numpy as np
from tools.time_unit import DatetimeUtil
from data_prepare.common.config_common import ConfigCommon
from public.main_config import *
import json

dll_loading_module_name_var = 'dynamic_load_module'
instance_name_var = 'instance_name'
strategy_name_var = 'strategy_name'  # use for strategy_parameter table's NAME

class Strategy_para(ConfigCommon):
    def __init__(self):
        ConfigCommon.__init__(self)
        self.physical_date = DatetimeUtil().get_today('%Y-%m-%d')
        self.physical_datetime = DatetimeUtil().get_today('%Y-%m-%d %H:%M:%S')
        self.ini_input_dict = self.get_ini_input_dict()

    @staticmethod
    def get_sql_template(table):
        """
        return insert sql template string
        :param table:
                portfolio: 'account_position', 'pf_position',
                strategy: 'strategy_parameter'
        :return: template_str
        """
        if table == 'strategy_state':
            sql = "insert into strategy_state values ('%s', '%s', '%s')"

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

    def get_strategy_parameter_string(self, ticker_param_set_list):
        parameter_value_dict = dict()
        parameter_value_dict['Account'] = fund_name
        for [ticker, param_set] in ticker_param_set_list:
            parameter_list = self.parameter_dict[str(param_set)].split(',')
            for ind in range(len(parameter_list)):
                key = '%s_%s' % (ticker, self.parameter_title[ind])
                parameter_value_dict[key] = parameter_list[ind]
        return json.dumps(parameter_value_dict)

    def get_strategy_state_string(self, ticker_param_set_list):
        return

    def insert_stock_strategy(self, test_type):
        df = self.get_strategy_loader_df(test_type)
        strategy_name_field = 'strategy_parameter_name'
        df[strategy_name_field] = map(lambda a, b: '%s.%s' % (a, b), df[strategy_name_var], df[instance_name_var])
        group = df.groupby(strategy_name_field)
        sql_list = []
        strategy_sql_template = self.get_sql_template('strategy_parameter')
        for strategy_name, data in group:
            ticker_param_set_list = np.array(data[['target', 'param_set']]).tolist()
            parameter_dict_json = self.get_strategy_parameter_string \
                (ticker_param_set_list)
            sql = strategy_sql_template % \
            (self.physical_datetime, strategy_name, parameter_dict_json)
            sql_list.append(sql)
        print sql_list
        self.execute_db_sql('strategy', sql_list)

    # =================== insert parameter into db ==========================
    def insert_db_strategy(self, test_type):
        test_type == 'stock'
        self.insert_stock_strategy(test_type)


    def start_init_process(self, test_type):
        test_type == 'stock'
        self.insert_db_strategy(test_type)

if __name__ == '__main__':
    common_cfg = ConfigCommon().get_ini_input_dict()
    strategy_para = Strategy_para()
    strategy_para.start_init_process(test_type='stock')
