# -*- coding: utf-8 -*-
import os
import codecs
import json
from model.eod_parse_arguments import parse_arguments
from datetime import datetime
from model.BaseModel import *
from model.server_constans import ServerConstant
from tools.getConfig import getConfig
from tools.file_utils import FileUtils
from model.instrument import Instrument
from tools.time_unit import CalendarUtil
from public.main_config import platform_logger, get_log_format_string


calendar = CalendarUtil()
today = calendar.get_today()
pre_trade_day = calendar.get_last_trade_day(today)
now = datetime.now()
file_path = getConfig()['datafetcher_file_path']
instrument_exchange_db_dict = dict()
fund_db_dict = dict()
pre_structured_fund_dict = dict()
pre_index_db_dict = dict()


def build_instrument_db_dict():
    query = session.query(Instrument)
    for instrument_db in query.filter(Instrument.exchange_id.in_((18, 19))):
        if instrument_db.type_id == 6:
            dict_key = '%s|%s' % (instrument_db.ticker_exch_real, instrument_db.exchange_id)
        else:
            dict_key = '%s|%s' % (instrument_db.ticker, instrument_db.exchange_id)
        instrument_exchange_db_dict[dict_key] = instrument_db

        if instrument_db.type_id in (7, 15, 16):
            fund_db_dict[instrument_db.ticker] = instrument_db
        elif instrument_db.type_id == 6:
            pre_index_db_dict[instrument_db.ticker] = instrument_db

        if instrument_db.type_id == 16:
            pre_structured_fund_dict[instrument_db.ticker] = instrument_db


def read_position_file_lts(lts_file_path):
    fr = codecs.open(lts_file_path, 'r', 'gbk')
    sf_instrument_array = []
    of_instrument_array = []
    instrument_array = []
    market_array = []
    index_array = []
    for line in fr.xreadlines():
        base_model = BaseModel()
        for temp_str in line.split('|')[1].split(','):
            temp_array = temp_str.replace('\n', '').split(':', 1)
            setattr(base_model, temp_array[0].strip(), temp_array[1])
        if 'OnRspQrySFInstrument' in line:
            sf_instrument_array.append(base_model)
        if 'OnRspQryOFInstrument' in line:
            of_instrument_array.append(base_model)
        elif 'OnRspQryInstrument' in line:
            instrument_array.append(base_model)
        elif 'OnRtnDepthMarketData' in line:
            market_array.append(base_model)
        elif 'OnRtnL2Index' in line:
            index_array.append(base_model)

    print('update_fund, sf_instrument record num: %d')% len(sf_instrument_array)
    print('update_fund,of_instrument record num: %d') % len(of_instrument_array)
    # platform_logger.info('update_fund, update sf_instrument record num: %d' % len(sf_instrument_array))
    # platform_logger.info('update_fund, update of_instrument record num: %d' % len(of_instrument_array))
    update_fund(sf_instrument_array, of_instrument_array)  # 更新分级基金的prev_nav

    # platform_logger.info('update_instrument_base_info, update record num: %d' % len(instrument_array))
    print('update_instrument_base_info, update record num: %d')% len(instrument_array)
    update_instrument_base_info(instrument_array)

    # different time, different function
    # platform_logger.info('update_market, update record num: %d' % len(market_array))
    print('update_market, update record num: %d') % len(market_array)
    update_market(market_array)  # 根据md行情数据更新prev_close


    # platform_logger.info('update_market_index, update record num: %d' % len(index_array))
    print('update_market_index, update record num: %d')% len(index_array)
    update_market_index(index_array)  # 根据md的L2行情数据更新指数的prev_close



# 更新分级基金pcf中PREDAYRATIO属性值
def update_structured_fund():
    now_time = long(now.strftime('%H%M%S'))
    # if now_time > 150500:
    #     return
    for (ticker, pre_structured_fund) in pre_structured_fund_dict.items():
        # 筛选出分级基金母基金
        # print ticker
        if pre_structured_fund.tranche is not None:
            continue
        (sub_ticker1, sub_ticker2) = pre_structured_fund.undl_tickers.split(';')
        sub_structured_fund = pre_structured_fund_dict[sub_ticker1]
        if sub_structured_fund.undl_tickers is None or sub_structured_fund.undl_tickers == '':
            # platform_logger.debug('sub structured fund:%s not point to index' % (sub_ticker1,))
            print('Debug: sub structured fund:%s not point to index') % \
                 sub_ticker1
            continue

        if sub_structured_fund.undl_tickers not in pre_index_db_dict:
            # platform_logger.debug('unfind index,ticker:%s' % (sub_structured_fund.undl_tickers,))
            print('Debug: unfind index,ticker:%s') % sub_structured_fund
        pre_index_db = pre_index_db_dict[sub_structured_fund.undl_tickers]
        dict_key = '%s|%s' % (pre_index_db.ticker_exch_real, pre_index_db.exchange_id)
        index_db = instrument_exchange_db_dict[dict_key]
        dict_key = '%s|%s' % (pre_structured_fund.ticker, pre_structured_fund.exchange_id)
        structured_fund = instrument_exchange_db_dict[dict_key]

        if index_db.prev_close == pre_index_db.prev_close:
            preday_ratio = 0
        else:
            preday_ratio = ((structured_fund.prev_nav - pre_structured_fund.prev_nav) * index_db.prev_close) \
                           / ((index_db.prev_close - pre_index_db.prev_close) * structured_fund.prev_nav)
            preday_ratio = '%.6f' % preday_ratio

        for structured_fund_ticker in [pre_structured_fund.ticker, sub_ticker1, sub_ticker2]:
            structured_fund_temp = pre_structured_fund_dict[structured_fund_ticker]
            dict_key = '%s|%s' % (structured_fund_temp.ticker, structured_fund_temp.exchange_id)
            structured_fund_db = instrument_exchange_db_dict[dict_key]
            structured_fund_pcf = json.loads(structured_fund_db.pcf)
            structured_fund_pcf['TradingDay'] = today
            structured_fund_pcf['PreTradingDay'] = pre_trade_day
            # print structured_fund_pcf
            structured_fund_pcf['PREDAYRATIO'] = preday_ratio
            structured_fund_db.pcf = json.dumps(structured_fund_pcf)


