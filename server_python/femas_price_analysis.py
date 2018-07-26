# -*- coding: utf-8 -*-
from datetime import datetime
from model.BaseModel import *
from model.server_constans import ServerConstant
from tools.getConfig import getConfig
from model.instrument import Instrument
from tools.file_utils import FileUtils

now = datetime.now()
today_str = now.strftime('%Y-%m-%d')
validate_time = long(now.strftime('%H%M%S'))

file_path = getConfig()['datafetcher_file_path']
session = None
future_db_dict = dict()


def read_price_file_femas(femas_file_path):
    print 'Start read file:', femas_file_path
    fr = open(femas_file_path)
    option_array = []
    future_array = []
    instrument_cff_array = []
    market_array = []
    for line in fr.readlines():
        base_model = BaseModel()
        for tempStr in line.split('|')[1].split(','):
            temp_array = tempStr.replace('\n', '').split(':', 1)
            setattr(base_model, temp_array[0].strip(), temp_array[1])
        if 'OnRspQryInstrument' in line:
            product_id = getattr(base_model, 'ProductID', '')
            options_type = getattr(base_model, 'OptionsType', '')
            if (product_id == 'IC') or (product_id == 'IF') or (product_id == 'IH') or (product_id == 'TF') or \
                    (product_id == 'T'):
                future_array.append(base_model)
                instrument_cff_array.append(base_model)
            elif (options_type == '1') or (options_type == '2'):
                option_array.append(base_model)
                instrument_cff_array.append(option_array)
        elif 'OnRtnDepthMarketData' in line:
            market_array.append(base_model)

    update_instrument_cff(future_array)
    update_market_data(market_array)


def update_market_data(message_array):
    for messageInfo in message_array:
        ticker = getattr(messageInfo, 'InstrumentID', '')
        exchange_id = 25
        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key not in future_db_dict:
            print 'error future_info key:', dict_key
            continue

        future_db = future_db_dict[dict_key]
        now_time = long(now.strftime('%H%M%S'))
        if now_time < 150500:
            future_db.prev_close = getattr(messageInfo, 'PreClosePrice', '')
            future_db.prev_close_update_time = datetime.now()
        else:
            future_db.close = getattr(messageInfo, 'ClosePrice', '')
            future_db.volume = getattr(messageInfo, 'Volume', '')
            future_db.close_update_time = datetime.now()
        future_db.update_date = datetime.now()


def update_instrument_cff(message_array):
    for messageInfo in message_array:
        ticker = getattr(messageInfo, 'InstrumentID', '')
        exchange_name = getattr(messageInfo, 'ExchangeID', '')
        if exchange_name == 'CFFEX':
            exchange_id = 25
        dict_key = '%s|%s' % (ticker, exchange_id)
        if dict_key not in future_db_dict:
            print 'error future_info key:', dict_key
            continue

        future_db = future_db_dict[dict_key]
        future_db.fut_val_pt = getattr(messageInfo, 'VolumeMultiple', '')
        future_db.max_market_order_vol = getattr(messageInfo, 'MaxMarketOrderVolume', '')
        future_db.min_market_order_vol = getattr(messageInfo, 'MinMarketOrderVolume', '')
        future_db.max_limit_order_vol = getattr(messageInfo, 'MaxLimitOrderVolume', '')
        future_db.min_limit_order_vol = getattr(messageInfo, 'MinLimitOrderVolume', '')
        # productID = getattr(messageInfo, 'ProductID', '')


def update_db():
    for (dict_key, future) in future_db_dict.items():
        session.merge(future)


def build_future_db_dict():
    query = session.query(Instrument)
    for future in query.filter(Instrument.exchange_id == 25):
        dict_key = '%s|%s' % (future.ticker, future.exchange_id)
        future_db_dict[dict_key] = future


if __name__ == '__main__':
    print 'Enter femas_price_analysis.'
    host_server_model = ServerConstant().get_server_model('host')
    session = host_server_model.get_db_session('common')
    build_future_db_dict()
    femas_td_file_list = FileUtils(file_path).filter_file('Femas_TD', today_str)
    for femas_td_file in femas_td_file_list:
        read_price_file_femas('%s/%s' % (file_path, femas_td_file))

    # femas_md_file_list = FileUtils(file_path).filter_file('Femas_MD', today_str)
    # for femas_md_file in femas_md_file_list:
    #     read_price_file_femas('%s/%s' % (file_path, femas_md_file))
    update_db()
    session.commit()
    print 'Exit femas_price_analysis.'
