# coding: utf-8
import os
import pandas as pd
from realaccount import RealAccount
from pf_account import PfAccount
from phone_trade_info import PhoneTradeInfo

from flask import render_template, request, current_app, flash, redirect, url_for, jsonify, make_response
from . import report
import json
from flask_login import login_required
from server_risk import ServerRisk
from server_constans import ServerConstant
from eod_const import const, CustomEnumUtils


SEARCH_ATTRS = {'attr_names': ['server_name',],
                'server_name': ['all','huabao','guoxin', 'nanhua','zhongxin','luzheng']}
server_constant = ServerConstant()
date_utils = DateUtils()

custom_enum_utils = CustomEnumUtils()
order_type_inversion_dict = custom_enum_utils.enum_to_dict(const.ORDER_TYPE_ENUMS, True)
hedgeflag_type_inversion_dict = custom_enum_utils.enum_to_dict(const.HEDGEFLAG_TYPE_ENUMS, True)
order_status_inversion_dict = custom_enum_utils.enum_to_dict(const.ORDER_STATUS_ENUMS, True)
operation_status_inversion_dict = custom_enum_utils.enum_to_dict(const.OPERATION_STATUS_ENUMS, True)
trade_type_inversion_dict = custom_enum_utils.enum_to_dict(const.TRADE_TYPE_ENUMS, True)
algo_status_inversion_dict = custom_enum_utils.enum_to_dict(const.ALGO_STATUS_ENUMS, True)

instrument_type_inversion_dict = custom_enum_utils.enum_to_dict(const.INSTRUMENT_TYPE_ENUMS, True)
market_status_inversion_dict = custom_enum_utils.enum_to_dict(const.MARKET_STATUS_ENUMS, True)
exchange_type_inversion_dict = custom_enum_utils.enum_to_dict(const.EXCHANGE_TYPE_ENUMS, True)

direction_dict = custom_enum_utils.enum_to_dict(const.DIRECTION_ENUMS)
trade_type_dict = custom_enum_utils.enum_to_dict(const.TRADE_TYPE_ENUMS)
io_type_dict = custom_enum_utils.enum_to_dict(const.IO_TYPE_ENUMS)


@report.route('/report_risks', methods=['GET', 'POST'])
@login_required
def report_risks():
    return render_template('report/report_risks.html', search_attrs=SEARCH_ATTRS, risk_list=[])


@report.route('/report_risks_func', methods=['GET', 'POST'])
@login_required
def report_risks_func():
    config = json.loads(request.form.get('config'))

    query_risk_list = []
    server_model = server_constant.get_server_model('host')
    session_history = server_model.get_db_session('history')
    for server_risk_db in session_history.query(ServerRisk).filter(ServerRisk.date.between(config['start_day'], config['end_day']),
                                                                    ServerRisk.server_name == config['server_name']):
        query_risk_list.append(server_risk_db)
    return json.dumps(query_risk_list)


@report.route('/info', methods=['GET'])
def basic_info():
    basic_item = {
        'general': 'test_value',
        'cpu': 'cpu'
    }

    from eod_aps.tools.redis_aggregator_manager_tools import loader_market_from_redis
    loader_market_from_redis()
    return make_response(jsonify(code=200, data=basic_item), 200)


@report.route('/market_list', methods=['GET', 'POST'])
def query_market_list():
    query_params = request.json
    query_instrument_type = query_params.get('instrument_type')
    query_exchange = query_params.get('exchange')
    query_ticker = query_params.get('ticker')

    query_result_list = []
    instrument_msg_dict = const.EOD_POOL['instrument_dict']
    for (market_id, market_msg) in const.EOD_POOL['market_dict'].items():
        market_item_dict = dict()
        instrument_msg = instrument_msg_dict[market_id]

        if query_ticker and query_ticker not in instrument_msg.ticker:
            continue
        if query_instrument_type and query_instrument_type != instrument_type_inversion_dict[instrument_msg.TypeIDWire]:
            continue
        if query_exchange and query_exchange != exchange_type_inversion_dict[instrument_msg.ExchangeIDWire]:
            continue

        market_item_dict['Symbol'] = instrument_msg.ticker
        market_item_dict['Bid1'] = market_msg.Args.Bid1
        market_item_dict['Bid1Size'] = market_msg.Args.Bid1Size
        market_item_dict['Ask1'] = market_msg.Args.Ask1
        market_item_dict['Ask1Size'] = market_msg.Args.Ask1Size
        market_item_dict['YdVolume'] = market_msg.Args.VolumeTdy
        market_item_dict['Volume'] = market_msg.Args.Volume
        market_item_dict['UpdateTime'] = GetDateTime(market_msg.Args.UpdateTime).strftime('%H:%M:%S')
        market_item_dict['PrevClose'] = instrument_msg.prevCloseWired
        market_item_dict['LastPrice'] = market_msg.Args.LastPrice
        market_item_dict['NominalPrice'] = market_msg.Args.NominalPrice
        market_item_dict['Status'] = market_status_inversion_dict[instrument_msg.marketStatusWired]

        if float(instrument_msg.prevCloseWired) == 0:
            chg_value = 0
        else:
            chg_value = '%.2f%%' % ((market_msg.Args.NominalPrice / instrument_msg.prevCloseWired - 1) * 100)
        market_item_dict['Chg'] = chg_value
        market_item_dict['BidAbnormal'] = market_msg.Args.BidAbnormal
        market_item_dict['AskAbnormal'] = market_msg.Args.AskAbnormal
        query_result_list.append(market_item_dict)

    sort_prop = query_params.get('sort_prop')
    sort_order = query_params.get('sort_order')
    if sort_prop:
        if sort_order == 'ascending':
            query_result_list = sorted(query_result_list, key=lambda market_item: market_item[sort_prop], reverse=True)
        else:
            query_result_list = sorted(query_result_list, key=lambda market_item: market_item[sort_prop])
    else:
        query_result_list.sort(key=lambda obj: obj['Symbol'])

    query_page = int(query_params.get('page'))
    query_size = int(query_params.get('size'))
    total_number = len(query_result_list)
    query_result = {'data': query_result_list[(query_page - 1) * query_size: query_page * query_size],
                    'total': total_number
                    }
    return make_response(jsonify(code=200, data=query_result), 200)


