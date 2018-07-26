import pandas as pd
import datetime

from public.main_config import *

from server_python.Lts_price_analysis_add import lts_price_analysis_add
from server_python.Lts_price_analysis import lts_price_analysis
from server_python.ctp_price_analysis_add import ctp_price_analysis_add
from server_python.ctp_price_analysis import ctp_price_analysis
from server_python.update_by_etf_file import update_by_pcf_file

check_fields = [
    'ID', 'TICKER', 'EXCHANGE_ID', 'PREV_CLOSE', 'PREV_CLOSE_UPDATE_TIME', 'PREV_SETTLEMENTPRICE',
    'TRACK_UNDL_TICKERS', 'PCF', 'UPDATE_DATE',
    u'LONGMARGINRATIO', u'SHORTMARGINRATIO',
    u'LONGMARGINRATIO_SPECULATION', u'SHORTMARGINRATIO_SPECULATION',
    u'LONGMARGINRATIO_HEDGE', u'SHORTMARGINRATIO_HEDGE',
    u'LONGMARGINRATIO_ARBITRAGE', u'SHORTMARGINRATIO_ARBITRAGE'
]


class InstrumentUpdate(object):

    def __init__(self):
        time_tab_format = '%Y-%m-%d'
        self.physical_date = datetime.datetime.now().strftime(time_tab_format)
        self.physical_date_begin = '%s 00:00:00' % self.physical_date
        self.pre_trade_day = calendar.get_last_trade_day(self.physical_date, time_tab_format)
        self.pre_close_update_time = '%s 15:00:00' % self.pre_trade_day
        self.table = 'instrument'
        self.stock_buy_commission = 0.00027
        self.stock_sell_commission = 0.00127

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
    def get_qa_conn(db='common', ip=sql_server):
        qa_conn = MySQLdb.connect(
            host=ip,
            user=sql_user,
            passwd=sql_password,
            db="%s" % db,
            charset="GBK"
        )
        return qa_conn

    @staticmethod
    def get_existed_etf_pcf_list(date):
        folder_path = os.path.join(etf_file_path, date)
        etf_files = filter(lambda x: x.endswith('.ETF'), os.listdir(folder_path))
        pcf_files = filter(lambda x: x.startswith('pcf'), os.listdir(folder_path))
        etf_list = map(lambda x: x.replace('_', '')[:-8], etf_files)
        pcf_list = map(lambda x: x.split('_')[1], pcf_files)
        if '50' in etf_list:
            etf_list.remove('50')
            etf_list.append('510050')
        if '180' in etf_list:
            etf_list.remove('180')
            etf_list.append('510180')
        if 'YQ50' in etf_list:
            etf_list.remove('YQ50')
            etf_list.append('510060')
        if 'HL' in etf_list:
            etf_list.remove('HL')
            etf_list.append('510880')

        etf_pcf_list = []
        etf_pcf_list.extend(etf_list)
        etf_pcf_list.extend(pcf_list)
        return etf_pcf_list

    def get_sql_dataframe(self, sql, conn=None):
        if conn is None:
            conn = self.get_qa_conn('common')
        df = pd.read_sql(sql, conn)
        conn.close()
        return df

    def check_option_pcf_field(self, date):
        sql = "SELECT * FROM %s WHERE PCF IS NULL " % self.table
        df = self.get_sql_dataframe(sql)
        ticker_list = [x for x in df['TICKER'].values]

        etf_pcf_list = self.get_existed_etf_pcf_list(date)
        ticker_list = filter(lambda ticker: ticker in etf_pcf_list, ticker_list)

        if len(ticker_list):
            platform_logger.error('PCF Error, field is empty: %s ' % ','.join(ticker_list))

    def check_ctp_long_short_field(self):
        sql_template = "SELECT ID, TICKER, %s FROM %s WHERE TYPE_ID = 1"
        long_short_fields = [
            u'LONGMARGINRATIO', u'SHORTMARGINRATIO',
            u'LONGMARGINRATIO_SPECULATION', u'SHORTMARGINRATIO_SPECULATION',
            u'LONGMARGINRATIO_HEDGE', u'SHORTMARGINRATIO_HEDGE',
            u'LONGMARGINRATIO_ARBITRAGE', u'SHORTMARGINRATIO_ARBITRAGE'
        ]
        sql = sql_template % (','.join(long_short_fields), self.table)
        df = self.get_sql_dataframe(sql)
        df.index = df['ID']
        df = df.fillna(0)
        df_data = pd.DataFrame()
        for field in long_short_fields:
            empty_df = df[df[field] == 0]
            df_data = pd.concat([df_data, empty_df])
        df_data = df_data.drop_duplicates()

        for ind in df_data.index.values:
            ticker = df_data.at[ind, 'TICKER']
            zero_field_list = []
            for field in long_short_fields:
                if df_data.at[ind, field] == 0:
                    zero_field_list.append(field)
            platform_logger.error('LongShort Field Error, ID: %s; TICKER: %s; Zero/Empty Field: %s' %
                                 (ind, ticker, ','.join(zero_field_list)))

    def check_track_undl_tickers_field(self):
        check_field = 'TRACK_UNDL_TICKERS'
        sql = "SELECT ID, TICKER FROM instrument WHERE TYPE_ID = 10 AND %s IS NULL;" % check_field
        df = self.get_sql_dataframe(sql)
        df.index = df['ID']
        for ind in df.index.values:
            ticker = df.at[ind, 'TICKER']
            platform_logger.error('%s Error, field is empty: ID: %s; TICKER: %s' % (check_field, ind, ticker))

    def check_pre_close_field(self):
        sql = "SELECT ID, TICKER, PREV_CLOSE FROM instrument WHERE " \
              "TYPE_ID in (1, 4) AND EXCHANGE_ID IN (18, 19) AND PREV_CLOSE_UPDATE_TIME = '%s'"\
              % self.pre_close_update_time
        df = self.get_sql_dataframe(sql)
        df_empty = df[df['PREV_CLOSE'].isnull()]
        df_empty.index = df_empty['ID']
        for ind in df_empty.ID:
            ticker = df_empty.at[ind, 'TICKER']
            platform_logger.error("PREV_CLOSE error, it's empay, ID: %s; TICKER: '%s" % (ind, ticker))

    def check_is_settle_instantly_field(self):
        check_field = 'IS_SETTLE_INSTANTLY'
        sql = "SELECT ID, TICKER FROM instrument WHERE TYPE_ID = 1 AND %s = 0;" % check_field
        df = self.get_sql_dataframe(sql)
        df.index = df['ID']
        for ind in df.index.values:
            ticker = df.at[ind, 'TICKER']
            platform_logger.error('%s Error, field is 0: ID: %s; TICKER: %s' % (check_field, ind, ticker))

        sql = "SELECT ID, TICKER, %s FROM instrument WHERE TYPE_ID = 15;" \
              % check_field
        df = self.get_sql_dataframe(sql)
        df.index = df['ID']
        for ind in df.index.values:
            ticker = df.at[ind, 'TICKER']
            is_settle_instantly = df.at[ind, 'IS_SETTLE_INSTANTLY']
            if is_settle_instantly == 0:
                platform_logger.error('%s Error, field is 0: ID: %s; TICKER: %s' % (check_field, ind, ticker))

    def update_stock_buy_sell_commission(self):
        """
        only update A stock buy_commission and
        :return: nothing
        """
        sql = "update instrument set BUY_COMMISSION = %f, SELL_COMMISSION = %f " \
              "WHERE TYPE_ID = 4 AND EXCHANGE_ID IN (18, 19)" % (self.stock_buy_commission, self.stock_sell_commission)
        self.execute_db_sql('common', [sql])

    def update_pre_close_update_time(self):
        # 'PREV_CLOSE_UPDATE_TIME', 'CLOSE_UPDATE_TIME', 'UPDATE_DATE'
        sql_template = "UPDATE instrument SET %s = '%s' WHERE %s > '%s'"
        sql = sql_template % \
              ('PREV_CLOSE_UPDATE_TIME', self.pre_close_update_time, 'UPDATE_DATE', self.physical_date_begin)
        self.execute_db_sql('common', [sql])

    def update_future_option_trade_session(self):
        sql_template = "UPDATE instrument SET `SESSION` = '(19700101," \
                       "20991231)(1,5)(08:00:00,23:00:00)'  where exchange_id in (20,21,22,25)"
        self.execute_db_sql('common', [sql_template])

    def update_instrument_day(self, date):
        # ZhouJie project
        lts_price_analysis_add(date)
        lts_price_analysis(date)
        ctp_price_analysis_add(date)
        ctp_price_analysis(date)
        update_by_pcf_file(date)

        # update for QA environment
        self.update_stock_buy_sell_commission()
        self.update_pre_close_update_time()
        self.update_future_option_trade_session()
        # Field checking
        self.check_pre_close_field()
        self.check_track_undl_tickers_field()
        self.check_option_pcf_field(date)
        self.check_ctp_long_short_field()
        self.check_is_settle_instantly_field()

    @staticmethod
    def get_ip_conn(ip, db='common'):
        info_map = {
            '172.16.12.66': {'user': 'linhua', 'passwd': '123linhua'},
            '172.16.10.126': {'user': 'llh', 'passwd': 'llh@yansheng'}
        }
        conn = MySQLdb.connect(
            host=ip,
            user=info_map[ip]['user'],
            passwd=info_map[ip]['passwd'],
            db="%s" % db,
            charset="GBK"
        )
        return conn

    def record_instrument_info(self, ip, file_path):
        conn = self.get_ip_conn(ip)

        sql = "select %s from instrument" % ','.join(check_fields)
        df = pd.read_sql(sql, conn)
        # df.to_csv(file_path, index=False)
        conn.close()
        return df

    
if __name__ == '__main__':
    # update_control()
    day = '20180713'
    iu_object = InstrumentUpdate()
    # ctp_price_analysis(day)
    iu_object.update_instrument_day(day)
    # iu_object.check_is_settle_instantly_field()
    # iu_object.check_pre_close_field()
    # from ysdata.PathUnit import