def update_fund(sf_instrument_array, of_instrument_array):
    instrument_cr_dict = dict()
    for messageInfo in of_instrument_array:

        instrument_id = getattr(messageInfo, 'InstrumentID', '')
        # print instrument_id
        creation_redemption = getattr(messageInfo, 'Creationredemption', '')
        instrument_cr_dict[instrument_id] = creation_redemption

    for messageInfo in sf_instrument_array:
        instrument_id = getattr(messageInfo, 'InstrumentID', '')
        if instrument_id not in fund_db_dict:
            continue
        fund_db = fund_db_dict[instrument_id]
        if fund_db.tranche is None:
            # 只更新母基金的prev_nav
            fund_db.prev_nav = getattr(messageInfo, 'NetPrice', '')

        pcf_dict = dict()
        pcf_dict['Ticker'] = instrument_id
        split_merge_status = getattr(messageInfo, 'SplitMergeStatus', '')
        if split_merge_status == '0':
            pcf_dict['Split'] = '1'
            pcf_dict['Merge'] = '1'
        elif split_merge_status == '1':
            pcf_dict['Split'] = '1'
            pcf_dict['Merge'] = '0'
        elif split_merge_status == '2':
            pcf_dict['Split'] = '0'
            pcf_dict['Merge'] = '1'
        else:
            pcf_dict['Split'] = '0'
            pcf_dict['Merge'] = '0'
        sf_instrument_id = getattr(messageInfo, 'SFInstrumentID', '')
        pcf_dict['SFInstrumentID'] = sf_instrument_id
        min_split_volume = getattr(messageInfo, 'MinSplitVolume', '')
        pcf_dict['MinSplitVolume'] = min_split_volume
        min_merge_volume = getattr(messageInfo, 'MinMergeVolume', '')
        pcf_dict['MinMergeVolume'] = min_merge_volume
        volume_ratio = getattr(messageInfo, 'VolumeRatio', '')
        pcf_dict['VolumeRatio'] = volume_ratio
        pcf_dict['TradingDay'] = now.strftime('%Y%m%d')

        if instrument_id in instrument_cr_dict:
            creation_redemption = instrument_cr_dict[instrument_id]
            if creation_redemption == '0':
                pcf_dict['Creation'] = '0'
                pcf_dict['Redemption'] = '0'
            elif creation_redemption == '1':
                pcf_dict['Creation'] = '1'
                pcf_dict['Redemption'] = '1'
            elif creation_redemption == '2':
                pcf_dict['Creation'] = '1'
                pcf_dict['Redemption'] = '0'
            elif creation_redemption == '3':
                pcf_dict['Creation'] = '0'
                pcf_dict['Redemption'] = '1'
        fund_db.pcf = json.dumps(pcf_dict)


def update_instrument_base_info(message_array):
    for messageInfo in message_array:
        ticker = getattr(messageInfo, 'InstrumentID', '')
        exchange_name = getattr(messageInfo, 'ExchangeID', '')
        if exchange_name == 'SSE':
            exchange_id = 18
        elif exchange_name == 'SZE':
            exchange_id = 19

        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key not in instrument_exchange_db_dict:
            continue

        instrument_db = instrument_exchange_db_dict[dict_key]
        instrument_db.fut_val_pt = getattr(messageInfo, 'VolumeMultiple', '')
        instrument_db.max_market_order_vol = getattr(messageInfo, 'MaxMarketOrderVolume', '')
        instrument_db.min_market_order_vol = getattr(messageInfo, 'MinMarketOrderVolume', '')
        instrument_db.max_limit_order_vol = getattr(messageInfo, 'MaxLimitOrderVolume', '')
        instrument_db.min_limit_order_vol = getattr(messageInfo, 'MinLimitOrderVolume', '')
        instrument_db.strike = getattr(messageInfo, 'ExecPrice', '')
        # print '***%s is' % instrument_db.fut_val_pt
        # 判断股票是否停牌
        if instrument_db.type_id != 4:
            continue
        is_trading = getattr(messageInfo, 'IsTrading', '')
        if is_trading == '1':
            instrument_db.inactive_date = None
        elif instrument_db.inactive_date is None:
            instrument_db.inactive_date = filter_date_str