@report.route('/order_list', methods=['GET', 'POST'])
def query_order_list():
    query_params = request.json
    query_server_name = query_params.get('server_name')
    query_fund_name = query_params.get('fund_name')
    query_strategy = query_params.get('strategy')
    query_ticker = query_params.get('ticker')
    query_order_id = query_params.get('order_id')
    query_order_status = query_params.get('order_status')

    query_result_list = []
    for (order_id, order_msg) in const.EOD_POOL['order_dict'].items():
        if query_fund_name and query_fund_name not in order_msg.Order.OrderAccount:
            continue
        if query_strategy and query_strategy not in order_msg.Order.StrategyID:
            continue
        if query_ticker and query_ticker not in order_msg.Symbol:
            continue

        server_name = __get_server_name(order_msg.Location)
        if query_server_name and query_server_name != server_name:
            continue

        if query_order_id and query_order_id not in order_msg.Order.ID:
            continue

        order_status = order_status_inversion_dict[order_msg.Order.StatusWire]
        if query_order_status and query_order_status != order_status:
            continue

        order_item_dict = dict()
        order_item_dict['Type'] = order_type_inversion_dict[order_msg.Order.TypeWire]
        order_item_dict['Strategy'] = order_msg.Order.StrategyID
        order_item_dict['Symbol'] = order_msg.Symbol
        order_item_dict['HedgeType'] = hedgeflag_type_inversion_dict[order_msg.Order.HedgeTypeWire]
        order_item_dict['Status'] = order_status
        order_item_dict['OpStatus'] = operation_status_inversion_dict[order_msg.Order.OperationStatusWire]
        order_item_dict['AlgoStatus'] = algo_status_inversion_dict[order_msg.Order.AlgoStatus]
        order_item_dict['Price'] =  order_msg.Order.Price
        order_item_dict['OrdVol'] = order_msg.Order.Qty
        order_item_dict['TradeVol'] = '%.f' % (order_msg.Order.ExQty / order_msg.Order.Qty * 100)
        order_item_dict['ExPrice'] =  order_msg.Order.ExAvgPrice
        # order_item_dict['CxlVol'] =
        order_item_dict['CreationT'] = GetDateTime(order_msg.Order.CreationTime).strftime('%H:%M:%S.%f')[:12]
        order_item_dict['TransactionT'] = GetDateTime(order_msg.Order.TransactionTime).strftime('%H:%M:%S.%f')[:12]
        order_item_dict['Note'] = order_msg.Order.Note
        # order_item_dict['Undl'] =
        # order_item_dict['C/P'] =
        # order_item_dict['Expire'] =
        # order_item_dict['Strike'] =
        order_item_dict['Account'] = order_msg.Order.OrderAccount
        order_item_dict['OrderID'] = order_msg.Order.ID
        order_item_dict['SysOrderID'] = order_msg.Order.SysID
        order_item_dict['TradeType'] = trade_type_inversion_dict[order_msg.Order.TradeTypeWire]
        order_item_dict['NominalTradeType'] = trade_type_inversion_dict[order_msg.Order.NominalTradeTypeWire]
        order_item_dict['ParentOrderID'] = order_msg.Order.ParentOrderID
        order_item_dict['Server'] = server_name
        query_result_list.append(order_item_dict)
    query_page = int(query_params.get('page'))
    query_size = int(query_params.get('size'))
    total_number = len(query_result_list)

    query_result_list.sort(key=lambda obj: obj['TransactionT'], reverse=True)
    query_result = {'data': query_result_list[(query_page - 1) * query_size: query_page * query_size],
                    'total': total_number
                    }
    return make_response(jsonify(code=200, data=query_result), 200)


