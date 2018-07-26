import os
import pandas as pd

from tools.path_unit import future_path, gta_path, adj_path
from tools.SqlUnit import get_118_db
from tools.time_unit import CalendarUtil
from tools.common_unit import get_tab_day
calendar = CalendarUtil()

# ============================ future_info.csv ====================================================
future_info = pd.read_csv(os.path.join(future_path, 'future_info.csv'), encoding='GBK')
future_info.index = future_info['symbol']
DCE = future_info[future_info['exchange'] == 'DCE']['symbol'].tolist()
SHF = future_info[future_info['exchange'] == 'SHF']['symbol'].tolist()
ZCE = future_info[future_info['exchange'] == 'ZCE']['symbol'].tolist()
CFF = future_info[future_info['exchange'] == 'CFF']['symbol'].tolist()
NIGHT_FUTURE = future_info[future_info['night'] == 'Y']['symbol'].tolist()
all_future = future_info['symbol'].tolist()
Bond = ['T', 'TF']
Index = ['IF', 'IH', 'IC']
Commodity = list(set(all_future).difference(set(CFF)))


def if_night_future_type(future_type):
    return future_type in NIGHT_FUTURE


# ctp output name is capital for some future_type, others not
def get_ctp_future_type_name(future_type):
    return future_info.at[future_type.upper(), 'ctp_symbol']


def get_future_type_unit(future_type):
    return future_info.at[future_type.upper(), 'unit']


def get_future_type_point_value(future_type):
    return future_info.at[future_type.upper(), 'point_value']


def get_exchange(future_type):
    return future_info.at[future_type.upper(), 'exchange']


def get_wind_exchange(future_type):
    return future_info.at[future_type.upper(), 'wind_exchange']


def get_future_type_name(future_type):
    return future_info.at[future_type.upper(), 'name']


# ============================= additional function ===============================================
def get_platform_name(contract, data_type='quote'):
    '''
    for yansheng platform data name_format
    :param contract: show input full year month, for example ZC1705, not ZC705
    :param data_type: there are two type output type ,for 'quote' or 'bar'
                    for 'quote', output is '%s%s' % (exchange, contract)
                    for 'bar', output is '%s %s m' % (contract, exchange)
    :return: bar or quote name for ys platform
    '''
    future_type = contract[:-4]
    exchange = get_exchange(future_type)
    future_type = get_ctp_future_type_name(future_type)
    if future_type not in ZCE and future_type not in CFF:
        new_contract = contract.lower()
    else:
        if future_type in ZCE:
            new_contract = future_type + contract[-3:]
        else:
            new_contract = future_type + contract[-4:]

    if data_type == 'bar':
        return '%s %s m' % (new_contract, exchange)
    elif data_type == 'quote':
        return '%s%s' % (exchange, new_contract)
    else:
        print 'not a right data_type, please input quote or bar'
        return None


def get_future_trade_time(future_type, date):
    conn = get_118_db('basic_info')
    sql = "select time from trading_info WHERE symbol = '%s' and date = '%s'" % \
          (future_type.upper(), date)
    df = pd.read_sql(sql, conn)
    trade_time = df['time'].iloc[0][5:]
    trade_time = trade_time.replace('(', '')
    trade_time = trade_time.replace(')', '')
    periods = trade_time.split(';')
    conn.close()
    return periods


# ============================ market data, summary ===============================================
def get_origin_future_df(contract, date):
    '''
    :param contract: contract with full year and month, and with capital letter, like RB1705
    :param date: '%Y%m%d'
    :return: data_frame
    '''
    contract = contract.upper()
    filepath = os.path.join(gta_path, date, 'tick', '%s.csv' % contract)
    try:
        df = pd.read_csv(filepath)
    except IOError:
        print 'lack file %s' % filepath
        return pd.DataFrame()
    return df


def get_future_summary_df(date):
    '''
    return summary data_frame, you can use data_frame to get serveral fields
    e.g df.at[contract, field], symbol is contract, field like 'high_limited', 'low_limited'
        ohlc, volume, turnover, prev_close
    :param date: '%Y%m%d'
    :return: data_frame
    '''

    filepath = os.path.join(gta_path, date, 'tick', 'summary.csv')
    df_summary = pd.read_csv(filepath)
    df_summary.index = df_summary['symbol']
    return df_summary


# ============================ future trade time ==================================================
def get_future_trade_time_df(df, future_type, date, time_field='datetime', time_end='.000',
                             label='left'):
    df.index = df[time_field].astype('str')
    periods = get_future_trade_time(future_type, date)
    data = pd.DataFrame()
    date_ = get_tab_day(date)
    last_day = calendar.get_last_trade_day(date_, '%Y-%m-%d')
    satuday = calendar.get_next_day(last_day, '%Y-%m-%d')

    for period in periods:
        [start, end] = period.split(',')
        if start == '21:00:00':
            start = '%s %s%s' % (last_day, '21:00:00', time_end)
            if end <= '02:30:00':
                end = '%s %s%s' % (satuday, end, time_end)
            else:
                end = '%s %s%s' % (last_day, end, time_end)
        else:
            start = '%s %s%s' % (date_, start, time_end)
            end = '%s %s%s' % (date_, end, time_end)

        # print start, end
        if label == 'left':
            b1 = df[time_field] >= start
            b2 = df[time_field] < end
            temp_data = df[b1 & b2]
            # left left left
        elif label == 'right':
            b1 = df[time_field] > start
            b2 = df[time_field] <= end
            temp_data = df[b1 & b2]

        elif label == 'all':
            temp_data = df[start: end]

        else:
            temp_data = pd.DataFrame()

        data = pd.concat([data, temp_data])
    return data


def get_main_contract(future_type, date):
    '''
    :param future_type: input future_type
    :param date: '%Y%m%d' like 20170630
    :return: main contract of future_type on date
    '''
    filepath = os.path.join(adj_path, 'adj_table_night', '%s.csv' % future_type.upper())
    df = pd.read_csv(filepath)
    df.index = df['datetime'].astype('str')
    return df.at[date, 'symbol']


if __name__ == '__main__':
    # print get_ctp_future_type_name('ZN')
    day = '20170630'
    contract_ = 'RB1709'
    temp = get_origin_future_df(contract_, day)
    symbol = contract_[:-4]
    temp = get_future_trade_time_df(temp, symbol, day)
    print get_main_contract(symbol, day)
    # temp.to_csv(os.path.join(future_path, 'test.csv'), index=False)
