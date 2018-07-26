# -*- coding: utf-8 -*-
# 对各数据库新增期权和股票数据
import os
import sys
import codecs
from datetime import datetime

from model.BaseModel import *
from model.server_constans import ServerConstant
from tools.getConfig import getConfig
from model.instrument import Instrument
from tools.file_utils import FileUtils
from model.eod_parse_arguments import parse_arguments
from public.main_config import platform_logger, get_log_format_string
reload(sys)
sys.setdefaultencoding('utf8')

now = datetime.now()
server_constant = ServerConstant()

file_path = getConfig()['datafetcher_file_path']
session = None
instrument_db_dict = dict()
instrument_insert_list = []
undl_ticker_dict = dict()
structured_fund_dict = dict()


def read_position_file_lts(lts_file_path):
    fr = codecs.open(lts_file_path, 'r', 'gbk')
    sf_instrument_array = []
    option_array = []
    stock_array = []
    structured_fund_array = []
    # 货币基金
    mmf_fund_array = []
    for line in fr.xreadlines():
        base_model = BaseModel()
        for tempStr in line.split('|')[1].split(','):
            temp_array = tempStr.replace('\n', '').split(':', 1)
            setattr(base_model, temp_array[0].strip(), temp_array[1])
        if 'OnRspQryInstrument' in line:
            product_id = getattr(base_model, 'ProductID', '')
            # productClass = getattr(baseModel, 'ProductClass', '')
            if (product_id == 'SHEOP') or (product_id == 'SHAOP'):
                option_array.append(base_model)
            elif (product_id == 'SZA') or (product_id == 'SHA') or (product_id == 'HKA') or (product_id == 'CY') :
                stock_array.append(base_model)
            elif (product_id == 'SZOF') or (product_id == 'SHOF'):
                structured_fund_array.append(base_model)
            elif product_id == 'SHFUNDETF':
                mmf_fund_array.append(base_model)
        elif 'OnRspQrySFInstrument' in line:
            sf_instrument_array.append(base_model)

    # print structured_fund_array
    structured_fund_undl_ticker(sf_instrument_array)
    add_structured_fund(structured_fund_array)

    platform_logger.info('add_option, update record num: %d' % len(option_array))
    # print '--**--'
    add_option(option_array)  # 新增期权
    # print '**--**'

    platform_logger.info('add_stock, update record num: %d' % len(stock_array))
    add_stock(stock_array)  # 更新股票停牌日期数据和新增股票

    platform_logger.info('add_mmf_fund, update record num: %d' % len(mmf_fund_array))
    add_mmf_fund(mmf_fund_array)  # 新增货币基金


def add_mmf_fund(message_array):
    global max_instrument_id
    for messageInfo in message_array:
        # print "good"
        ticker = getattr(messageInfo, 'InstrumentID', '')
        exchange_name = getattr(messageInfo, 'ExchangeID', '')
        if exchange_name == 'SSE':
            exchange_id = 18
        elif exchange_name == 'SZE':
            exchange_id = 19

        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key in instrument_db_dict:
            continue

        mmf_fund_db = Instrument()
        max_instrument_id += 1
        mmf_fund_db.id = max_instrument_id
        mmf_fund_db.ticker = ticker
        mmf_fund_db.exchange_id = exchange_id
        mmf_fund_db.name = ''

        mmf_fund_db.fut_val_pt = getattr(messageInfo, 'VolumeMultiple', '')
        mmf_fund_db.multiplier = mmf_fund_db.fut_val_pt
        mmf_fund_db.max_market_order_vol = getattr(messageInfo, 'MaxMarketOrderVolume', '')
        mmf_fund_db.min_market_order_vol = getattr(messageInfo, 'MinMarketOrderVolume', '')
        mmf_fund_db.max_limit_order_vol = getattr(messageInfo, 'MaxLimitOrderVolume', '')
        mmf_fund_db.min_limit_order_vol = getattr(messageInfo, 'MinLimitOrderVolume', '')

        mmf_fund_db.ticker_exch = ticker
        mmf_fund_db.ticker_exch_real = ticker
        mmf_fund_db.market_status_id = 2
        mmf_fund_db.type_id = 15
        mmf_fund_db.market_sector_id = 4
        mmf_fund_db.round_lot_size = 100
        # price_tick = getattr(messageInfo, 'PriceTick', '')
        mmf_fund_db.tick_size_table = '0:0.001'
        mmf_fund_db.crncy = 'CNY'
        mmf_fund_db.longmarginratio = 0
        mmf_fund_db.shortmarginratio = 999
        mmf_fund_db.longmarginratio_speculation = mmf_fund_db.longmarginratio
        mmf_fund_db.shortmarginratio_speculation = mmf_fund_db.shortmarginratio
        mmf_fund_db.longmarginratio_hedge = mmf_fund_db.longmarginratio
        mmf_fund_db.shortmarginratio_hedge = mmf_fund_db.shortmarginratio
        mmf_fund_db.longmarginratio_arbitrage = mmf_fund_db.longmarginratio
        mmf_fund_db.shortmarginratio_arbitrage = mmf_fund_db.shortmarginratio

        if exchange_name == 'SSE':
            mmf_fund_db.is_settle_instantly = 1
            mmf_fund_db.is_purchase_to_redemption_instantly = 0
            mmf_fund_db.is_buy_to_redpur_instantly = 0
            mmf_fund_db.is_redpur_to_sell_instantly = 0
        elif exchange_name == 'SZE':
            mmf_fund_db.is_settle_instantly = 1
            mmf_fund_db.is_purchase_to_redemption_instantly = 1
            mmf_fund_db.is_buy_to_redpur_instantly = 1
            mmf_fund_db.is_redpur_to_sell_instantly = 1

        instrument_insert_list.append(mmf_fund_db)
        # print instrument_insert_list
        print 'prepare insert etf:', ticker