@report.route('/trade_list', methods=['GET', 'POST'])
def query_trade_list():
    query_params = request.json
    query_server_name = query_params.get('server_name')
    query_fund_name = query_params.get('fund_name')
    query_strategy = query_params.get('strategy')
    query_ticker = query_params.get('ticker')

    query_result_list = []
    # instrument_msg_dict = const.EOD_POOL['instrument_dict']
    for (trade_time, trade_msg) in const.EOD_POOL['trade_list']:
        if query_fund_name and query_fund_name not in trade_msg.Trade.AccountID:
            continue
        if query_strategy and query_strategy not in trade_msg.Trade.StrategyID:
            continue
        if query_ticker and query_ticker not in trade_msg.Trade.symbol:
            continue

        server_name = __get_server_name(trade_msg.Location)
        if query_server_name and query_server_name != server_name:
            continue

        trade_item_dict = dict()
        trade_item_dict['Time'] = trade_time
        trade_item_dict['Symbol'] = trade_msg.Trade.symbol
        trade_item_dict['Qty'] = trade_msg.Trade.Qty
        trade_item_dict['Price'] = trade_msg.Trade.Price
        trade_item_dict['Type'] = trade_msg.Trade.TradeTypeWired
        trade_item_dict['TradePL'] = trade_msg.Trade.TradePL.PL
        trade_item_dict['Fee'] = trade_msg.Trade.TradeFee
        # trade_item_dict['FairTradePL'] = trade_msg
        # trade_item_dict['NetTradePL'] = trade_msg
        # trade_item_dict['Delta'] = trade_msg
        # trade_item_dict['Gamma'] = trade_msg
        # trade_item_dict['Vega'] = trade_msg
        # trade_item_dict['Theta'] = trade_msg
        # trade_item_dict['Undl'] = trade_msg
        # trade_item_dict['C/P'] = trade_msg
        #
        # trade_item_dict['Expire'] = trade_msg
        # trade_item_dict['Strike'] = trade_msg
        trade_item_dict['OrderID'] = trade_msg.Trade.OrderID
        trade_item_dict['Strategy'] = trade_msg.Trade.StrategyID
        trade_item_dict['Account'] = trade_msg.Trade.AccountID
        trade_item_dict['NominalTradeType'] = trade_msg.Trade.NominalTradeTypeWired
        trade_item_dict['TradeID'] = trade_msg.Trade.TradeID
        trade_item_dict['SelfCross'] = trade_msg.Trade.SelfCross
        trade_item_dict['Note'] = trade_msg.Trade.Note
        trade_item_dict['Server'] = server_name
        query_result_list.append(trade_item_dict)
    query_page = int(query_params.get('page'))
    query_size = int(query_params.get('size'))
    total_number = len(query_result_list)

    query_result_list.sort(key=lambda obj: obj['Time'], reverse=True)
    query_result = {'data': query_result_list[(query_page - 1) * query_size: query_page * query_size],
                    'total': total_number
                    }
    return make_response(jsonify(code=200, data=query_result), 200)


def __get_server_name(server_ip_str):
    server_name_result = ''
    for (server_name, server_model) in const.SERVER_DICT.items():
        if server_model.ip in server_ip_str:
            server_name_result = server_name
    return server_name_result


@report.route('/query_pf_position', methods=['GET', 'POST'])
def query_pf_position():
    query_params = request.json
    query_server_name = query_params.get('server_name')
    query_fund_name = query_params.get('fund_name')
    query_strategy = query_params.get('strategy')
    query_ticker = query_params.get('ticker')

    query_result_list = []
    instrument_msg_dict = const.EOD_POOL['instrument_dict']
    market_msg_dict = const.EOD_POOL['market_dict']

    sum_trading_pl = 0.0
    sum_position_pl = 0.0
    for (strategy_name, strategy_risk_dict) in const.EOD_POOL['risk_dict'].items():
        if query_server_name:
            server_model = server_constant.get_server_model(query_server_name)
            if server_model.ip not in strategy_name:
                continue
        if query_fund_name and query_fund_name not in strategy_name:
            continue
        if query_strategy and query_strategy not in strategy_name:
            continue

        for (instrument_key, position_msg) in strategy_risk_dict.items():
            if instrument_key not in instrument_msg_dict:
                print instrument_key
                continue

            instrument_msg = instrument_msg_dict[instrument_key]
            if query_ticker and query_ticker != instrument_msg.ticker:
                continue

            (base_strategy_name, server_ip_str) = strategy_name.split('@')
            market_msg = market_msg_dict[instrument_key]
            instrument_view = InstrumentView(instrument_msg, market_msg)
            risk_view = RiskView(instrument_view, position_msg, base_strategy_name)

            pf_position_item_dict = dict()
            pf_position_item_dict['Strategy'] = base_strategy_name
            pf_position_item_dict['Server'] = __get_server_name(server_ip_str)
            pf_position_item_dict['Ticker'] = instrument_msg.ticker
            pf_position_item_dict['HedgeFlag'] = position_msg.HedgeFlagWire
            pf_position_item_dict['YdLongRemain'] = position_msg.YdLongRemain
            pf_position_item_dict['PrevLong'] =  position_msg.PrevLong
            pf_position_item_dict['Long'] =  position_msg.Long
            pf_position_item_dict['LongCost'] =  position_msg.LongCost
            pf_position_item_dict['DayLong'] = position_msg.DayLong
            pf_position_item_dict['DayLongCost'] =  position_msg.DayLongCost
            pf_position_item_dict['PrevLongAvail'] =  position_msg.PrevLongAvailable
            pf_position_item_dict['LongAvail'] =  position_msg.LongAvailable
            pf_position_item_dict['YdShortRemain'] = position_msg.YdShortRemain
            pf_position_item_dict['PrevShort'] = position_msg.PrevShort
            pf_position_item_dict['Short'] = position_msg.Short
            pf_position_item_dict['ShortCost'] =  position_msg.ShortCost
            pf_position_item_dict['DayShort'] = position_msg.DayShort
            pf_position_item_dict['DayShortCost'] =  position_msg.DayShortCost
            # pf_position_item_dict['PrevShortAvail'] = position_msg.PrevShortAvailable
            pf_position_item_dict['ShortAvail'] =  position_msg.ShortAvailable

            pf_position_item_dict['TradingPL'] =  risk_view.trading_pl
            pf_position_item_dict['DayTradeFee'] =  position_msg.DayTradeFee
            pf_position_item_dict['PositionPL'] =  risk_view.position_pl
            pf_position_item_dict['TotalPL'] =  risk_view.total_pl
            query_result_list.append(pf_position_item_dict)

            sum_trading_pl += risk_view.trading_pl
            sum_position_pl += risk_view.position_pl

    sort_prop = query_params.get('sort_prop')
    sort_order = query_params.get('sort_order')
    if sort_prop:
        if sort_order == 'ascending':
            query_result_list = sorted(query_result_list, key=lambda pf_position_item: float(pf_position_item[sort_prop]), reverse=True)
        else:
            query_result_list = sorted(query_result_list, key=lambda pf_position_item: float(pf_position_item[sort_prop]))
    else:
        query_result_list.sort(key=lambda obj: obj['Strategy'] + obj['Server'], reverse=False)

    query_page = int(query_params.get('page'))
    query_size = int(query_params.get('size'))
    total_number = len(query_result_list)

    query_result = {'data': query_result_list[(query_page - 1) * query_size: query_page * query_size],
                    'total': total_number,
                    'sum_trading_pl':  sum_trading_pl,
                    'sum_position_pl':  sum_position_pl,
                    'sum_total_pl': sum_trading_pl + sum_position_pl
                    }
    return make_response(jsonify(code=200, data=query_result), 200)


