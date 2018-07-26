# -*- coding: utf-8 -*-
import os
import datetime
import shutil
import sys
import numpy
import pandas as pd
import csv
from model.instrument import Instrument
from model.instrument_history import InstrumentHistory
from model.quote_bar_info import QuoteBarInfo
from model.minute_bar_info import MinuteBarInfo
from model.server_constans import ServerConstant
from tools.date_utils import DateUtils

instrument_dict = dict()
trading_time_dict = dict()
date_utils = DateUtils()

quote_dict = dict()
minbar_dict = dict()

chunksize = 10 ** 5
interval_time = 60
quote_size = 4000
minbar_size = 500

ctp_header_list = [
    'TradingDay', 'InstrumentID', 'ExchangeID', 'ExchangeInstID', 'lastPrice',
    'PreSettlementPrice', 'preClosePrice', 'PreOpenInterest', 'openPrice',
    'highestPrice', 'lowestPrice', 'volume', 'turnover', 'open_interest',
    'closePrice', 'settlementPrice', 'upperLimitPrice', 'lowerLimitPrice',
    'preDelta', 'currDelta', 'UpdateTime', 'UpdateMillisec', 'bidPrice1',
    'BidVolume1', 'askPrice1', 'AskVolume1', 'bidPrice2', 'BidVolume2',
    'askPrice2', 'AskVolume2', 'bidPrice3', 'BidVolume3', 'askPrice3',
    'AskVolume3', 'bidPrice4', 'BidVolume4', 'askPrice4', 'AskVolume4',
    'bidPrice5', 'BidVolume5', 'askPrice5', 'AskVolume5', 'AveragePrice',
    'actionDay', 'localtime'
]

ctp_reheader = [
    'datetime', 'temp', 'exchtime', 'last_prc', 'open_interest', 'volume',
    'turnover', 'ask_prc1', 'ask_vol1', 'bid_prc1', 'bid_vol1', 'open', 'close',
    'high', 'low', 'prev_close', 'prev_settlement', 'prev_open_interest',
    'settlement', 'high_limited', 'low_limited', 'localtime', 'num'
]

ctp_reorder = [
    'actionDay', 'UpdateTime', 'UpdateMillisec', 'lastPrice', 'open_interest',
    'volume', 'turnover', 'askPrice1', 'AskVolume1', 'bidPrice1', 'BidVolume1',
    'openPrice', 'closePrice', 'highestPrice', 'lowestPrice', 'preClosePrice',
    'PreSettlementPrice', 'PreOpenInterest', 'settlementPrice',
    'upperLimitPrice', 'lowerLimitPrice', 'localtime', 'num'
]

# market_file_path = '/home/trader/dailyjob/DerivativesClient/marketFile'
# quotes_base_file_folder = '/home/trader/history_data/quotes_base'
# quotes_file_folder = '/home/trader/history_data/quotes'
# minbar_file_folder = '/home/trader/history_data/bars'

market_file_path = 'E:/history_data/ctp_data'
quotes_base_file_folder = 'E:/history_data/ctp_data/quotes_base'
quotes_file_folder = 'E:/history_data/ctp_data/quotes'
minbar_file_folder = 'E:/history_data/ctp_data/bars'


def start_build_file():
    build_quotes_minbar_file()

def start(ctp_file_name):
    build_quotes_base(ctp_file_name)
    build_quotes_minbar_file()