def update_market(message_array):

    after_trade_time = False

    for messageInfo in message_array:
        ticker = getattr(messageInfo, 'InstrumentID', '')
        exchange_name = getattr(messageInfo, 'ExchangeID', '')
        if exchange_name == 'SSE':
            exchange_id = 18
        elif exchange_name == 'SZE':
            exchange_id = 19
        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key not in instrument_exchange_db_dict:
            print ('Error: instrument_info key: %s') %dict_key
            # rst = 'error instrument_info key: %s' %dict_key
            # platform_logger.error(rst)
            continue

        instrument_db = instrument_exchange_db_dict[dict_key]
        if after_trade_time:
            instrument_db.prev_close = getattr(messageInfo, 'PreClosePrice', '')
            instrument_db.prev_settlementprice = getattr(messageInfo, 'PreSettlementPrice', '')
            instrument_db.uplimit = getattr(messageInfo, 'UpperLimitPrice', '')
            instrument_db.downlimit = getattr(messageInfo, 'LowerLimitPrice', '')
            instrument_db.prev_close_update_time = datetime.now()
        else:
            instrument_db.close = getattr(messageInfo, 'ClosePrice', '')
            instrument_db.volume = getattr(messageInfo, 'Volume', '')
            instrument_db.close_update_time = datetime.now()
        # print 'pre_price is %s' % instrument_db.prev_close
        instrument_db.update_date = datetime.now()


def update_market_index(message_array):

    after_trade_time = False

    for messageInfo in message_array:
        ticker = getattr(messageInfo, 'InstrumentID', '')
        exchange_name = getattr(messageInfo, 'ExchangeID', '')
        if exchange_name == 'SSE':
            exchange_id = 18
        elif exchange_name == 'SZE':
            exchange_id = 19

        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key not in instrument_exchange_db_dict:
            print ('Error: index_info key: %s') % dict_key
            # rst = 'error index_info key: %s' % dict_key
            # platform_logger.error(rst)
            continue

        index_db = instrument_exchange_db_dict[dict_key]

        if after_trade_time:
            index_db.prev_close = getattr(messageInfo, 'PreClosePrice', '')
            index_db.prev_close_update_time = datetime.now()
        else:
            index_db.close = getattr(messageInfo, 'ClosePrice', '')
            index_db.volume = getattr(messageInfo, 'Volume', '')
            index_db.close_update_time = datetime.now()
        index_db.update_date = datetime.now()
        # print index_db

def update_db():
    for (dict_key, future) in instrument_exchange_db_dict.items():
        session.merge(future)

    # now_time = long(now.strftime('%H%M%S'))
    # 000974,000823的prev_close早上行情中为0，用昨日close赋值。
    # if now_time < 150500:
    update_sql = 'update common.instrument t set t.PREV_CLOSE = t.`CLOSE` where t.PREV_CLOSE = 0'
    session.execute(update_sql)


def lts_price_analysis(date):
    # platform_logger.info(get_log_format_string('Enter Lts_price_analysis'))
    print('Enter Lts_price_analysis')
    global session
    global filter_date_str
    date_ = '-'.join([date[:4], date[4:6], date[6:8]])

    host_server_model = ServerConstant().get_server_model('host')
    session = host_server_model.get_db_session('common')
    if date is None or date == '':
        filter_date_str = now.strftime('%Y-%m-%d')
    else:
        filter_date_str = date_

    build_instrument_db_dict()
    data_path = os.path.join(file_path, date)
    instrument_file_list = FileUtils(data_path).filter_file('HUABAO_INSTRUMENT', filter_date_str)
    market_file_list = FileUtils(data_path).filter_file('HUABAO_MARKET', filter_date_str)

    lts_file_list = []
    lts_file_list.extend(instrument_file_list)
    lts_file_list.extend(market_file_list)
    # platform_logger.info('taget_files: %s' % lts_file_list)
    print ('Info: taget_files: %s') % lts_file_list

    for qd_file in lts_file_list:
        # platform_logger.info(get_log_format_string('Start: %s' % qd_file))
        print ('Info: Start: %s') % qd_file
        read_position_file_lts(os.path.join(data_path, qd_file))

    # platform_logger.info('update_structured_fund')
    print ('Info: update_structured_fund')

    update_structured_fund()
    update_db()
    session.commit()
    # platform_logger.info(get_log_format_string('Exit Lts_price_analysis'))
    print('Info: Exit Lts_price_analysis')


if __name__ == '__main__':
    options = parse_arguments()
    date_str = options.date
    day = '20180713'
    lts_price_analysis(day)
    # lts_file_path = '/nas/data_share/price_files/20180521' \
    #                 '/HUABAO_INSTRUMENT_4_2018-05-21.txt'
    # read_position_file_lts(lts_file_path)