@report.route('/query_real_position', methods=['GET', 'POST'])
def query_real_position():
    query_params = request.json
    query_server_name = query_params.get('server_name')
    query_fund_name = query_params.get('fund_name')
    query_ticker = query_params.get('ticker')

    query_result_list = []
    instrument_msg_dict = const.EOD_POOL['instrument_dict']
    market_msg_dict = const.EOD_POOL['market_dict']

    sum_trading_pl = 0.0
    sum_position_pl = 0.0
    for (account_name, account_position_dict) in const.EOD_POOL['position_dict'].items():
        if query_server_name:
            server_model = server_constant.get_server_model(query_server_name)
            if server_model.ip not in account_name:
                continue
        if query_fund_name and query_fund_name not in account_name:
            continue

        for (instrument_key, position_msg) in account_position_dict.items():
            if instrument_key not in instrument_msg_dict:
                print instrument_key
                continue

            instrument_msg = instrument_msg_dict[instrument_key]
            if query_ticker and query_ticker != instrument_msg.ticker:
                continue

            (base_account_name, server_ip_str) = account_name.split('@')
            market_msg = market_msg_dict[instrument_key]
            instrument_view = InstrumentView(instrument_msg, market_msg)
            risk_view = RiskView(instrument_view, position_msg, account_name)

            position_item_dict = dict()
            position_item_dict['Server'] = __get_server_name(server_ip_str)
            position_item_dict['Account'] = base_account_name
            position_item_dict['Ticker'] = instrument_msg.ticker
            position_item_dict['HedgeFlag'] = position_msg.HedgeFlagWire
            position_item_dict['YdLongRemain'] = position_msg.YdLongRemain
            position_item_dict['PrevLong'] =  position_msg.PrevLong
            position_item_dict['Long'] =  position_msg.Long
            position_item_dict['LongCost'] =  position_msg.LongCost
            position_item_dict['DayLong'] = position_msg.DayLong
            position_item_dict['DayLongCost'] =  position_msg.DayLongCost
            position_item_dict['PrevLongAvail'] =  position_msg.PrevLongAvailable
            position_item_dict['LongAvail'] =  position_msg.LongAvailable
            position_item_dict['YdShortRemain'] = position_msg.YdShortRemain
            position_item_dict['PrevShort'] = position_msg.PrevShort
            position_item_dict['Short'] = position_msg.Short
            position_item_dict['ShortCost'] =  position_msg.ShortCost
            position_item_dict['DayShort'] = position_msg.DayShort
            position_item_dict['DayShortCost'] =  position_msg.DayShortCost
            # pf_position_item_dict['PrevShortAvail'] = position_msg.PrevShortAvailable
            position_item_dict['ShortAvail'] =  position_msg.ShortAvailable

            position_item_dict['TradingPL'] =  risk_view.trading_pl
            position_item_dict['DayTradeFee'] =  position_msg.DayTradeFee
            position_item_dict['PositionPL'] =  risk_view.position_pl
            position_item_dict['TotalPL'] =  risk_view.total_pl
            query_result_list.append(position_item_dict)

            sum_trading_pl += risk_view.trading_pl
            sum_position_pl += risk_view.position_pl

    sort_prop = query_params.get('sort_prop')
    sort_order = query_params.get('sort_order')
    if sort_prop:
        if sort_order == 'ascending':
            query_result_list = sorted(query_result_list, key=lambda position_item: float(position_item[sort_prop]), reverse=True)
        else:
            query_result_list = sorted(query_result_list, key=lambda position_item: float(position_item[sort_prop]))
    else:
        query_result_list.sort(key=lambda obj: obj['Server'], reverse=False)

    query_page = int(query_params.get('page'))
    query_size = int(query_params.get('size'))
    total_number = len(query_result_list)
    query_result = {'data': query_result_list[(query_page - 1) * query_size: query_page * query_size],
                    'total': total_number,
                    'sum_trading_pl':  sum_trading_pl,
                    'sum_position_pl':  sum_position_pl,
                    'sum_total_pl': (sum_trading_pl + sum_position_pl)
                    }
    return make_response(jsonify(code=200, data=query_result), 200)