def structured_fund_undl_ticker(sf_instrument_array):
    for messageInfo in sf_instrument_array:
        ticker = getattr(messageInfo, 'InstrumentID', '')
        undl_ticker = getattr(messageInfo, 'SFInstrumentID', '')
        structured_fund_dict[ticker] = ''
        structured_fund_dict[undl_ticker] = ''

        if ticker == undl_ticker:
            continue
        if undl_ticker in undl_ticker_dict:
            undl_ticker_dict[undl_ticker].append(ticker)
        else:
            ticker_list = [ticker]
            undl_ticker_dict[undl_ticker] = ticker_list


def add_structured_fund(message_array):
    global max_instrument_id
    for messageInfo in message_array:
        ticker = getattr(messageInfo, 'InstrumentID', '')

        if ticker not in structured_fund_dict:
            continue
        # print ticker
        exchange_name = getattr(messageInfo, 'ExchangeID', '')

        if exchange_name == 'SSE':
            exchange_id = 18
        elif exchange_name == 'SZE':
            exchange_id = 19
        else:
            print '-------------------', exchange_id
        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key in instrument_db_dict:
            continue

        structured_fund_db = Instrument()
        max_instrument_id += 1
        structured_fund_db.id = max_instrument_id
        structured_fund_db.ticker = ticker
        structured_fund_db.exchange_id = exchange_id
        structured_fund_db.name = ''

        undl_ticker_str = ''
        if ticker in undl_ticker_dict:
            undl_ticker_list = undl_ticker_dict[ticker]
            undl_ticker_str = ';'.join(undl_ticker_list)
        structured_fund_db.undl_tickers = undl_ticker_str

        if exchange_id == 18:
            structured_fund_db.is_settle_instantly = 0
            structured_fund_db.is_purchase_to_redemption_instantly = 0
            structured_fund_db.is_buy_to_redpur_instantly = 1
            structured_fund_db.is_redpur_to_sell_instantly = 1
        elif exchange_id == 19:
            structured_fund_db.is_settle_instantly = 0
            structured_fund_db.is_purchase_to_redemption_instantly = 0
            structured_fund_db.is_buy_to_redpur_instantly = 0
            structured_fund_db.is_redpur_to_sell_instantly = 0

        structured_fund_db.ticker_exch = ticker
        structured_fund_db.ticker_exch_real = ticker
        structured_fund_db.market_sector_id = 4
        structured_fund_db.type_id = 16
        structured_fund_db.crncy = 'CNY'
        structured_fund_db.round_lot_size = 100
        structured_fund_db.tick_size_table = '0:0.001'
        structured_fund_db.market_status_id = 2
        structured_fund_db.fut_val_pt = 1
        structured_fund_db.max_limit_order_vol = 1000000
        structured_fund_db.min_limit_order_vol = 100
        structured_fund_db.max_market_order_vol = 0
        structured_fund_db.min_market_order_vol = 0
        structured_fund_db.longmarginratio = 0
        structured_fund_db.shortmarginratio = 999
        structured_fund_db.longmarginratio_speculation = structured_fund_db.longmarginratio
        structured_fund_db.shortmarginratio_speculation = structured_fund_db.shortmarginratio
        structured_fund_db.longmarginratio_hedge = structured_fund_db.longmarginratio
        structured_fund_db.shortmarginratio_hedge = structured_fund_db.shortmarginratio
        structured_fund_db.longmarginratio_arbitrage = structured_fund_db.longmarginratio
        structured_fund_db.shortmarginratio_arbitrage = structured_fund_db.shortmarginratio
        structured_fund_db.multiplier = 1
        instrument_insert_list.append(structured_fund_db)
        print 'prepare insert structured fund:', ticker


