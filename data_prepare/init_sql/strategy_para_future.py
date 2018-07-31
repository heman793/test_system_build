import numpy as np
from tools.time_unit import DatetimeUtil
from data_prepare.common.config_common import ConfigCommon
from model.strategy_online import StrategyOnline
from model.strategy_parameter import StrategyParameter
from model.server_constans import ServerConstant
from tools.date_utils import DateUtils
from public.main_config import *
import pandas as pd

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

    def clear_db_strategy(self, date):
        sql_list = []
        # print "hello"
        delete_sql = "delete from %s where TIME < '%s' and NAME='%s'"
        delete_table_list = ['strategy_parameter', 'strategy_state']
        map(lambda table: sql_list.append(delete_sql % (table, date, strategy_name_var)),
            delete_table_list)
        self.execute_db_sql(db='strategy', sql_list=sql_list)
        # print sql_list

    def insert_future_strategy_para(self):
        strategy_file_path = os.path.join(future_strategy_para_path,
                                          'strategy_parameter.csv')
        df = pd.read_csv(strategy_file_path)
        # print df
        sql_list = []
        for ind in df.index.values:
            name = df.at[ind, 'NAME']
            value = df.at[ind, 'VALUE']
            sql_strategy_para_template = self.get_sql_template(
                'strategy_parameter')
            sql_strategy_para = sql_strategy_para_template % (self.physical_datetime, name, value)
            sql_list.append(sql_strategy_para)
        print sql_list
        self.execute_db_sql('strategy', sql_list)

    def insert_future_state_para(self):
        state_file_path = os.path.join(future_strategy_para_path,
                                          'state_parameter.csv')
        df = pd.read_csv(state_file_path)
        # print df
        sql_list = []
        for ind in df.index.values:
            name = df.at[ind, 'NAME']
            value = df.at[ind, 'VALUE']
            sql_strategy_state_template = self.get_sql_template(
                'strategy_state')
            sql_strategy_para = sql_strategy_state_template % (self.physical_datetime, name, value)
            sql_list.append(sql_strategy_para)
        # print sql_list
        self.execute_db_sql('strategy', sql_list)

    def start_init_process(self):
        self.clear_db_strategy(self.physical_datetime)
        self.insert_future_strategy_para()
        self.insert_future_state_para()

if __name__ == '__main__':
    common_cfg = ConfigCommon().get_ini_input_dict()
    strategy_para = Strategy_para()
    strategy_para.start_init_process()