@report.route('/query_services', methods=['GET', 'POST'])
def query_services():
    params = request.json
    server_name = params.get('server_name')

    service_list = []
    server_model = server_constant.get_server_model('host')
    session_common = server_model.get_db_session('common')
    query_sql = "select app_name from common.server_info where server_name= '%s'" % server_name
    query_result = session_common.execute(query_sql)
    for result_item in query_result:
        server_item_dict = dict()
        server_item_dict['value'] = result_item[0]
        server_item_dict['label'] = result_item[0]
        service_list.append(server_item_dict)
    return make_response(jsonify(code=200, data=service_list), 200)


@report.route('/query_log_files', methods=['GET', 'POST'])
def query_log_files():
    params = request.json
    server_name = params.get('server_name')
    service_name = params.get('service_name')

    server_model = server_constant.get_server_model(server_name)
    cmd_list = ['cd %s' % server_model.server_path_dict['tradeplat_log_folder'],
                'ls *%s*.log' % service_name
                ]
    log_file_list = server_model.run_cmd_str2(';'.join(cmd_list))

    return_list = []
    for log_file_name in log_file_list:
        item_dict = dict()
        item_dict['value'] = log_file_name
        item_dict['label'] = log_file_name
        return_list.append(item_dict)
    return make_response(jsonify(code=200, data=return_list), 200)


@report.route('/query_ts_accounts', methods=['GET', 'POST'])
def query_ts_accounts():
    ts_account_list = []

    server_name = 'guoxin'
    server_model = server_constant.get_server_model(server_name)
    session_portfolio = server_model.get_db_session('portfolio')
    query = session_portfolio.query(RealAccount)
    for account_db in query.filter(RealAccount.accounttype == 'TS', RealAccount.enable == 1):
        item_dict = dict()
        account_name = '%s-%s-%s-' % (account_db.accountname, account_db.accounttype, account_db.fund_name)
        item_dict['value'] = account_name
        item_dict['label'] = account_name
        ts_account_list.append(item_dict)
    return make_response(jsonify(code=200, data=ts_account_list), 200)


@report.route('/query_fund_by_server', methods=['GET', 'POST'])
def query_fund_by_server():
    params = request.json
    server_name = params.get('servername')

    fund_list = []
    server_model = server_constant.get_server_model(server_name)
    session_portfolio = server_model.get_db_session('portfolio')
    query_account = session_portfolio.query(RealAccount)
    for result_item in query_account.group_by(RealAccount.fund_name):
        fund_item_dict = dict()
        fund_item_dict['value'] = result_item.fund_name
        fund_item_dict['label'] = result_item.fund_name
        fund_list.append(fund_item_dict)
    fund_list.sort()

    query_result = {'data': fund_list}
    return make_response(jsonify(code=200, data=query_result), 200)


@report.route('/query_strategy_by_fund', methods=['GET', 'POST'])
def query_strategy_by_fund():
    params = request.json
    server_name = params.get('servername')
    fund = params.get('fund')
    print server_name, fund

    strategy_list = []
    server_model = server_constant.get_server_model(server_name)
    session_portfolio = server_model.get_db_session('portfolio')
    query_pf_account = session_portfolio.query(PfAccount)
    for pf_account_db in query_pf_account.filter(PfAccount.fund_name.like('%' + fund + '%')):
        strategy_item_dict = dict()
        strategy_item_dict['value'] = '%s.%s' % (pf_account_db.group_name, pf_account_db.name)
        strategy_item_dict['label'] = '%s.%s' % (pf_account_db.group_name, pf_account_db.name)
        strategy_list.append(strategy_item_dict)
    strategy_list.sort()

    query_result = {'data': strategy_list}
    return make_response(jsonify(code=200, data=query_result), 200)


@report.route('/phone_trade_list', methods=['GET', 'POST'])
def save_phone_trade_list():
    params = request.json
    print params

    phone_trade_list = []
    for param_item in params:
        phone_trade_info = PhoneTradeInfo()
        phone_trade_info.server_name = param_item.get('servername')
        phone_trade_info.fund = param_item.get('fundname')
        phone_trade_info.strategy1 = param_item.get('strategy1')

        phone_trade_info.symbol = param_item.get('ticker')
        phone_trade_info.exqty = param_item.get('volume')
        phone_trade_info.exprice = param_item.get('price')

        phone_trade_info.direction = direction_dict[param_item.get('direction')]
        phone_trade_info.tradetype = trade_type_dict[param_item.get('tradetype')]

        phone_trade_info.hedgeflag = const.HEDGEFLAG_TYPE_ENUMS.Speculation
        phone_trade_info.strategy2 = param_item.get('strategy2')
        phone_trade_info.iotype = io_type_dict[param_item.get('iotype')]
        phone_trade_list.append(phone_trade_info)
    server_save_path = os.path.join(const.EOD_CONFIG_DICT['phone_trade_folder'], param_item.get('servername'))
    if not os.path.exists(server_save_path):
        os.mkdir(server_save_path)
    phone_trade_file_path = '%s/position_repair_%s.csv' % (server_save_path, date_utils.get_today_str('%Y%m%d'))
    # save_phone_trade_file(phone_trade_file_path, phone_trade_list)
    send_phone_trade(param_item.get('servername'), phone_trade_list)

    query_result = {'data': "success"}
    return make_response(jsonify(code=200, data=query_result), 200)


