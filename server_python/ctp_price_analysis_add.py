# -*- coding: utf-8 -*-
import os
from datetime import datetime
from model.BaseModel import *
from model.future_main_contract import FutureMainContract
from model.eod_parse_arguments import parse_arguments
from model.server_constans import ServerConstant
from tools.getConfig import getConfig
from model.instrument import Instrument
from tools.file_utils import FileUtils
from model.eod_const import const
# from public.main_config import platform_logger, get_log_format_string

now = datetime.now()
server_constant = ServerConstant()

file_path = getConfig()['datafetcher_file_path']

session = None
future_db_dict = dict()
option_db_dict = dict()
instrument_history_db_dict = dict()
future_insert_list = []
instrument_history_list = []
option_insert_list = []


def read_price_file_ctp(ctp_file_path):
    fr = open(ctp_file_path)
    future_list = []
    option_list = []
    for line in fr.readlines():
        base_model = BaseModel()
        if len(line.strip()) == 0:
            continue
        for tempStr in line.split('|')[1].split(','):
            temp_array = tempStr.replace('\n', '').split(':', 1)
            setattr(base_model, temp_array[0].strip(), temp_array[1])

        if 'OnRspQryInstrument' in line:
            product_class = getattr(base_model, 'ProductClass', '')
            if product_class == '1':
                future_list.append(base_model)
            if product_class == '2':
                option_list.append(base_model)

    # platform_logger.info('pre_add_future, add record num: %d' % len(future_list))
    print('pre_add_future, add record num: %d') % len(future_list)
    pre_add_future(future_list)  # 新增期货

    # platform_logger.info('pre_add_option, add record num: %d' % len(option_list))
    print ('pre_add_option, add record num: %d') % len(option_list)
    pre_add_option(option_list)  # 新增期权


def pre_add_future(message_array):
    global max_instrument_id
    for message_info in message_array:
        ticker = getattr(message_info, 'InstrumentID', '')
        exchange_name = getattr(message_info, 'ExchangeID', '')
        if 'CFFEX' == exchange_name:
            exchange_id = 25
        elif 'SHFE' == exchange_name:
            exchange_id = 20
        elif 'DCE' == exchange_name:
            exchange_id = 21
        elif 'CZCE' == exchange_name:
            exchange_id = 22
        else:
            continue
        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key in future_db_dict:
            continue

        future_db = Instrument()
        max_instrument_id += 1
        future_db.id = max_instrument_id
        future_db.ticker = ticker
        future_db.exchange_id = exchange_id
        future_db.fut_val_pt = getattr(message_info, 'VolumeMultiple', '')
        future_db.max_market_order_vol = getattr(message_info, 'MaxMarketOrderVolume', '')
        future_db.min_market_order_vol = getattr(message_info, 'MinMarketOrderVolume', '')
        future_db.max_limit_order_vol = getattr(message_info, 'MaxLimitOrderVolume', '')
        future_db.min_limit_order_vol = getattr(message_info, 'MinLimitOrderVolume', '')
        future_db.longmarginratio = getattr(message_info, 'LongMarginRatio', '')
        future_db.shortmarginratio = getattr(message_info, 'ShortMarginRatio', '')
        future_db.longmarginratio_speculation = future_db.longmarginratio
        future_db.shortmarginratio_speculation = future_db.shortmarginratio
        future_db.longmarginratio_hedge = future_db.longmarginratio
        future_db.shortmarginratio_hedge = future_db.shortmarginratio
        future_db.longmarginratio_arbitrage = future_db.longmarginratio
        future_db.shortmarginratio_arbitrage = future_db.shortmarginratio

        future_db.create_date = getattr(message_info, 'CreateDate', '')
        future_db.expire_date = getattr(message_info, 'ExpireDate', '')

        future_db.ticker_exch = ticker
        future_db.ticker_exch_real = ticker
        future_db.type_id = 1  # future
        future_db.market_status_id = 2
        future_db.multiplier = 1
        future_db.crncy = 'CNY'
        future_db.effective_since = getattr(message_info, 'OpenDate', '')

        product_id = getattr(message_info, 'ProductID', '')
        name_message = getattr(message_info, 'InstrumentName', '')
        price_tick = getattr(message_info, 'PriceTick', '')

        if (product_id == 'TF') or (product_id == 'T'):
            future_db.market_sector_id = 5
            future_db.round_lot_size = 1
            future_db.tick_size_table = '0:%f' % (float(price_tick),)
            future_db.undl_tickers = product_id
            future_db.name = ticker
        elif (product_id == 'IC') or (product_id == 'IF') or (product_id == 'IH'):
            future_db.market_sector_id = 6
            future_db.round_lot_size = 1
            future_db.tick_size_table = '0:%f' % (float(price_tick),)

            future_db.longmarginratio_hedge = 0.2
            future_db.shortmarginratio_hedge = 0.2

            undl_ticker = ''
            if product_id == 'IF':
                undl_ticker = 'SHSZ300'
            elif product_id == 'IC':
                undl_ticker = 'SH000905'
            elif product_id == 'IH':
                undl_ticker = 'SSE50'
            future_db.undl_tickers = undl_ticker

            future_db.name = name_message.replace('中证', 'cs').replace('上证', 'SSE').replace('股指', 'IDX') \
                .replace('期货', 'Future').replace('国债', 'TF').replace('指数', 'Index').strip()
        else:
            future_db.market_sector_id = 1
            future_db.round_lot_size = 1
            future_db.tick_size_table = '0:%f' % (float(price_tick),)
            if product_id == 'cu':
                expire_date = getattr(message_info, 'ExpireDate', '')
                if now.strftime('%Y-%m') == expire_date[:7]:
                    future_db.round_lot_size = 5
            future_db.undl_tickers = product_id
            future_db.name = ticker

        future_db.is_settle_instantly = 1
        future_db.is_purchase_to_redemption_instantly = 0
        future_db.is_buy_to_redpur_instantly = 0
        future_db.is_redpur_to_sell_instantly = 0

        ticker_type = filter(lambda x: not x.isdigit(), ticker)
        future_db.session = __get_trading_info_list(ticker_type)[-1]
        future_insert_list.append(future_db)
        # platform_logger.info('prepare insert future:', ticker)
        print ('prepare insert future: %s') % ticker


