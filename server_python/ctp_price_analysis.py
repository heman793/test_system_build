# -*- coding: utf-8 -*-
import os
from datetime import datetime

from model.BaseModel import *
from model.server_constans import ServerConstant
from tools.getConfig import getConfig
from model.instrument import Instrument
from tools.file_utils import FileUtils
from model.eod_parse_arguments import parse_arguments
# from public.main_config import platform_logger, get_log_format_string

now = datetime.now()
validate_time = long(now.strftime('%H%M%S'))
file_path = getConfig()['datafetcher_file_path']

session = None
instrument_db_dict = dict()


def build_instrument_db_dict():
    query = session.query(Instrument)
    for instrument_db in query:
        dict_key = '%s|%s' % (instrument_db.ticker, instrument_db.exchange_id)
        instrument_db_dict[dict_key] = instrument_db


def read_price_file_ctp(ctp_file_path):
    fr = open(ctp_file_path)
    instrument_array = []
    market_array = []
    for line in fr.readlines():
        base_model = BaseModel()
        if len(line.strip()) == 0:
            continue
        for tempStr in line.split('|')[1].split(','):
            temp_array = tempStr.replace('\n', '').split(':', 1)
            setattr(base_model, temp_array[0].strip(), temp_array[1])

        if 'OnRspQryInstrument' in line:
            exchange_id = getattr(base_model, 'ExchangeID', '')
            product_id = getattr(base_model, 'ProductID', '')
            instrument_array.append(base_model)
        elif 'OnRspQryDepthMarketData' in line:
            market_array.append(base_model)

    field_list = [
        'VolumeMultiple', 'MaxMarketOrderVolume', 'MinMarketOrderVolume', 'MaxLimitOrderVolume',
        'MinLimitOrderVolume', 'LongMarginRatio', 'ShortMarginRatio'
    ]

    # platform_logger.debug('update_instrument_info, update record num: %d; fields: %s' %
    #                       (len(instrument_array), field_list))
    print ('update_instrument_info, update record num: %d; fields: %s') % (len(instrument_array), field_list)
    update_instrument_info(instrument_array)

    # platform_logger.debug('update market_info, update record num: %d' % (len(market_array)))
    print ('update market_info, update record num: %d') % len(market_array)
    update_market_info(market_array)  # 根据md行情数据更新prev_close


def update_instrument_info(message_array):

    for message_info in message_array:
        ticker = getattr(message_info, 'InstrumentID', '')
        exchange_name = getattr(message_info, 'ExchangeID', '')
        if 'SSE' == exchange_name:
            exchange_id = 18
        elif 'SZE' == exchange_name:
            exchange_id = 19
        elif 'SHFE' == exchange_name:
            exchange_id = 20
        elif 'DCE' == exchange_name:
            exchange_id = 21
        elif 'CZCE' == exchange_name:
            exchange_id = 22
        elif 'CFFEX' == exchange_name:
            exchange_id = 25
        else:
            continue

        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key not in instrument_db_dict:
            # print 'error instrument_info key:', dict_key
            continue

        instrument_db = instrument_db_dict[dict_key]
        instrument_db.fut_val_pt = getattr(message_info, 'VolumeMultiple', '')
        instrument_db.max_market_order_vol = getattr(message_info, 'MaxMarketOrderVolume', '')
        instrument_db.min_market_order_vol = getattr(message_info, 'MinMarketOrderVolume', '')
        instrument_db.max_limit_order_vol = getattr(message_info, 'MaxLimitOrderVolume', '')
        instrument_db.min_limit_order_vol = getattr(message_info, 'MinLimitOrderVolume', '')

        instrument_db.longmarginratio = float(getattr(message_info, 'LongMarginRatio', 0))
        if instrument_db.longmarginratio > 10000:
            instrument_db.longmarginratio = 0
        instrument_db.shortmarginratio = float(getattr(message_info, 'ShortMarginRatio', 0))
        if instrument_db.shortmarginratio > 10000:
            instrument_db.shortmarginratio = 0
        instrument_db.longmarginratio_speculation = instrument_db.longmarginratio
        instrument_db.shortmarginratio_speculation = instrument_db.shortmarginratio
        instrument_db.longmarginratio_hedge = instrument_db.longmarginratio
        instrument_db.shortmarginratio_hedge = instrument_db.shortmarginratio
        instrument_db.longmarginratio_arbitrage = instrument_db.longmarginratio
        instrument_db.shortmarginratio_arbitrage = instrument_db.shortmarginratio