@report.route('/query_risk_history', methods=['GET', 'POST'])
def query_risk_history():
    query_params = request.json

    user_token = query_params.get('user_token')
    search_date_item = query_params.get('search_date')
    server_name = query_params.get('server_name')
    fund_name = query_params.get('fund_name')
    strategy_name = query_params.get('strategy_name')

    if search_date_item:
        [start_date, end_date] = search_date_item
        start_date = start_date[:10]
        end_date = end_date[:10]
    else:
        start_date = date_utils.get_today_str('%Y-%m-%d')
        end_date = start_date

    user_id = user_token.split('|')[0]
    query_sql = "select pf_account_list from jobs.user_list where user_id='%s'" % user_id
    server_model = server_constant.get_server_model('host')
    session_jobs = server_model.get_db_session('jobs')
    pf_account_list_str = session_jobs.execute(query_sql).first()[0]
    filter_pf_account_list = pf_account_list_str.split(',')

    server_risk_db_list = []
    server_host = server_constant.get_server_model('host')
    session_history = server_host.get_db_session('history')
    sum_total_pl = 0
    for server_risk_db in session_history.query(ServerRisk).filter(ServerRisk.date.between(start_date, end_date)):
        item_dict = dict()
        if server_name and server_name != server_risk_db.server_name:
            continue
        if fund_name and fund_name not in server_risk_db.strategy_name:
            continue
        if strategy_name and strategy_name not in server_risk_db.strategy_name:
            continue

        strategy_name_item = server_risk_db.strategy_name.split('-')
        if filter_pf_account_list and strategy_name_item[1] not in filter_pf_account_list:
            continue

        item_dict['server_name'] = server_risk_db.server_name
        item_dict['date'] = date_utils.datetime_toString(server_risk_db.date, '%Y-%m-%d')
        item_dict['strategy_name'] = server_risk_db.strategy_name
        item_dict['position_pl'] = server_risk_db.position_pl
        item_dict['trading_pl'] = server_risk_db.trading_pl
        item_dict['fee'] = server_risk_db.fee
        item_dict['stocks_pl'] = server_risk_db.stocks_pl
        item_dict['future_pl'] = server_risk_db.future_pl
        item_dict['total_pl'] = server_risk_db.total_pl
        item_dict['total_stocks_value'] = server_risk_db.total_stocks_value
        item_dict['total_future_value'] = server_risk_db.total_future_value
        server_risk_db_list.append(item_dict)
        sum_total_pl += float(server_risk_db.total_pl)

    sort_prop = query_params.get('sort_prop')
    sort_order = query_params.get('sort_order')
    if sort_prop:
        if sort_order == 'ascending':
            server_risk_db_list = sorted(server_risk_db_list,
                                         key=lambda server_risk: int(server_risk[sort_prop]),
                                         reverse=True)
        else:
            server_risk_db_list = sorted(server_risk_db_list, key=lambda server_risk: int(server_risk[sort_prop]))

    query_page = int(query_params.get('page'))
    query_size = int(query_params.get('size'))
    total_number = len(server_risk_db_list)
    result_list = server_risk_db_list[(query_page - 1) * query_size: query_page * query_size]
    query_result = {'data': result_list, 'total': total_number, 'sum_total_pl': sum_total_pl}
    return make_response(jsonify(code=200, data=query_result), 200)