def build_quotes_base(ctp_file_name):
    if ctp_file_name is None:
        ctp_file_name = __filter_market_file(market_file_path)
    print 'start read file:%s' % (ctp_file_name,)

    # 添加文件头
    ctp_file_path = '%s/%s' % (market_file_path, ctp_file_name)
    index_num = 0
    for chunk in pd.read_csv(os.path.join(ctp_file_path),
                             chunksize=chunksize,
                             names=ctp_header_list,
                             dtype={'actionDay': object, 'UpdateTime': object,
                                    'UpdateMillisec': object}):
        chunk['num'] = numpy.arange(index_num, index_num + len(chunk))
        index_num += len(chunk)
        b1 = chunk['UpdateTime'] >= '20:30:00'
        b2 = chunk['UpdateTime'] <= '23:59:59'
        b3 = chunk['UpdateTime'] >= '08:30:00'
        b4 = chunk['UpdateTime'] <= '16:00:00'
        b5 = chunk['UpdateTime'] >= '00:00:00'
        b6 = chunk['UpdateTime'] <= '02:59:59'
        # b7 = chunk['actionDay'] == actday
        # b8 = chunk['actionDay'] == preday
        # b9 = chunk['actionDay'] == satday
        # chunk = chunk[(b1 & b2 & b8) | (b3 & b4 & b7) | (b5 & b6 & b9)]
        chunk = chunk[(b1 & b2) | (b3 & b4) | (b5 & b6)]

        chunk['UpdateMillisec'] = chunk['UpdateMillisec'].astype('int').apply(lambda x: '%03d' % x)
        chunk['actionDay'] = chunk['actionDay'].astype('str').apply(lambda x: x[:4] + '-' + x[4:6] + '-' + x[6:8])
        # chunk['actionDay'] = chunk['actionDay'].astype('str').apply(lambda x: x.split(' ')[0])
        chunk['actionDay'] = chunk['actionDay'].astype('str') + ' ' + \
                             chunk['UpdateTime'].astype('str') + '.' + \
                             chunk['UpdateMillisec'].astype('str')
        chunk['UpdateMillisec'] = pd.to_datetime(chunk['actionDay']).apply(lambda x: (x.value - 8 * 3600 * 10 ** 9) / 1000)

        grouped = chunk.groupby('InstrumentID')
        for ticker, df in grouped:
            csv_name = os.path.join(quotes_base_file_folder, ticker + '.csv')
            df = df[ctp_reorder]
            df.columns = ctp_reheader
            if not os.path.exists(csv_name):
                df.to_csv(csv_name, index=False)
            else:
                df.to_csv(csv_name, index=False, mode='a', header=False)

def __filter_market_file(market_file_path):
    ctp_market_file_list = []
    for file_name in os.listdir(market_file_path):
        if 'Market' in file_name:
            ctp_market_file_list.append(file_name)
        ctp_market_file_list.sort()
    return ctp_market_file_list[len(ctp_market_file_list) - 1]


def __build_quotes_base(market_file_name):
    build_ticker_exchange()
    build_trading_time_dict()

    global market_file_date_str
    market_file_date_str = market_file_name[11:23]

    build_quote_data(market_file_name)

    for (ticker, quote_data_list) in quote_dict.items():
        if ticker not in instrument_dict:
            continue

        quote_data_list = quote_filter(ticker, quote_data_list)
        __save_quote_base_file(ticker, quote_data_list)


def build_quotes_minbar_file():
    print 'start build_quotes_minbar_file'
    clear_folder()
    for ticker_folder_name in os.listdir(quotes_base_file_folder):
        instrument_file_list = []
        for date_file_name in os.listdir(quotes_base_file_folder + '/' + ticker_folder_name):
            instrument_file_list.append(date_file_name)
        instrument_file_list.sort()
        if len(instrument_file_list) > 4:
            instrument_file_list = instrument_file_list[-4:]

        quote_message_list = []
        for date_file_name in instrument_file_list:
            temp_quote_message_list = []
            f = open('%s/%s/%s' % (quotes_base_file_folder, ticker_folder_name, date_file_name), 'r')
            try:
                for line in f.xreadlines():
                    temp_quote_message_list.append(line.replace('\n', ''))
            finally:
                f.close()
            quote_message_list = quote_message_list + temp_quote_message_list
        __save_quote_file(ticker_folder_name, quote_message_list)
        __build_minbar_data(ticker_folder_name, quote_message_list)


def clear_folder():
    if os.path.exists(quotes_file_folder):
        shutil.rmtree(quotes_file_folder)
    if os.path.exists(minbar_file_folder):
        shutil.rmtree(minbar_file_folder)


