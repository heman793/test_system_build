from tools.time_unit import DatetimeUtil
from data_prepare.instrument.instrument_update import InstrumentUpdate
from public.main_config import *
from data_prepare.common.config_common import ConfigCommon
from ysdata.data_info import FutureData
from ysdata.future_info import *
import sys
from decimal import *
from MySQLdb.cursors import DictCursor

class DataBaseUnit(ConfigCommon):
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
        if table == 'account_position':
            sql = "insert into account_position values " \
                  "('%s', '%s', '%s', '0', '%f', '%f', '%f', '0', '0', '%f', '%f', '%f', '0', '0'" \
                  ",'0', '0', '0', null, null, null, null, null, '0', '0', " \
                  "'0', '0', '%f', '0', '0', '%s');"

        elif table == 'pf_position':
            sql = "insert into pf_position values " \
                  "('%s', '%s', '%s', '0', '%f', '%f', '%f', '0', '0', '%f', " \
                  "'%f', '%f', '0', '0', '0', '0', null, '1'," \
                  " '0', '0', '0', '0', '0', '0', '0', '0', '%f', '0', '0', '0', null);"

        elif table == 'account_trade_restrictions':
            sql = "insert into account_trade_restrictions values " \
                  "('%s', '%s', '18', '0', '1000', '0', '1000', '0', '2000', " \
                  "'0', '3000', '0', '1000', '0', '1000', '0','1000', '1000', '0.9'," \
                  " '1000', '0.2', '0.1','100000000', '0', '0',  '0', " \
                  "'0', '0','0' )"
        elif table == 'instrument':
            sql = "select ticker, pre_price from instrument where  ticker= '%s'"

        elif table == 'pf_account':
            sql = "insert into pf_account values" \
                  "('%s', '%s', '%s', '%s', null, '');"
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

    def get_target_pre_price(self, ticker):
        sql_command = "select prev_close, ticker from instrument "
        df = pd.read_sql_query(sql_command, con=get_conn_db("common"),
                            index_col='ticker')
        pre_close = df.at[ticker, 'prev_close']
        return pre_close

    # =================== clear database before insert ======================
    def clear_db_om(self):
        delete_table_list = ['order_broker', 'order_history', '`order`',
                             'trade2', 'trade2_broker', 'trade2_history']
        sql_list = []
        delete_sql = "delete from %s"
        map(lambda table: sql_list.append(delete_sql % table),
             delete_table_list)
        self.execute_db_sql(db='om', sql_list=sql_list)
        print sql_list

    def clear_db_portfolio(self, date):
        sql_list = []
        # print "hello"
        delete_sql = "delete from %s where DATE = '%s'"
        delete_table_list = ['pf_position', 'account_position']
        map(lambda table: sql_list.append(delete_sql % (table, date)), delete_table_list)
        self.execute_db_sql(db='portfolio', sql_list=sql_list)
        print sql_list

    def clear_pf_account(self, test_type):
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        filename = 'account_%s.csv' % test_type
        df = pd.read_csv(os.path.join(strategy_config_path, filename))
        sql_list = []
        for ind in df.index.values:
            pf_account_id = df.at[ind, 'pf_account_id']
            delete_sql = "delete from %s where id = '%s'"
            delete_table_list = ['pf_account']
            map(lambda table: sql_list.append(delete_sql % (table, pf_account_id)),
                delete_table_list)
        self.execute_db_sql(db='portfolio', sql_list=sql_list)
        print sql_list

    def insert_pf_account(self, test_type):
        sql_list = []
        filename = 'account_%s.csv' % test_type
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename))
        for ind in df.index.values:
            account_id = df.at[ind, 'account_id']
            pf_account_id = df.at[ind, 'pf_account_id']
            instance_name = df.at[ind, 'instance_name']
            dynamic_load_module = df.at[ind, 'dynamic_load_module']
            strategy_fund_name = '%s-%s-%s-' % \
                                 (instance_name, dynamic_load_module, fund_name)
            sql_pf_account_template = self.get_sql_template('pf_account')
            sql_pf_account = sql_pf_account_template % \
                         (pf_account_id, instance_name,
                          strategy_fund_name, dynamic_load_module)
            sql_list.append(sql_pf_account)
        self.execute_db_sql('portfolio', sql_list)
        print sql_list


    def clear_table_restrictions(self):
        sql_list = []
        delete_sql = "delete from %s"
        delete_table_list = ['account_trade_restrictions']
        map(lambda table: sql_list.append(delete_sql % table), delete_table_list)
        self.execute_db_sql(db='portfolio', sql_list=sql_list)
        print sql_list

    def insert_db_common(self, date):
        InstrumentUpdate().update_instrument_day(date)

    def get_target_symbol(self, test_type, clientid):
        df = self.get_strategy_loader_df(test_type)
        symbol = df.at[clientid, 'target']
        if test_type == 'future':
            df1 = FutureData().get_future_type_adj_table(symbol)
            contract = df1['symbol'].iloc[-1]
            contract_str = get_platform_name(contract, 'quote')
            ticker = contract_str[3:]
        else:
            ticker = symbol
        return ticker

    def insert_db_portfolio(self, test_type):
        sql_list = []
        sql_account_sql_template = self.get_sql_template('account_position')
        sql_pf_sql_template = self.get_sql_template('pf_position')
        filename = 'test_data_%s.csv' % test_type
        strategy_config_path = os.path.join(version_path,
                                            '%s_Config' % test_type)
        df = pd.read_csv(os.path.join(strategy_config_path, filename),
                         index_col='test_case_no')

        for clientid in df.index.values:
            target = self.get_target_symbol(test_type,clientid)
            pre_prc = self.get_target_pre_price(target)
            long_amount = df.at[clientid, 'long']
            long_cost = float(long_amount) * float(pre_prc)
            short_amount = df.at[clientid, 'short']
            short_cost = float(short_amount) * float(pre_prc)
            prev_net = abs(long_amount - short_amount)
            account_id = df.at[clientid, 'account_id']
            pf_account_id = df.at[clientid, 'pf_account_id']
            sql_account = sql_account_sql_template % \
                          (self.physical_date, account_id, target, long_amount, long_cost, long_amount,
                           short_amount, short_cost, short_amount, prev_net, self.physical_datetime)
            sql_pf_position = sql_pf_sql_template % \
                          (self.physical_date, pf_account_id, target, long_amount,
                           long_cost, long_amount, short_amount, short_cost,
                           short_amount, prev_net)

            sql_list.append(sql_account)
            sql_list.append(sql_pf_position)
        self.execute_db_sql('portfolio', sql_list)
        print sql_list

    def insert_portfolio_cny(self, test_type):
        df = self.get_strategy_loader_df(test_type)
        sql_list = []
        cash_num = 1000000000.000000
        account_id = [x for x in df['account_id'].values]
        account_id = list(set(account_id))
        # print account_id
        for id in account_id:
            sql_template = self.get_sql_template('account_position')
            sql_account = sql_template % (self.physical_date, id, 'CNY',
                                          cash_num, 0, cash_num, 0, 0, 0, cash_num,
                                          self.physical_datetime)
            sql_list.append(sql_account)
        self.execute_db_sql(db='portfolio', sql_list=sql_list)
        print sql_list

    def insert_portfolio_restrictions(self, test_type):
        df = self.get_strategy_loader_df(test_type)
        sql_list = []
        account_id_un = [x for x in df['account_id'].values]
        account_id_un = list(set(account_id_un))
        # print account_id_un
        for id in account_id_un:
            sql_template = self.get_sql_template('account_trade_restrictions')
            sql_restrictions = sql_template % (id, 'all')
            sql_list.append(sql_restrictions)


        for clientid in df.index.values:
            symbol = self.get_target_symbol(test_type, clientid)
            account_id = df.at[clientid, 'account_id']
            sql_template = self.get_sql_template('account_trade_restrictions')
            sql_restrictions = sql_template % (account_id, symbol)
            sql_list.append(sql_restrictions)
        # print sql_list

        self.execute_db_sql(db='portfolio', sql_list=sql_list)
        print sql_list

    def start_init_process(self, date, test_type):
        self.insert_db_common(date)
        self.clear_db_om()
        self.clear_db_portfolio(self.physical_date)
        self.clear_pf_account(test_type)
        self.insert_pf_account(test_type)
        self.clear_table_restrictions()
        self.insert_portfolio_cny(test_type)
        self.insert_db_portfolio(test_type)
        self.insert_portfolio_restrictions(test_type)

if __name__ == '__main__':
    date = '20180713'
    test_type = 'all'
    common_cfg = ConfigCommon().get_ini_input_dict()
    sql_prepare = DataBaseUnit()
    sql_prepare.start_init_process(sys.argv[1], sys.argv[2])
    # sql_prepare.start_init_process(date, test_type)
    # sql_prepare.get_target_symbol(test_type, clientid)
    # sql_prepare.clear_db_om()
    # sql_prepare.insert_db_portfolio(test_type)
    # sql_prepare.clear_pf_account(test_type)
    # sql_prepare.get_target_pre_price(ticker='600000')
    # sql_prepare.insert_db_portfolio(test_type)