@report.route('/export_risk_history', methods=['GET', 'POST'])
def export_risk_history():
    query_params = request.json
    user_token = query_params.get('user_token')
    search_date_item = query_params.get('search_date')
    server_name = query_params.get('server_name')
    fund_name = query_params.get('fund_name')
    strategy_name = query_params.get('strategy_name')

    if search_date_item:
        [start_date, end_date] = search_date_item
        start_date = date_utils.get_last_trading_day('%Y-%m-%d', start_date[:10])
        end_date = end_date[:10]
    else:
        start_date = date_utils.get_today_str('%Y-%m-%d')
        end_date = start_date

    user_id = user_token.split('|')[0]
    query_sql = "select pf_account_list from jobs.user_list where user_id='%s'" % user_id
    server_model = server_constant.get_server_model('host')
    session_jobs = server_model.get_db_session('jobs')
    pf_account_list_str = session_jobs.execute(query_sql).first()[0]
    filter_pf_account_list = pf_account_list_str.split(',')

    index_return_rate_list = []
    query_sql = "select date, RETURN_RATE from jobs.daily_return_history where ticker = 'SH000905' and date >= '%s' \
    and date <= '%s'" % (start_date, end_date)
    session_jobs = server_model.get_db_session('jobs')
    for query_result_item in session_jobs.execute(query_sql):
        date_str = date_utils.datetime_toString(query_result_item[0], '%Y-%m-%d')
        index_return_rate_list.append([date_str, query_result_item[1]])
    index_return_rate_df = pd.DataFrame(index_return_rate_list, columns=["Date", "Index_Rate"])

    server_risk_db_list = []
    server_host = server_constant.get_server_model('host')
    session_history = server_host.get_db_session('history')
    for server_risk_db in session_history.query(ServerRisk).filter(ServerRisk.date.between(start_date, end_date)):
        if server_name and server_name != server_risk_db.server_name:
            continue
        if fund_name and fund_name not in server_risk_db.strategy_name:
            continue
        if strategy_name and strategy_name not in server_risk_db.strategy_name:
            continue

        strategy_name_item = server_risk_db.strategy_name.split('-')
        if filter_pf_account_list and strategy_name_item[1] not in filter_pf_account_list:
            continue

        item_list = []
        item_list.append(date_utils.datetime_toString(server_risk_db.date, '%Y-%m-%d'))
        item_list.append(server_risk_db.total_stocks_value)
        item_list.append(abs(server_risk_db.total_future_value))
        item_list.append(server_risk_db.position_pl)
        item_list.append(server_risk_db.future_pl)
        item_list.append(server_risk_db.stocks_pl)
        item_list.append(server_risk_db.total_pl)
        server_risk_db_list.append(item_list)

    risk_view_df = pd.DataFrame(server_risk_db_list, columns=["Date", "Total_Stocks_Value", "Total_Future_Value",
                                                              "Position_PL", "Stocks_PL", "Future_PL", "Total_PL"])

    groupby_df1 = risk_view_df.groupby("Date").sum()[["Total_Stocks_Value", "Total_Future_Value", "Position_PL",
                                                      "Stocks_PL", "Future_PL", "Total_PL"]]
    groupby_df1['Date'] = groupby_df1.index.values
    groupby_df1.index = range(len(groupby_df1))
    groupby_df1 = pd.merge(groupby_df1, index_return_rate_df, on=['Date'], how='left')

    groupby_df1['Pre_Stocks_Value'] = groupby_df1.Total_Stocks_Value.shift(1)
    groupby_df1 = groupby_df1.sort_values('Date', ascending=True)
    groupby_df1 = groupby_df1.drop(0)

    groupby_df1['Alpha_Value'] = groupby_df1.Position_PL / groupby_df1.Pre_Stocks_Value - groupby_df1.Index_Rate
    groupby_df1['Net_Rate'] = groupby_df1.Total_PL / groupby_df1.Pre_Stocks_Value
    groupby_df1.index = groupby_df1.Date

    del groupby_df1['Position_PL']
    del groupby_df1['Total_Future_Value']
    groupby_df1 = groupby_df1.fillna(0)

    groupby_df1['Alpha_Value'] = groupby_df1['Alpha_Value'].apply(lambda x: '%.4f%%' % (x*100))
    groupby_df1['Net_Rate'] = groupby_df1['Net_Rate'].apply(lambda x: '%.4f%%' % (x*100))
    groupby_df1['Index_Rate'] = groupby_df1['Index_Rate'].apply(lambda x: '%.4f%%' % (x*100))

    groupby_df1['Pre_Stocks_Value'] = groupby_df1['Pre_Stocks_Value'].apply(lambda x: '{:,}'.format(x))
    groupby_df1['Total_Stocks_Value'] = groupby_df1['Total_Stocks_Value'].apply(lambda x: '{:,}'.format(x))
    groupby_df1['Stocks_PL'] = groupby_df1['Stocks_PL'].apply(lambda x: '{:,}'.format(x))
    groupby_df1['Future_PL'] = groupby_df1['Future_PL'].apply(lambda x: '{:,}'.format(x))
    groupby_df1['Total_PL'] = groupby_df1['Total_PL'].apply(lambda x: '{:,}'.format(x))

    return_data_list = []
    return_data_dict = groupby_df1.to_dict("index")
    for (dict_key, dict_value) in return_data_dict.items():
        return_data_list.append(dict_value)
    return_data_list.sort(key=lambda obj: obj['Date'], reverse=False)
    query_result = {'data_list': return_data_list}
    print query_result
    return make_response(jsonify(code=200, data=query_result), 200)


@report.route('/refresh_risk_history', methods=['GET', 'POST'])
def refresh_risk_history():
    all_trade_servers_list = server_constant.get_all_trade_servers()
    from eod_aps.job.server_risk_backup_job import server_risk_backup_job
    server_risk_backup_job(all_trade_servers_list)
    return make_response(jsonify(code=200, message=u"更新成功"), 200)


@report.route('/query_risk_history_detail', methods=['GET', 'POST'])
def query_risk_history_detail():
    query_params = request.json
    strategy_name = query_params.get('strategy_name')
    if 'Earning' in strategy_name:
        strategy_name = 'Earning'
    elif 'Inflow' in strategy_name:
        strategy_name = 'Inflow'

    date_list = date_utils.get_interval_trading_day_list(date_utils.get_now(), -20, '%Y-%m-%d')
    date_list.reverse()
    start_date = date_list[0]
    end_date = date_list[-1]

    query_result_dict = dict()
    server_host = server_constant.get_server_model('host')
    session_history = server_host.get_db_session('history')

    for server_risk_db in session_history.query(ServerRisk).filter(ServerRisk.date.between(start_date, end_date)):
        if strategy_name not in server_risk_db.strategy_name:
            continue

        item_date = date_utils.datetime_toString(server_risk_db.date, '%Y-%m-%d')
        if item_date in query_result_dict:
            query_result_dict[item_date] += float(server_risk_db.total_pl)
        else:
            query_result_dict[item_date] = float(server_risk_db.total_pl)

    pl_list = []
    for date_item in date_list:
        if date_item in query_result_dict:
            pl_list.append(query_result_dict[date_item])
        else:
            pl_list.append(0)

    query_result = {'date_list': date_list, 'pl_list': pl_list}
    return make_response(jsonify(code=200, data=query_result), 200)