def __save_quote_base_file(ticker, data_list):
    if len(data_list) == 0:
        return
    content_list = []
    for data in data_list:
        content_list.append(data.to_quote_str())

    instrument_db = instrument_dict[ticker]
    if instrument_db.exchange_id == 20:
        exchange_name = 'SHF'
    if instrument_db.exchange_id == 21:
        exchange_name = 'DCE'
    if instrument_db.exchange_id == 22:
        exchange_name = 'ZCE'
    if instrument_db.exchange_id == 25:
        exchange_name = 'CFF'

    if not os.path.exists(quotes_base_file_folder):
        os.mkdir(quotes_base_file_folder)
    file_folder = quotes_base_file_folder + '/' + exchange_name + ticker
    if not os.path.exists(file_folder):
        os.mkdir(file_folder)
    file_path = '%s/%s.csv' % (file_folder, market_file_date_str)
    file_object = open(file_path, 'w+')
    file_object.write('\n'.join(content_list))
    file_object.close()


def __save_quote_file(ticker_folder_name, data_list):
    if len(data_list) > quote_size:
        data_list = data_list[-quote_size:]

    if not os.path.exists(quotes_file_folder):
        os.mkdir(quotes_file_folder)

    file_folder = quotes_file_folder + '/' + ticker_folder_name
    if not os.path.exists(file_folder):
        os.mkdir(file_folder)

    file_path = '%s/%s.csv' % (file_folder, datetime.datetime.now().strftime('%Y%m%d'))
    file_object = open(file_path, 'w')
    file_object.write('\n'.join(data_list) + '\n')
    file_object.close()


def save_minbar_file(ticker_folder_name, data_list):
    if len(data_list) == 0:
        return
    content_list = []
    for data in data_list:
        content_list.append(data.info_str())
    if len(content_list) > minbar_size:
        content_list = content_list[-minbar_size:]

    if not os.path.exists(minbar_file_folder):
        os.mkdir(minbar_file_folder)
    file_path = '%s/%s %s %s' % (minbar_file_folder, ticker_folder_name[3:], ticker_folder_name[:3], 'm')
    file_object = open(file_path, 'w+')
    file_object.write('\n'.join(content_list))
    file_object.close()


def quote_filter(ticker, data_list):
    filter_bar_list = []
    for quote_bar_info in data_list:
        if is_trading_time(quote_bar_info.date_time, ticker):
            temp_quote_info = quote_bar_info.copy()
            filter_bar_list.append(temp_quote_info)
    return filter_bar_list


def minbar_filter(ticker, data_list):
    filter_bar_list = []
    last_quote_bar = None
    for quote_bar_info in data_list:
        if is_trading_time(quote_bar_info.date_time, ticker):
            temp_quote_bar_info = quote_bar_info.copy()
            if last_quote_bar is not None:
                temp_quote_bar_info.volume = int(quote_bar_info.volume) - int(last_quote_bar.volume)
            filter_bar_list.append(temp_quote_bar_info)
            last_quote_bar = quote_bar_info
    return filter_bar_list


def is_trading_time(date_time, ticker):
    trading_time_flag = False
    if not date_utils.is_trading_day(str(date_time)[:10]):
        return trading_time_flag

    if ticker in trading_time_dict:
        trading_time_list = trading_time_dict[ticker]
    else:
        if len(ticker) == 5:
            ticker = ticker[:2] + '1' + ticker[2:]
        if ticker in trading_time_dict:
            trading_time_list = trading_time_dict[ticker]
        else:
            print 'unfind ticker:%s trading time' % (ticker,)
            trading_time_list = [('9:00', '10:15'), ('10:30', '11:30'), ('13:30', '15:00'), ('21:00', '23:00')]

    for (start_time, end_time) in trading_time_list:
        if count_time_number(start_time) <= count_time_number(str(date_time)[11:16]) < count_time_number(
                end_time):
            trading_time_flag = True
            break
    return trading_time_flag