def add_option(message_array):
    global max_instrument_id
    for messageInfo in message_array:
        ticker = getattr(messageInfo, 'InstrumentID', '')
        exchange_name = getattr(messageInfo, 'ExchangeID', '')
        if exchange_name == 'SSE':
            exchange_id = 18
        elif exchange_name == 'SZE':
            exchange_id = 19

        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key in instrument_db_dict:
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
        option_db.strike = getattr(messageInfo, 'ExecPrice', '')


        exchange_inst_id = getattr(messageInfo, 'ExchangeInstID', '')
        undl_tickers = exchange_inst_id[0:6]
        option_db.undl_tickers = undl_tickers
        option_db.track_undl_tickers = undl_tickers
        if 'M' in exchange_inst_id:
            option_db.contract_adjustment = 0
        elif 'A' in exchange_inst_id:
            option_db.contract_adjustment = 1
        elif 'B' in exchange_inst_id:
            option_db.contract_adjustment = 2
        elif 'C' in exchange_inst_id:
            option_db.contract_adjustment = 3

        option_db.create_date = getattr(messageInfo, 'CreateDate', '')
        option_db.expire_date = getattr(messageInfo, 'ExpireDate', '')

        instrument_name = getattr(messageInfo, 'InstrumentName', '').strip()
        instrument_name = instrument_name.replace('购', 'Call').replace('沽', 'Put').replace('月', 'month') \
            .replace('中国平安', undl_tickers).replace('上汽集团', undl_tickers)
        if 'Call' in instrument_name:
            put_call = 1
        else:
            put_call = 0
        option_db.name = instrument_name
        option_db.put_call = put_call

        price_tick = getattr(messageInfo, 'PriceTick', '')
        option_db.tick_size_table = '0:%s' % (float(price_tick),)

        option_db.ticker_exch = ticker
        option_db.ticker_exch_real = ticker
        option_db.market_status_id = 2
        option_db.type_id = 10  # option
        option_db.market_sector_id = 4
        option_db.round_lot_size = 1
        option_db.longmarginratio = 0
        option_db.shortmarginratio = 0.15
        option_db.longmarginratio_speculation = option_db.longmarginratio
        option_db.shortmarginratio_speculation = option_db.shortmarginratio
        option_db.longmarginratio_hedge = option_db.longmarginratio
        option_db.shortmarginratio_hedge = option_db.shortmarginratio
        option_db.longmarginratio_arbitrage = option_db.longmarginratio
        option_db.shortmarginratio_arbitrage = option_db.shortmarginratio
        option_db.multiplier = 10000
        option_db.crncy = 'CNY'
        option_db.effective_since = filter_date_str
        option_db.is_settle_instantly = 1
        option_db.is_purchase_to_redemption_instantly = 0
        option_db.is_buy_to_redpur_instantly = 0
        option_db.is_redpur_to_sell_instantly = 0
        option_db.option_margin_factor1 = 0.15
        option_db.option_margin_factor2 = 0.07
        instrument_insert_list.append(option_db)
        # print instrument_insert_list
        print 'prepare insert option:', ticker