def __get_track_undl_tickers(ticker_type):
    query = session.query(FutureMainContract)
    future_maincontract_db = query.filter(FutureMainContract.ticker_type == ticker_type).first()
    return future_maincontract_db.main_symbol


def __get_trading_info_list(ticker_type):
    start_date = None
    end_date = None
    trading_info_list = []
    last_trading_time = None

    query_sql = "select * from basic_info.trading_info t where t.symbol = '%s' order by date" % ticker_type
    for trading_info in session_basicinfo.execute(query_sql):
        if start_date is None:
            start_date = trading_info[1]

        if str(trading_info[1]) in const.HOLIDAYS:
            continue

        if last_trading_time is None:
            last_trading_time = trading_info[2]

        if trading_info[2] != last_trading_time:
            trading_info_list.append('(%s,%s)%s' % (start_date, end_date, last_trading_time))
            start_date = trading_info[1]

        end_date = trading_info[1]
        last_trading_time = trading_info[2]
    end_date = '20991231'
    trading_info_list.append('(%s,%s)%s' % (start_date, end_date, last_trading_time))
    return trading_info_list


def pre_add_option(message_array):
    global max_instrument_id
    for messageInfo in message_array:
        ticker = getattr(messageInfo, 'InstrumentID', '')
        exchange_name = getattr(messageInfo, 'ExchangeID', '')
        if 'CFFEX' == exchange_name:
            exchange_id = 25
        elif 'SHFE' == exchange_name:
            exchange_id = 20
        elif 'DCE' == exchange_name:
            exchange_id = 21
        elif 'CZCE' == exchange_name:
            exchange_id = 22
        else:
            continue

        if ticker in option_db_dict:
            continue

        option_db = Instrument()
        max_instrument_id += 1
        option_db.id = max_instrument_id
        option_db.ticker = ticker
        option_db.exchange_id = exchange_id
        option_db.fut_val_pt = getattr(messageInfo, 'VolumeMultiple', '')
        option_db.max_market_order_vol = getattr(messageInfo, 'MaxMarketOrderVolume', '')
        option_db.min_market_order_vol = getattr(messageInfo, 'MinMarketOrderVolume', '')
        option_db.max_limit_order_vol = getattr(messageInfo, 'MaxLimitOrderVolume', '')
        option_db.min_limit_order_vol = getattr(messageInfo, 'MinLimitOrderVolume', '')

        undl_tickers = getattr(messageInfo, 'UnderlyingInstrID', '')
        option_db.undl_tickers = undl_tickers

        option_db.create_date = getattr(messageInfo, 'CreateDate', '')
        option_db.expire_date = getattr(messageInfo, 'ExpireDate', '')

        instrument_name = getattr(messageInfo, 'InstrumentName', '').strip()
        instrument_name = instrument_name.replace('买权', 'Call').replace('卖权', 'Put').replace('白糖', 'SR')

        option_db.name = ticker

        put_call = __get_put_call(instrument_name)
        option_db.put_call = put_call

        if put_call == 0:
            option_db.strike = ticker.replace('-', '').split('P')[-1]
        else:
            option_db.strike = ticker.replace('-', '').split('C')[-1]

        price_tick = getattr(messageInfo, 'PriceTick', '')
        option_db.tick_size_table = '0:%s' % (float(price_tick),)

        option_db.ticker_exch = ticker
        option_db.ticker_exch_real = ticker
        option_db.market_status_id = 2
        option_db.type_id = 10  # option
        option_db.market_sector_id = 1
        option_db.round_lot_size = 1
        option_db.longmarginratio = 0
        option_db.shortmarginratio = 0.15
        option_db.longmarginratio_speculation = option_db.longmarginratio
        option_db.shortmarginratio_speculation = option_db.shortmarginratio
        option_db.longmarginratio_hedge = option_db.longmarginratio
        option_db.shortmarginratio_hedge = option_db.shortmarginratio
        option_db.longmarginratio_arbitrage = option_db.longmarginratio
        option_db.shortmarginratio_arbitrage = option_db.shortmarginratio
        option_db.multiplier = 10
        option_db.crncy = 'CNY'

        option_db.effective_since = filter_date_str
        option_db.is_settle_instantly = 1
        option_db.is_purchase_to_redemption_instantly = 0
        option_db.is_buy_to_redpur_instantly = 0
        option_db.is_redpur_to_sell_instantly = 0
        option_db.option_margin_factor1 = 0.5
        option_db.option_margin_factor2 = 0.5

        ticker_type = filter(lambda x: not x.isdigit(), undl_tickers)
        option_db.session = __get_trading_info_list(ticker_type)[-1]
        option_db.track_undl_tickers = __get_track_undl_tickers(ticker_type)
        option_insert_list.append(option_db)
        print 'prepare insert option:', ticker