def update_market_info(message_array):
    now_time = long(now.strftime('%H%M%S'))
    # after_trade_time = (now_time > 150500) and (now_time < 180000)
    after_trade_time = False

    if after_trade_time:
        fields = ['ClosePrice', 'Volume']
        # platform_logger.debug('update %s' % fields)
        print ('update %s') % fields
    else:
        fields = ['PreClosePrice', 'PreSettlementPrice', 'UpperLimitPrice', 'LowerLimitPrice']
        # platform_logger.debug('update %s' % fields)
        print ('update %s') % fields

    for message_info in message_array:
        ticker = getattr(message_info, 'InstrumentID', '')
        exchange_name = getattr(message_info, 'ExchangeID', '')
        if 'SSE' == exchange_name:
            exchange_id = 18
        elif 'SZE' == exchange_name:
            exchange_id = 19
        elif 'SHFE' == exchange_name:
            exchange_id = 20
        elif 'DCE' == exchange_name:
            exchange_id = 21
        elif 'CZCE' == exchange_name:
            exchange_id = 22
        elif 'CFFEX' == exchange_name:
            exchange_id = 25
        else:
            # print 'error exchange_name:', exchange_name
            continue

        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key not in instrument_db_dict:
            # print 'error market_info key:', dict_key
            continue

        instrument_db = instrument_db_dict[dict_key]

        if after_trade_time:
            instrument_db.close = getattr(message_info, 'ClosePrice', '')
            instrument_db.volume = getattr(message_info, 'Volume', '')
            instrument_db.close_update_time = datetime.now()
        else:
            instrument_db.prev_close = getattr(message_info, 'PreClosePrice', '')
            instrument_db.prev_settlementprice = getattr(message_info, 'PreSettlementPrice', '')
            instrument_db.uplimit = getattr(message_info, 'UpperLimitPrice', '')
            instrument_db.downlimit = getattr(message_info, 'LowerLimitPrice', '')
            instrument_db.prev_close_update_time = datetime.now()

            if instrument_db.undl_tickers == 'cu':
                if now.strftime('%Y-%m') == instrument_db.expire_date.strftime('%Y-%m'):
                    instrument_db.round_lot_size = 5
        instrument_db.update_date = datetime.now()


def set_main_submain():
    if (validate_time < 150500) or (validate_time > 180000):
        return
    future_undl_tickers_dict = dict()
    for (dict_key, future_db) in instrument_db_dict.items():
        if future_db.exchange_id not in (20, 21, 22):
            continue

        # 判断主次合约前先都置空
        future_db.tranche = None
        if future_db.volume is None:
            future_db.volume = 0

        if future_db.undl_tickers in future_undl_tickers_dict:
            future_undl_tickers_dict[future_db.undl_tickers].append(future_db)
        else:
            future_list = [future_db]
            future_undl_tickers_dict[future_db.undl_tickers] = future_list

    for (dict_key, future_list) in future_undl_tickers_dict.items():
        future_list = sorted(future_list, cmp=lambda x, y: cmp(int(x.volume), int(y.volume)), reverse=True)
        if len(future_list) > 1:
            if int(future_list[0].volume) > 0:
                future_list[0].tranche = 'Main'
            if int(future_list[1].volume) > 0:
                future_list[1].tranche = 'Sub'


def update_db():
    for (dict_key, future) in instrument_db_dict.items():
        session.merge(future)



def ctp_price_analysis(date):

    # platform_logger.info(get_log_format_string('Enter ctp_price_analysis', tag='='))
    print ('Enter ctp_price_analysis')
    host_server_model = ServerConstant().get_server_model('host')
    global session
    global filter_date_str

    date_ = '-'.join([date[:4], date[4:6], date[6:8]])
    session = host_server_model.get_db_session('common')
    if date is None or date == '':
        filter_date_str = now.strftime('%Y-%m-%d')
    else:
        filter_date_str = date_


    data_path = os.path.join(file_path, date)
    instrument_file_list = FileUtils(data_path).filter_file('CTP_INSTRUMENT', filter_date_str)
    print instrument_file_list
    market_file_list = FileUtils(data_path).filter_file('CTP_MARKET',
                                                         filter_date_str)
    ctp_file_list = []
    ctp_file_list.extend(instrument_file_list)
    ctp_file_list.extend(market_file_list)
    # platform_logger.info('src_file_path: %s' % data_path)
    print ('src_file_path: %s')% data_path
    # platform_logger.info('target_file_list: %s')% ctp_file_list
    print ('target_file_list: %s') % ctp_file_list

    for ctp_file in ctp_file_list:
        # platform_logger.info(get_log_format_string('start: %s' % ctp_file, tag='-'))
        print ('start: %s')% ctp_file
        read_price_file_ctp(os.path.join(data_path, ctp_file))

    set_main_submain()
    update_db()
    session.commit()
    # platform_logger.info(get_log_format_string('Exit ctp_price_analysis', tag='='))
    print ('Exit ctp_price_analysis')

if __name__ == '__main__':
    options = parse_arguments()
    date_str = options.date
    day = '20180713'
    ctp_price_analysis(day)