def add_stock(message_array):
    # print 'hello'
    # print message_array
    global max_instrument_id
    for messageInfo in message_array:
        ticker = getattr(messageInfo, 'InstrumentID', '')
        # print ticker
        exchange_name = getattr(messageInfo, 'ExchangeID', '')
        if exchange_name == 'SSE':
            exchange_id = 18
        elif exchange_name == 'SZE':
            exchange_id = 19
        elif exchange_name == 'HGE':
            exchange_id = 13
        dict_key = '%s|%s' % (ticker, exchange_id)
        # # print instrument_db_dict
        if dict_key in instrument_db_dict:
            continue
        # instrument_name = getattr(messageInfo, 'InstrumentName', '')

        # print "bye"
        stock_db = Instrument()
        max_instrument_id += 1
        stock_db.id = max_instrument_id
        stock_db.ticker = ticker
        stock_db.exchange_id = exchange_id
        stock_db.name = ''

        stock_db.ticker_exch = ticker
        stock_db.ticker_exch_real = ticker
        stock_db.market_status_id = 2
        stock_db.market_sector_id = 4
        stock_db.type_id = 4
        stock_db.crncy = 'CNY'
        stock_db.round_lot_size = 100
        stock_db.tick_size_table = '0:0.01'
        stock_db.fut_val_pt = 1
        stock_db.max_market_order_vol = 0
        stock_db.min_market_order_vol = 0
        stock_db.max_limit_order_vol = 1000000
        stock_db.min_limit_order_vol = 100
        stock_db.longmarginratio = 0
        stock_db.shortmarginratio = 999
        stock_db.longmarginratio_speculation = stock_db.longmarginratio
        stock_db.shortmarginratio_speculation = stock_db.shortmarginratio
        stock_db.longmarginratio_hedge = stock_db.longmarginratio
        stock_db.shortmarginratio_hedge = stock_db.shortmarginratio
        stock_db.longmarginratio_arbitrage = stock_db.longmarginratio
        stock_db.shortmarginratio_arbitrage = stock_db.shortmarginratio
        stock_db.multiplier = 1
        stock_db.strike = 0
        stock_db.is_settle_instantly = 0
        stock_db.is_purchase_to_redemption_instantly = 0
        stock_db.is_buy_to_redpur_instantly = 1
        stock_db.is_redpur_to_sell_instantly = 1
        # print 'hi'
        instrument_insert_list.append(stock_db)
        print 'prepare insert stock:', ticker


def build_instrument_db_dict():
    # host_server_model = server_constant.get_server_model('host')
    # session = host_server_model.get_db_session('common')
    query = session.query(Instrument)

    for future in query.filter(Instrument.exchange_id.in_((18, 19, 13))):
        dict_key = '%s|%s' % (future.ticker, future.exchange_id)
        instrument_db_dict[dict_key] = future
    # print 'HELLO , %s is ' % instrument_db_dict


def get_instrument_max_id():
    global max_instrument_id
    max_instrument_id = session.execute('select max(id) from common.instrument').first()[0]
    # print max_instrument_id

def insert_server_db():
    if len(instrument_insert_list) == 0:
        # print '***'
        return

    for server_model in server_constant.get_all_server():
        server_session = server_model.get_db_session('common')
        for instrument_db in instrument_insert_list:
            server_session.add(instrument_db.copy())
        server_session.commit()
        # print instrument_insert_list


def lts_price_analysis_add(date):
    platform_logger.info(get_log_format_string('Enter Lts_price_analysis_add'))
    global session
    global filter_date_str

    date_ = '-'.join([date[:4], date[4:6], date[6:8]])
    host_server_model = server_constant.get_server_model('host')
    session = host_server_model.get_db_session('common')
    if date is None or date == '':
        filter_date_str = now.strftime('%Y-%m-%d')
    else:
        filter_date_str = date_

    build_instrument_db_dict()
    get_instrument_max_id()
    data_path = os.path.join(file_path, date)

    instrument_file_list = FileUtils(data_path).filter_file('HUABAO_INSTRUMENT', filter_date_str)

    platform_logger.info('target_files: %s' % instrument_file_list)
    for qd_file in instrument_file_list:
        platform_logger.info(get_log_format_string('Start: %s' % qd_file, '-'))
        read_position_file_lts(os.path.join(data_path, qd_file))
    session.commit()
    insert_server_db()

    platform_logger.info(get_log_format_string('Exit Lts_price_analysis_add'))


if __name__ == '__main__':
    options = parse_arguments()
    date_str = options.date
    if date_str is not None and date_str != '':
        day = date_str
    else:
        day = datetime.now().strftime('%Y%m%d')

    day = '20180521'
    lts_price_analysis_add(day)