def insert_server_db():
    if len(future_insert_list) == 0 and len(option_insert_list) == 0:
        return

    for server_model in server_constant.get_all_server():
        server_session = server_model.get_db_session('common')
        for future_db in future_insert_list:
            server_session.add(future_db.copy())

        for option_db in option_insert_list:
            server_session.add(option_db.copy())
        server_session.commit()

    # # 只更新本地的instrument_histroy表
    # for instrument_history_db in instrument_history_list:
    #     session.add(instrument_history_db.copy())
    session.commit()


def build_future_db_dict():
    query = session.query(Instrument)
    for future_db in query.filter(Instrument.exchange_id.in_((20, 21, 22, 25))):
        dict_key = '%s|%s' % (future_db.ticker, future_db.exchange_id)
        future_db_dict[dict_key] = future_db

    for option_db in query.filter(Instrument.type_id == 10):
        option_db_dict[option_db.ticker] = option_db


def __get_put_call(line_str):
    if 'P' in line_str:
        return 0
    elif 'C' in line_str:
        return 1
    else:
        print 'unfind:', line_str
        return 0


def get_instrument_max_id():
    global max_instrument_id
    max_instrument_id = session.execute('select max(id) from common.instrument').first()[0]


def ctp_price_analysis_add(date):
    # platform_logger.info(get_log_format_string('Enter ctp_price_analysis_add'))
    print ('Enter ctp_price_analysis_add')
    host_server_model = server_constant.get_server_model('host')
    global session
    global session_basicinfo
    global filter_date_str
    date_ = '-'.join([date[:4], date[4:6], date[6:8]])
    session = host_server_model.get_db_session('common')
    session_basicinfo = host_server_model.get_db_session('basic_info')
    if date is None or date == '':
        filter_date_str = now.strftime('%Y-%m-%d')
    else:
        filter_date_str = date_
    data_path = os.path.join(file_path, date)
    # print data_path
    # print filter_date_str
    instrument_file_list = FileUtils(data_path).filter_file('CTP_INSTRUMENT', filter_date_str)

    build_future_db_dict()
    get_instrument_max_id()
    # platform_logger.info('target_files: %s' % instrument_file_list)
    print ('target_files: %s') % instrument_file_list
    for ctp_file in instrument_file_list:
        # platform_logger.info(get_log_format_string('Start: %s' % ctp_file))
        print ('Start: %s') % ctp_file
        read_price_file_ctp(os.path.join(data_path, ctp_file))
    session.commit()

    insert_server_db()
    # platform_logger.info(get_log_format_string('Exit ctp_price_analysis_add'))
    print ('Exit ctp_price_analysis_add')


if __name__ == '__main__':
    options = parse_arguments()
    date_str = options.date
    day = '20180521'
    ctp_price_analysis_add(day)