def build_quote_data(file_name):
    file_path = '%s/%s' % (market_file_path, file_name)
    print 'start read file:%s' % (file_path,)
    f = open(file_path, 'r')
    try:
        for line in f.xreadlines():
            message_item = line.replace('\n', '').replace('	', '').split(',')
            if len(message_item) != 45:
                continue

            market_info = QuoteBarInfo()
            ticker = message_item[1]
            market_info.ticker = ticker

            date_str = message_item[43]
            date_time = '%s-%s-%s %s.%s0000' % (
                date_str[:4], date_str[4:6], date_str[6:8], message_item[20], message_item[21].zfill(3))

            market_info.date_time = date_time

            market_info.price = message_item[4]
            market_info.volume = message_item[11]

            market_info.bid1 = rebuild_value(message_item[22])
            market_info.bid_size1 = rebuild_value(message_item[23])
            market_info.ask1 = rebuild_value(message_item[24])
            market_info.ask_size1 = rebuild_value(message_item[25])

            prev_close = rebuild_value(message_item[7])
            nominal_price = prev_close
            if market_info.price > 0:
                if market_info.price <= market_info.bid1:
                    nominal_price = market_info.bid1
                elif market_info.ask1 > market_info.bid1:
                    if market_info.price > market_info.ask1:
                        nominal_price = market_info.ask1
                    else:
                        nominal_price = market_info.price
                else:
                    nominal_price = market_info.price
            else:
                if prev_close <= market_info.bid1:
                    nominal_price = market_info.bid1
                elif market_info.ask1 > market_info.bid1:
                    if prev_close > market_info.ask1:
                        nominal_price = market_info.ask1
                    else:
                        nominal_price = prev_close
                else:
                    nominal_price = prev_close
            market_info.nominal_price = nominal_price

            if ticker in quote_dict:
                quote_dict[ticker].append(market_info)
            else:
                temp_list = [market_info]
                quote_dict[ticker] = temp_list
    finally:
        f.close()


def __build_minbar_data(ticker_folder_name, quote_message_list):
    if len(quote_message_list) == 0:
        return
    first_market_info = quote_message_list[0]
    start_datetime = datetime.datetime.strptime(first_market_info[:16] + ':00', "%Y-%m-%d %H:%M:%S")
    end_datetime = start_datetime + datetime.timedelta(seconds=interval_time)

    minute_bar_info = None
    minute_bar_list = []
    for line in quote_message_list:
        message_item = line.split(',')
        datetime_str = message_item[0][:19]

        quote_bar_info = QuoteBarInfo()
        quote_bar_info.date_time = datetime_str
        quote_bar_info.price = float(message_item[1])
        quote_bar_info.volume = float(message_item[2])
        quote_bar_info.bid1 = float(message_item[3])
        quote_bar_info.bid_size1 = float(message_item[4])
        quote_bar_info.ask1 = float(message_item[18])
        quote_bar_info.ask_size1 = float(message_item[19])
        if quote_bar_info.bid1 == 0 and quote_bar_info.ask1 == 0:
            continue

        if datetime_str < start_datetime.strftime("%Y-%m-%d %H:%M:%S"):
            minute_bar_info = MinuteBarInfo()
            minute_bar_info.date_time = start_datetime.strftime("%Y-%m-%d %H:%M:%S") + '.0000000'
            minute_bar_info.open = quote_bar_info.price
            minute_bar_info.high = quote_bar_info.price
            minute_bar_info.low = quote_bar_info.price
            minute_bar_info.close = quote_bar_info.price
            minute_bar_info.volume = quote_bar_info.volume
            minute_bar_info.bid1 = quote_bar_info.bid1
            minute_bar_info.bid_size1 = quote_bar_info.bid_size1
            minute_bar_info.ask1 = quote_bar_info.ask1
            minute_bar_info.ask_size1 = quote_bar_info.ask_size1
        elif start_datetime.strftime("%Y-%m-%d %H:%M:%S") <= datetime_str < end_datetime.strftime("%Y-%m-%d %H:%M:%S"):
            if minute_bar_info is None:
                minute_bar_info = MinuteBarInfo()
                minute_bar_info.date_time = start_datetime.strftime("%Y-%m-%d %H:%M:%S") + '.0000000'
                minute_bar_info.open = quote_bar_info.price
                minute_bar_info.high = quote_bar_info.price
                minute_bar_info.low = quote_bar_info.price
                minute_bar_info.close = quote_bar_info.price
                minute_bar_info.volume = quote_bar_info.volume
                minute_bar_info.bid1 = quote_bar_info.bid1
                minute_bar_info.bid_size1 = quote_bar_info.bid_size1
                minute_bar_info.ask1 = quote_bar_info.ask1
                minute_bar_info.ask_size1 = quote_bar_info.ask_size1
            else:
                minute_bar_info.high = max(minute_bar_info.high, quote_bar_info.price)
                minute_bar_info.low = min(minute_bar_info.low, quote_bar_info.price)
                minute_bar_info.close = quote_bar_info.price
                minute_bar_info.volume = quote_bar_info.volume
                minute_bar_info.bid1 = quote_bar_info.bid1
                minute_bar_info.bid_size1 = quote_bar_info.bid_size1
                minute_bar_info.ask1 = quote_bar_info.ask1
                minute_bar_info.ask_size1 = quote_bar_info.ask_size1
        elif datetime_str >= end_datetime.strftime("%Y-%m-%d %H:%M:%S"):
            if minute_bar_info is not None:
                minute_bar_list.append(minute_bar_info)
            start_datetime = end_datetime
            end_datetime = start_datetime + datetime.timedelta(seconds=interval_time)
            while datetime_str >= end_datetime.strftime("%Y-%m-%d %H:%M:%S"):
                if len(minute_bar_list) > 0:
                    minute_bar_info = minute_bar_list[-1]
                else:
                    minute_bar_info = MinuteBarInfo()
                temp_quote_bar_info = minute_bar_info.copy()
                temp_quote_bar_info.date_time = start_datetime.strftime("%Y-%m-%d %H:%M:%S") + '.0000000'
                minute_bar_list.append(temp_quote_bar_info)

                start_datetime = end_datetime
                end_datetime = start_datetime + datetime.timedelta(seconds=interval_time)

            minute_bar_info = MinuteBarInfo()
            minute_bar_info.date_time = start_datetime.strftime("%Y-%m-%d %H:%M:%S") + '.0000000'
            minute_bar_info.open = quote_bar_info.price
            minute_bar_info.high = quote_bar_info.price
            minute_bar_info.low = quote_bar_info.price
            minute_bar_info.close = quote_bar_info.price
            minute_bar_info.volume = quote_bar_info.volume
            minute_bar_info.bid1 = quote_bar_info.bid1
            minute_bar_info.bid_size1 = quote_bar_info.bid_size1
            minute_bar_info.ask1 = quote_bar_info.ask1
            minute_bar_info.ask_size1 = quote_bar_info.ask_size1
        else:
            pass

    if minute_bar_info is not None:
        minute_bar_list.append(minute_bar_info)

    minute_bar_list = minbar_filter(ticker_folder_name[3:], minute_bar_list)
    if len(minute_bar_list) > 0:
        save_minbar_file(ticker_folder_name, minute_bar_list)