@report.route('/save_user', methods=['GET', 'POST'])
def save_user():
    params = request.json
    print params

    id = params.get('id')
    user_id = params.get('user_id')
    password = params.get('password')
    pf_account_list = params.get('pf_account_list')
    describe = params.get('describe')
    role_id = params.get('role_id')

    server_model = server_constant.get_server_model('host')
    session_job = server_model.get_db_session('jobs')
    if id:
        sql_str = "UPDATE `jobs`.`user_list` SET user_id='%s', `password`='%s', `pf_account_list`='%s', `describe`='%s', role_id='%s' WHERE `id`=%s" % \
                            (user_id, password, ','.join(pf_account_list), describe, role_id, id)
    else:
        sql_str = "INSERT INTO `jobs`.`user_list` (user_id, `password`, `pf_account_list`, `describe`, role_id) VALUES ('%s','%s','%s','%s','%s')" % \
                            (user_id, password, ','.join(pf_account_list), describe, role_id)
    session_job.execute(sql_str)
    session_job.commit()
    result_message = u"保存用户:%s成功" % user_id
    return make_response(jsonify(code=200, data=result_message), 200)


@report.route('/query_users', methods=['GET', 'POST'])
def query_users():
    query_sql = 'select a.`id`, a.`user_id`, a.`password`, a.`pf_account_list`, a.`describe`, a.`role_id`, b.`name` as role_name from \
user_list a left join role_list b on a.role_id = b.id'

    server_model = server_constant.get_server_model('host')
    session_job = server_model.get_db_session('jobs')

    user_list = []
    for user_info in session_job.execute(query_sql):
        user_dict = dict()
        user_dict['id'] = user_info[0]
        user_dict['user_id'] = user_info[1]
        user_dict['password'] = user_info[2]
        user_dict['pf_account_list'] = user_info[3].split(',')
        user_dict['describe'] = user_info[4]
        user_dict['role_id'] = user_info[5]
        user_dict['role_name'] = user_info[6]
        user_list.append(user_dict)
    return make_response(jsonify(code=200, data=user_list), 200)


@report.route('/del_user', methods=['GET', 'POST'])
def del_user():
    params = request.json
    del_id = params.get('del_id')

    server_model = server_constant.get_server_model('host')
    session_job = server_model.get_db_session('jobs')
    del_sql = "delete from `jobs`.`user_list` where id=%s" % del_id
    session_job.execute(del_sql)
    session_job.commit()
    result_message = u"删除用户成功"
    return make_response(jsonify(code=200, data=result_message), 200)


@report.route('/save_role', methods=['GET', 'POST'])
def save_role():
    params = request.json
    print params

    id = params.get('id')
    name = params.get('name')
    menu_id_list = params.get('menu_id_list')
    describe = params.get('describe')

    server_model = server_constant.get_server_model('host')
    session_job = server_model.get_db_session('jobs')
    if id:
        sql_str = "UPDATE `jobs`.`role_list` SET `name`='%s', `describe`='%s', `menu_id_list`='%s' WHERE `id`=%s" % \
                            (name, describe, ';'.join(menu_id_list), id)
    else:
        sql_str = "INSERT INTO `jobs`.`role_list` (`name`, `describe`, `menu_id_list`) VALUES ('%s', '%s', '%s')" % \
                            (name, describe, ';'.join(menu_id_list))
    session_job.execute(sql_str)
    session_job.commit()
    result_message = u"保存角色:%s成功" % name
    return make_response(jsonify(code=200, data=result_message), 200)


@report.route('/del_role', methods=['GET', 'POST'])
def del_role():
    params = request.json
    del_id = params.get('del_id')

    server_model = server_constant.get_server_model('host')
    session_job = server_model.get_db_session('jobs')
    del_sql = "delete from `jobs`.`role_list` where id=%s" % del_id
    session_job.execute(del_sql)
    session_job.commit()
    result_message = u"删除角色成功"
    return make_response(jsonify(code=200, data=result_message), 200)


@report.route('/query_roles', methods=['GET', 'POST'])
def query_roles():
    query_sql = 'select `id`, `name`, `describe`, `menu_id_list` from `jobs`.`role_list`'

    server_model = server_constant.get_server_model('host')
    session_job = server_model.get_db_session('jobs')

    role_list = []
    for role_info in session_job.execute(query_sql):
        role_dict = dict()
        role_dict['id'] = role_info[0]
        role_dict['name'] = role_info[1]
        role_dict['describe'] = role_info[2]
        role_dict['menu_id_list'] = role_info[3].split(';')
        role_list.append(role_dict)
    return make_response(jsonify(code=200, data=role_list), 200)


@report.route('/query_menus', methods=['GET', 'POST'])
def query_menus():
    query_sql = 'select `id`, `name`, `describe`, `url` from menu_list'
    server_model = server_constant.get_server_model('host')
    session_job = server_model.get_db_session('jobs')

    menu_list = []
    for menu_info in session_job.execute(query_sql):
        menu_dict = dict()
        menu_dict['key'] = str(menu_info[0])
        menu_dict['label'] = menu_info[1]
        menu_list.append(menu_dict)
    return make_response(jsonify(code=200, data=menu_list), 200)


@report.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    params = request.json
    user_id = params.get('user_id')
    pre_password = params.get('pre_password')
    reset_pwd = params.get('reset_password')
    print user_id, pre_password

    server_model = server_constant.get_server_model('host')
    session_job = server_model.get_db_session('jobs')
    query_sql = "select password, role_id from `jobs`.`user_list` where user_id='%s'" % user_id
    user_info_item = session_job.execute(query_sql).first()
    if not user_info_item or user_info_item[0] != pre_password:
        return make_response(jsonify(code=404, message=u"原密码错误!"))
    else:
        update_sql = "UPDATE `jobs`.`user_list` SET `password`='%s' WHERE user_id='%s'" % (reset_pwd, user_id)
        session_job.execute(update_sql)
        session_job.commit()
        return make_response(jsonify(code=200, message=u"重置密码成功."), 200)
