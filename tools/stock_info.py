import os
import pandas as pd

from tools.path_unit import stock_path
from tools.time_unit import CalendarUtil
from tools.common_unit import check_if_exist
calendar = CalendarUtil()


def get_stock_summary_df(date):
    '''
    get stock summary information data_frame on date
    :param date: format '%Y%m%d' like 20170710
    :return: data_frame which index is ticker code
    '''
    summary_filepath = os.path.join(stock_path, date, 'market_data', 'summary.csv')
    df = pd.read_csv(summary_filepath, dtype={'symbol': str})
    df.index = df['symbol']
    return df


def check_ticker_validity(ticker, date):
    '''
    check whether the existence of market file of ticker on date
    :param ticker: 000001
    :param date: 'format '%Y%m%d' like 20170710'
    :return:
    '''
    data_type = ['order', 'transaction', 'market_data']
    if_all_good = True
    error_msg = ''
    for type_ in data_type:
        filename = '%s_%s_%s.csv' % (ticker, date, type_)
        filepath = os.path.join(stock_path, date, type_, filename)
        if ticker[0] == '6' and type_ == 'order':
            continue

        if not check_if_exist(filepath):
            if_all_good = False
            error_msg += 'lack file %s\n' % filename

    if not if_all_good:
        print error_msg

    return if_all_good


def get_index_filepath(index_code, date):
    '''
    :param index_code: normal index_code like 000016, get correct filepath of index
    :param date: 'format '%Y%m%d' like 20170710'
    :return: filepath of your input index_Code
    '''
    df = pd.read_csv(os.path.join(stock_path, 'change_list.csv'),
                     dtype={'original': str, 'changed': str})
    df.index = df['original']
    filename = '%s_%s_index_data.csv' % (df.at[index_code, 'changed'], date)
    index_path = os.path.join(stock_path, date, 'index_data', filename)
    return index_path


def get_stock_trade_time_period(date, time_end='.000'):
    trade_time_period = [
        ['%s 09:30:00%s' % (date, time_end), '%s 11:30:00%s' % (date, time_end)],
        ['%s 13:00:00%s' % (date, time_end), '%s 15:00:00%s' % (date, time_end)]
    ]
    return trade_time_period


if __name__ == '__main__':
    day = '20170710'
    tick = '603999'
    summary = get_stock_summary_df(day)
    print get_index_filepath('000016', day)