def build_ticker_exchange():
    host_server_model = ServerConstant().get_server_model('host')
    session_common = host_server_model.get_db_session('common')
    query = session_common.query(Instrument)
    for instrument_db in query.filter(Instrument.type_id == 1):
        instrument_dict[instrument_db.ticker] = instrument_db


def build_trading_time_dict():
    host_server_model = ServerConstant().get_server_model('host')
    session_history = host_server_model.get_db_session('history')
    query = session_history.query(InstrumentHistory)
    for instrument_history_db in query:
        trading_time_list = []
        if instrument_history_db.thours is None:
            continue
        for trading_time in instrument_history_db.thours.replace('(', '').replace(')', '').split(';'):
            (start_time, end_time) = trading_time.split(',')
            if count_time_number(start_time) > count_time_number(end_time):
                trading_time_list.append((start_time, '24:00'))
                trading_time_list.append(('00:00', end_time))
            else:
                trading_time_list.append((start_time, end_time))

        trading_time_dict[instrument_history_db.ticker] = trading_time_list


def count_time_number(time_str):
    return int(time_str.split(':')[0]) * 60 + int(time_str.split(':')[1])


def rebuild_value(data_value):
    if data_value == '0.000000':
        data_value = '0'
    return data_value


if __name__ == '__main__':
    # if len(sys.argv) == 1:
    #     ctp_file_name = None
    # else:
    #     ctp_file_name = sys.argv[1].strip()
    # start(ctp_file_name)
    build_quotes_base('CTP_Market_2016-12-13_2.txt')