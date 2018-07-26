# -*- coding: utf-8 -*-
# 对每日更新的数据进行校验
import json
from sqlalchemy import desc
from sqlalchemy import not_
import math
from sqlalchemy.sql.expression import func
from model.account import Account
from model.future_main_contract import FutureMainContract
from model.instrument import Instrument
from model.pf_position import PfPosition
from model.position import Position
from model.server_constans import ServerConstant
from job import up_down_limit_check
from model.strategy_parameter import StrategyParameter
from tools.date_utils import DateUtils
from WindPy import *

from tools.email_utils import EmailUtils

server_constant = ServerConstant()
date_utils = DateUtils()
email_list = []


column_filter_list = ['UPDATE_DATE', 'CLOSE_UPDATE_TIME', 'PREV_CLOSE_UPDATE_TIME', 'BUY_COMMISSION', 'SELL_COMMISSION', 'FAIR_PRICE', 'MAX_LIMIT_ORDER_VOL', 'MAX_MARKET_ORDER_VOL']
column_filter_list_temp = ['IS_SETTLE_INSTANTLY', 'INACTIVE_DATE', 'CLOSE', 'volume', 'SHORTMARGINRATIO', 'SHORTMARGINRATIO_HEDGE', 'SHORTMARGINRATIO_SPECULATION',
                           'SHORTMARGINRATIO_ARBITRAGE', 'LONGMARGINRATIO_HEDGE', 'LONGMARGINRATIO', 'LONGMARGINRATIO_SPECULATION', 'LONGMARGINRATIO_ARBITRAGE']

def __wind_login():
    w.start()


def __wind_close():
    w.close()


def __wind_prev_close_dict(ticker_list, date_str):
    prev_close_dict = dict()
    wind_data = w.wsd(ticker_list, "pre_close", date_str, date_str, "Fill=Previous")
    if wind_data.Data[0][0] == 'No Content':
        print 'No Content:'
        return
    data_list = wind_data.Data
    for i in range(0, len(ticker_list)):
        ticker = ticker_list[i]
        ticker_prev_close = data_list[0][i]
        prev_close_dict[ticker] = ticker_prev_close
    return prev_close_dict


def __price_check(server_name_list, type_id):
    # get a random instrument list in the first server and used it in other servers
    server_model = server_constant.get_server_model(server_name_list[0])
    session = server_model.get_db_session('common')

    query = session.query(Instrument)
    instrument_list = []

    if type_id == '6':
        for instrument_db in query.filter(Instrument.type_id == type_id, Instrument.del_flag == 0):
            instrument_list.append(instrument_db)
    else:
        for instrument_db in query.filter(Instrument.type_id == type_id, Instrument.prev_close > 0, Instrument.del_flag == 0).order_by(func.random()).limit(15):
            instrument_list.append(instrument_db)

    instrument_list_str = "('"
    # convert instrument list to string format for sql search
    for instrument in instrument_list[:-1]:
        instrument_list_str += instrument.ticker
        instrument_list_str += "','"
    instrument_list_str += instrument_list[-1].ticker
    instrument_list_str += "')"

    # convert instrument to wind ticker list
    ticker_wind_list = []
    ticker_wind_local_dict = dict()
    for instrument_db in instrument_list:
        ticker_wind_str = ''
        if instrument_db.exchange_id == 18:
            if instrument_db.type_id == 6:
                ticker_wind_str = '%s.SH' % instrument_db.ticker_exch_real
            else:
                ticker_wind_str = '%s.SH' % instrument_db.ticker
        elif instrument_db.exchange_id == 19:
            ticker_wind_str = '%s.SZ' % instrument_db.ticker
        elif instrument_db.exchange_id == 19:
            ticker_wind_str = '%s.SZ' % instrument_db.ticker
        elif instrument_db.exchange_id == 20:
            ticker_wind_str = '%s.SHF' % instrument_db.ticker
        elif instrument_db.exchange_id == 21:
            ticker_wind_str = '%s.DCE' % instrument_db.ticker
        elif instrument_db.exchange_id == 22:
            ticker_wind_str = '%s.CZC' % instrument_db.ticker
        elif instrument_db.exchange_id == 25:
            ticker_wind_str = '%s.CFE' % instrument_db.ticker

        ticker_wind_list.append(ticker_wind_str)
        ticker_wind_local_dict[instrument_db.ticker] = ticker_wind_str

    # get prev close from wind
    now_time = long(date_utils.get_today_str('%H%M%S'))
    if now_time > 200000:
        date_str = date_utils.get_next_trading_day('%Y-%m-%d')
    else:
        date_str = date_utils.get_today_str('%Y-%m-%d')

    wind_prev_close_dict = __wind_prev_close_dict(ticker_wind_list, date_str)

    # get prev close price from each server
    prev_close_server_dict = dict()
    for server_name in server_name_list:
        server_model = server_constant.get_server_model(server_name_list[0])
        session = server_model.get_db_session('common')

        sql_str = "select * from common.instrument where TICKER in %s;" % (instrument_list_str)
        sql_result = session.execute(sql_str)

        prev_close_dict = dict()
        for instrument_info in sql_result:
            prev_close_dict[ticker_wind_local_dict[instrument_info[1]]] = instrument_info[8]
        prev_close_server_dict[server_name] = prev_close_dict

    email_list.append('<table border="1"><tr>')
    email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % 'Ticker')
    email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % 'Wind')
    for server_name in server_name_list:
        email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % server_name)
    email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % 'Check Result')
    email_list.append('</tr>')

    temp_email_list = []
    for ticker_wind in ticker_wind_list:
        prev_close_wind = wind_prev_close_dict[ticker_wind]
        if str(prev_close_wind) != 'nan':
            table_line = '<tr><td align="center" font-size:12px; bgcolor="#ee4c50"><b>%s</b></td><td>%s</td>'\
                     % (ticker_wind, prev_close_wind)
        else:
            table_line = '<tr><td align="center" font-size:12px; bgcolor="#ee4c50"><b>%s</b></td>\
                <td bgcolor="#ee4c50">%s</td>' % (ticker_wind, prev_close_wind)

        prev_close_server_temp = -1000000
        error_flag = False
        for server_name in server_name_list:
            prev_close_server = prev_close_server_dict[server_name][ticker_wind]
            if math.fabs(prev_close_server) != prev_close_server_temp and prev_close_server_temp != -1000000:
                error_flag = True
            if math.fabs(float(prev_close_server) - float(prev_close_wind)) < 0.001 or str(prev_close_wind) == 'nan':
                if type_id == '10':
                    table_line += '<td>%s</td>' % ('%.4f' % (prev_close_server))
                elif type_id == '7,15,16':
                    table_line += '<td>%s</td>' % ('%.3f' % (prev_close_server))
                else:
                    table_line += '<td>%s</td>' % ('%.2f' % (prev_close_server))
            else:
                error_flag = True
                if type_id == '10':
                    table_line += '<td bgcolor="#ee4c50">%s</td>' % ('%.4f' % (prev_close_server))
                elif type_id == '7,15,16':
                    table_line += '<td bgcolor="#ee4c50">%s</td>' % ('%.3f' % (prev_close_server))
                else:
                    table_line += '<td bgcolor="#ee4c50">%s</td>' % ('%.2f' % (prev_close_server))

        if error_flag:
            table_line += '<td bgcolor="#70bbd9">%s</td>' % ('Error')
        else:
            table_line += '<td>%s</td>' % ('  ')

        table_line += '</tr>'
        temp_email_list.append(table_line)

    email_list.extend(temp_email_list)

    email_list.append('</table>')
    email_list.append('<br><br>')

def __cross_market_check(server_model):
    email_list.append('<li>CrossMarket ETF Check</li>')
    session = server_model.get_db_session('common')
    query = session.query(Instrument)
    cross_market_etf_size = query.filter(Instrument.type_id == 7, Instrument.cross_market == 1).count()
    email_list.append('crossmarket etf num:%s<br/><br/>' % cross_market_etf_size)


def __fund_pcf_check(server_name_list):
    etf_set_dict = dict()
    tradingday_error_list_dict = dict()
    for server_name in server_name_list:
        server_model = server_constant.get_server_model(server_name)
        today_filter_str = datetime.now().strftime('%Y%m%d')
        session_portfolio = server_model.get_db_session('portfolio')
        query = session_portfolio.query(Account)

        etf_set = set()
        for account_db in query.filter(not_(Account.allowed_etf_list == None)):
            allow_etf_str = account_db.allowed_etf_list
            for etfTicker in allow_etf_str.split(';'):
                if etfTicker.strip() != '':
                    etf_set.add(etfTicker)

        session = server_model.get_db_session('common')
        query = session.query(Instrument)
        tradingday_error_list = []
        for instrument_db in query.filter(Instrument.type_id.in_((7, 15, 16))):
            if instrument_db.type_id == 16:
                if instrument_db.ticker in etf_set:
                    etf_set.remove(instrument_db.ticker)
                continue

            if instrument_db.pcf is None or instrument_db.pcf == '':
                continue

            pcf_dict = json.loads(instrument_db.pcf)

            if pcf_dict['TradingDay'] == today_filter_str:
                if instrument_db.ticker in etf_set:
                    etf_set.remove(instrument_db.ticker)
            else:
                tradingday_error_list.append(instrument_db.ticker + '|' + pcf_dict['TradingDay'])

            if 'Components' not in pcf_dict:
                continue

        etf_set_dict[server_name] = etf_set
        tradingday_error_list_dict[server_name] = tradingday_error_list

    email_list.append('<table border="1"><tr>')
    email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % 'Index')
    for server_name in server_name_list:
        email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % server_name)
    email_list.append('</tr>')

    email_list.append('<th align="center" font-size:12px; ><b>%s</b></th>' % 'Allow ETF Error list')
    for server_name in server_name_list:
        email_list.append('<th align="center" font-size:12px;><b>%s</b></th>' % '<br/>'.join(etf_set_dict[server_name]))
    email_list.append('</tr>')

    email_list.append('<th align="center" font-size:12px; ><b>%s</b></th>' % 'ETF TradingDay Error list')
    for server_name in server_name_list:
        email_list.append('<th align="center" font-size:12px;><b>%s</b></th>' % '<br/>'.\
                          join(tradingday_error_list_dict[server_name]))
    email_list.append('</tr>')

    email_list.append('</table>')
    email_list.append('<br/><br/>')


def __option_callput_check(server_name_list):
    option_error_list_dict = dict()
    for server_name in server_name_list:
        server_model = server_constant.get_server_model(server_name)
        session = server_model.get_db_session('common')
        query = session.query(Instrument)
        for instrument_db in query.filter(Instrument.type_id == 10):
            name = instrument_db.name
            put_call = instrument_db.put_call
            option_error_list = []
            if ('Call' in name) and (0 == put_call):
                option_error_list.append(instrument_db.ticker)
            elif ('Put' in name) and (1 == put_call):
                option_error_list.append(instrument_db.ticker)
            elif ('-C-' in name) and (0 == put_call):
                option_error_list.append(instrument_db.ticker)
            elif ('-P-' in name) and (1 == put_call):
                option_error_list.append(instrument_db.ticker)

        option_error_list_dict[server_name] = option_error_list

    email_list.append('<h4>Call&Put Check------------</h4>')
    email_list.append('<table border="1"><tr>')
    for server_name in server_name_list:
        email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % server_name)
    email_list.append('</tr>')

    email_list.append('<tr>')
    for server_name in server_name_list:
        email_list.append('<th><b>%s</b></th>' % '<br>'.join(option_error_list_dict[server_name]))
    email_list.append('</tr>')

    email_list.append('</table>')
    email_list.append('<br/><br/>')


def __option_track_undl_tickers_check(server_name_list):
    option_error_dict = dict()
    for server_name in server_name_list:
        server_model = server_constant.get_server_model(server_name)
        session = server_model.get_db_session('common')
        query = session.query(Instrument)
        null_number = query.filter(Instrument.type_id == 10, Instrument.track_undl_tickers == None).count()
        option_error_dict[server_name] = null_number

    email_list.append('<h4>track_undl_tickers Check------------</h4>')
    email_list.append('<table border="1"><tr>')
    for server_name in server_name_list:
        email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % server_name)
    email_list.append('</tr>')

    email_list.append('<tr>')
    for server_name in server_name_list:
        if option_error_dict[server_name] > 0:
            email_list.append('<td bgcolor = "#ee4c50"><b>%s</b></td>' % option_error_dict[server_name])
        else:
            email_list.append('<td><b>%s</b></td>' % option_error_dict[server_name])
    email_list.append('</tr>')

    email_list.append('</table>')
    email_list.append('<br/><br/>')


def __account_position_check(server_name_list):
    account_position_dict_server = dict()
    account_dict_server = dict()
    account_list = []
    for server_name in server_name_list:
        server_model = server_constant.get_server_model(server_name)
        today_filter_str = datetime.now().strftime('%Y-%m-%d')
        session_portfolio = server_model.get_db_session('portfolio')
        query = session_portfolio.query(Position)

        account_position_dict = dict()
        for position_db in query.filter(Position.date == today_filter_str):
            if position_db.id in account_position_dict:
                account_position_dict[position_db.id].append(position_db)
            else:
                account_position_dict[position_db.id] = [position_db]

        account_position_dict_server[server_name] = account_position_dict

        query = session_portfolio.query(Account)
        account_dict = dict()
        for account_db in query:
            account_dict[account_db.accountid] = account_db
            if account_db.accountid not in account_list:
                account_list.append(account_db.accountid)

        account_dict_server[server_name] = account_dict

    account_list = sorted(account_list)

    email_list.append('<table border="1"><tr>')
    email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % 'Account')
    for server_name in server_name_list:
        email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % server_name)
    email_list.append('</tr>')

    for account_id in account_list:
        email_list.append('<tr><td align="center" font-size:12px; bgcolor="#ee4c50"><b>%s</b>' % (account_id))
        for server_name in server_name_list:
            if account_dict_server[server_name].has_key(account_id):
                account_db = account_dict_server[server_name][account_id]
                if account_db.enable == 1:
                    if account_id in account_position_dict_server[server_name]:
                        account_position_db = account_position_dict_server[server_name][account_id][0]
                        update_date = account_position_db.update_date
                    else:
                        update_date = 'Null'
                    if update_date != 'Null':
                        if int(datetime.now().strftime('%H%M%S')) > 200000:
                            if update_date > datetime.strptime(datetime.now().strftime('&Y-%m-%d') + ' 20:00:00', '&Y-%m-%d %H:%M:%S'):
                                email_list.append('<td align="center">%s</td>' % ('%s_%s' % (account_db.accounttype, update_date)))
                            else:
                                list.append('<td align="center"; bgcolor="#ee4c50">%s</td>' % ('%s_%s' % (account_db.accounttype, update_date)))
                        else:
                            email_list.append('<td align="center">%s</td>' % ('%s_%s' % (account_db.accounttype, update_date)))
                    else:
                        email_list.append('<td align="center"  bgcolor="#ee4c50">%s</td>' % ('%s_%s'\
                                                                % (account_db.accounttype, update_date)))
                else:
                    email_list.append('<td align="center">%s</td>' % ('/'))
            else:
                email_list.append('<td align="center">%s</td>' % ('/'))
        email_list.append('</tr>')
    email_list.append('</table>')
    email_list.append('<br/><br/>')


def __strategy_parameter_check(server_name_list):
    server_model = ServerConstant().get_server_model('host')
    session = server_model.get_db_session('common')
    query = session.query(Instrument)
    future_dict = dict()
    for instrument_db in query.filter(Instrument.type_id == 1):
        future_dict[instrument_db.ticker] = instrument_db

    maincontract_dict = dict()
    query = session.query(FutureMainContract)
    for future_maincontract_db in query:
        maincontract_dict[future_maincontract_db.ticker_type] = future_maincontract_db

    for server_name in server_name_list:
        email_list.append('<font >Strategy Parameter Check: %s</font><br/>' % (server_name))
        server_model = ServerConstant().get_server_model(server_name)
        server_session = server_model.get_db_session('strategy')

        strategy_check_result = []
        for strategy_name_group in server_session.query(StrategyParameter.name).group_by(StrategyParameter.name).all():
            strategy_name = strategy_name_group[0]
            if 'Calendar' not in strategy_name:
                continue
            print strategy_name
            strategy_parameter_db = server_session.query(StrategyParameter).filter(StrategyParameter.name == strategy_name).order_by(desc(StrategyParameter.time)).first()
            strategy_parameter_dict = json.loads(strategy_parameter_db.value)

            calendar_future_dict = dict()
            for (dict_key, dict_value) in strategy_parameter_dict.items():
                if 'BackFuture' in dict_key:
                    back_future_name = dict_value
                    if back_future_name not in future_dict:
                        email_list.append('<font color=red>strategy:%s BackFuture:%s can not find!</font><br/>' % (strategy_name, back_future_name))
                    else:
                        back_future_db = future_dict[back_future_name]
                        if back_future_db.exchange_id != 25 and (datetime.strptime(str(back_future_db.expire_date), '%Y-%m-%d') - datetime.now()).days <= 33:
                            strategy_check_result.append('<font color=red>strategy:%s BackFuture:%s expire_date:%s less than 30days!</font><br/>' % \
                                          (strategy_name, back_future_name,
                                           back_future_db.expire_date.strftime("%Y-%m-%d")))

                    ticker_type = filter(lambda x: not x.isdigit(), back_future_name)
                    if ticker_type in calendar_future_dict:
                        calendar_future_dict[ticker_type].append(back_future_name)
                    else:
                        calendar_future_dict[ticker_type] = [back_future_name, ]

                    ticker_month = filter(lambda x: x.isdigit(), back_future_name)
                    future_maincontract_db = maincontract_dict[ticker_type]
                    main_symbol_month = filter(lambda x: x.isdigit(), future_maincontract_db.main_symbol)
                    if str(ticker_month) < str(main_symbol_month):
                        strategy_check_result.append('<font color=red>strategy:%s BackFuture:%s, Main Contract is:%s</font><br/>' % (
                                    strategy_name, back_future_name, future_maincontract_db.main_symbol))
                elif 'FrontFuture' in dict_key:
                    front_future_name = dict_value
                    if front_future_name not in future_dict:
                        email_list.append('<font color=red>strategy:%s FrontFuture:%s can not find!</font><br/>' % (strategy_name, front_future_name))
                    else:
                        front_future_db = future_dict[front_future_name]
                        if front_future_db.exchange_id != 25 and (datetime.strptime(str(front_future_db.expire_date), '%Y-%m-%d') - datetime.now()).days <= 30:
                            strategy_check_result.append('<font color=red>strategy:%s FrontFuture:%s expire_date:%s less than 30days!</font><br/>' % \
                                          (strategy_name, front_future_name,
                                           front_future_db.expire_date.strftime("%Y-%m-%d")))

                    ticker_type = filter(lambda x: not x.isdigit(), front_future_name)
                    if ticker_type in calendar_future_dict:
                        calendar_future_dict[ticker_type].append(front_future_name)
                    else:
                        calendar_future_dict[ticker_type] = [front_future_name, ]

                    ticker_month = filter(lambda x: x.isdigit(), front_future_name)
                    future_maincontract_db = maincontract_dict[ticker_type]
                    main_symbol_month = filter(lambda x: x.isdigit(), future_maincontract_db.main_symbol)
                    if str(ticker_month) < str(main_symbol_month):
                        strategy_check_result.append('<font color=red>strategy:%s FrontFuture:%s, Main Contract is:%s</font><br/>' % (
                                    strategy_name, front_future_name, future_maincontract_db.main_symbol))

            for (key, ticker_list) in calendar_future_dict.items():
                if len(ticker_list) != 2:
                    continue
                if ticker_list[0] == ticker_list[1]:
                    strategy_check_result.append(
                        '<font color=red>Ticker:%s FrontFuture and BackFuture is same!</font><br/>' % ticker_list[0])

        if len(strategy_check_result) > 0:
            strategy_check_result.insert(0, '<li>server:%s, Check Strategy Parameter</li>' % server_name)
            email_list.extend(strategy_check_result)
            EmailUtils(EmailUtils.group4).send_email_group_all('[Error]Strategy Parameter Check', '\n'.join(strategy_check_result), 'html')
    email_list.append('<br/><br/>')

def __account_trade_restrictions_check(server_name_list):

    email_list.append('<li>Check  Today Cancel</li>')
    email_list.append('<table border="1"><tr>')
    email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % ' ')
    for server_name in server_name_list:
        email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % server_name)
    email_list.append('</tr>')

    email_list.append('<tr><th align="center" font-size:12px; bgcolor="#ee4c50"><b>%s</b></th>' % 'account trade restrictions')
    for server_name in server_name_list:
        server_model = ServerConstant().get_server_model(server_name)
        session_portfolio = server_model.get_db_session('portfolio')
        query_sql = "select sum(TODAY_CANCEL) from portfolio.account_trade_restrictions t where t.TODAY_CANCEL > 0"
        today_cancel_sum_num = session_portfolio.execute(query_sql).first()[0]
        if today_cancel_sum_num == 0 or today_cancel_sum_num is None:
            email_list.append('<th align="center" font-size:12px; bgcolor="#ee4c50"><b>%s</b></th>' % today_cancel_sum_num)
        else:
            email_list.append('<th><b>%s</b></th>' % today_cancel_sum_num)
    email_list.append('</tr>')
    email_list.append('</table>')
    email_list.append('<br/><br/>')


def get_instrument_informantion(server_name):
    server_model = server_constant.get_server_model(server_name)
    session_common = server_model.get_db_session('common')

    query_sql_column = "select COLUMN_NAME from information_schema.COLUMNS where table_name = 'instrument' and table_schema = 'common';"
    query_result_column = session_common.execute(query_sql_column)
    column_list = []
    for query_line in query_result_column:
        if (query_line[0] not in column_filter_list) and (query_line[0] not in column_filter_list_temp):
            column_list.append(query_line[0])
    column_list = sorted(column_list)

    column_list_str = ','.join(column_list)

    query_sql_instrument_value = "select %s from common.instrument order by id;" % (column_list_str)
    query_result_instrument_value = session_common.execute(query_sql_instrument_value)

    instrument_dict = dict()
    ticker_list = []
    for result_line in query_result_instrument_value:
        instrument_value_dict = dict()
        i = 0
        for column in column_list:
            if column.upper() == "TICKER":
                ticker_name = result_line[i]
                ticker_list.append(ticker_name)
            instrument_value_dict[column] = result_line[i]
            i += 1
        instrument_dict[ticker_name] = instrument_value_dict

    return instrument_dict, column_list, ticker_list


def __position_check(server_name_list):
    server_host = ServerConstant().get_server_model('host')
    session = server_host.get_db_session('common')
    maincontract_list = []
    query = session.query(FutureMainContract)
    for future_maincontract_db in query:
        maincontract_list.append(future_maincontract_db.pre_main_symbol)

    date_str = date_utils.get_today_str('%Y-%m-%d')
    for server_name in server_name_list:
        server_model = ServerConstant().get_server_model(server_name)
        session_portfolio = server_model.get_db_session('portfolio')
        query_pf_position = session_portfolio.query(PfPosition)
        for pf_position_db in query_pf_position.filter(PfPosition.date >= date_str):
            if pf_position_db.symbol.isdigit():
                continue
            filter_symbol = pf_position_db.symbol.split(' ')[0]
            if filter_symbol in maincontract_list:
                email_list.append('<font color=red>pf_position---server:%s, date:%s, id:%s, symbol:%s</font><br/>' % \
                                  (server_name, pf_position_db.date, pf_position_db.id, pf_position_db.symbol))
        query_position = session_portfolio.query(Position)
        for account_position_db in query_position.filter(Position.date >= date_str):
            if not account_position_db.symbol.isdigit():
                continue
            filter_symbol = account_position_db.symbol.split(' ')[0]
            if filter_symbol in maincontract_list:
                email_list.append('<font color=red>account_position---server:%s, date:%s, id:%s, symbol:%s</font><br/>' % \
                                  (server_name, pf_position_db.date, pf_position_db.id, pf_position_db.symbol))


def instrument_check(server_name_list):
    instrument_info_dict = dict()
    column_list_dict = dict()
    ticker_list_dict = dict()
    global email_list

    [instrument_info_origin, column_list_origin, ticker_list_origin] = get_instrument_informantion(server_name_list[0])

    for server_name in server_name_list[1:]:
        [instrument_info, column_list, ticker_list] = get_instrument_informantion(server_name)
        instrument_info_dict[server_name] = instrument_info
        column_list_dict[server_name] = column_list
        ticker_list_dict[server_name] = ticker_list

    column_list_merge = column_list_origin
    ticker_list_merge = ticker_list_origin
    for server_name in server_name_list[1:]:
        column_list_merge = list(set(column_list_merge + column_list_dict[server_name]))
        ticker_list_merge = list(set(ticker_list_merge + ticker_list_dict[server_name]))
        if column_list_dict[server_name] != column_list_origin:
            email_list.append("%s: column list error!\n\n" % (server_name))
        if ticker_list_dict[server_name] != ticker_list_origin:
            email_list.append("%s: ticker list error!\n\n" % (server_name))

    email_list.append('<table border="1"><tr>')
    email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>column</b></th>')
    email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>ticker</b></th>')
    for server_name in server_name_list:
        email_list.append('<th align="center" font-size:12px; bgcolor="#70bbd9"><b>%s</b></th>' % server_name)
    email_list.append('</tr>')


    for ticker in ticker_list_merge:
        for column in column_list_merge:
            value_origin = instrument_info_origin[ticker][column]
            error_flag = False
            for server_name in server_name_list[1:]:
                value = instrument_info_dict[server_name][ticker][column]
                if value != value_origin:
                    error_flag = True
            if error_flag:
                table_line = '<tr><td align="center" font-size:12px; bgcolor="#ee4c50"><b>%s</b></td>' % (column)
                table_line += '<td align="center" font-size:12px; bgcolor="#ee4c50"><b>%s</b></td>' % (ticker)
                table_line += '<td align="center" font-size:12px;><b>%s</b></td>' % (value_origin)
                for server_name in server_name_list[1:]:
                    value = instrument_info_dict[server_name][ticker][column]
                    if value != value_origin:
                        table_line += '<td align="center" font-size:12px; bgcolor="#ee4c50"><b>%s</b></td>' % (value)
                    else:
                        table_line += '<td align="center" font-size:12px><b>%s</b></td>' % (value)
                table_line += '</tr>'
                email_list.append(table_line)
    email_list.append('</table>')


def db_check_job(server_name_list):
    __wind_login()
    global email_list
    email_list = []
    subject = 'DailyCheck Check Result'

    email_list.append('<li>check Account Position</li>')
    __account_position_check(server_name_list)

    email_list.append('<li>Check Stock Prev_Close</li>')
    __price_check(server_name_list, '4')

    email_list.append('<li>Check Fund Prev_Close</li>')
    __price_check(server_name_list, '7,15,16')

    email_list.append('<li>Check Future Prev_Close</li>')
    __price_check(server_name_list, '1')

    email_list.append('<li>Check Option Prev_Close</li>')
    __price_check(server_name_list, '10')

    email_list.append('<li>Check Index Prev_Close</li>')
    __price_check(server_name_list, '6')

    email_list.append('<li>check Fund PCF Information</li>')
    __fund_pcf_check(server_name_list)

    email_list.append('<li>check Option Call/Put</li>')
    __option_callput_check(server_name_list)

    email_list.append('<li>check Option track_undl_tickers</li>')
    __option_track_undl_tickers_check(server_name_list)

    email_list.append('<li>check Strategy Parameter</li>')
    __strategy_parameter_check(['nanhua_web',])

    email_list.append('<li>check Account Trade Restrictions</li>')
    __account_trade_restrictions_check(['nanhua_web', 'zhongxin'])

    email_list.append('<li>position check</li>')
    __position_check(['huabao', 'nanhua', 'zhongxin', 'guoxin'])

    email_list.append('<li>instrument check</li>')
    instrument_check(['huabao', 'nanhua', 'zhongxin', 'guoxin'])

    EmailUtils(EmailUtils.group2).send_email_group_all(subject, '\n'.join(email_list), 'html')

    __wind_close()


def db_check_future_job(server_name_list):
    __wind_login()
    global email_list
    email_list = []
    subject = 'DailyCheck Check Result'

    email_list.append('<li>check Account Position</li>')
    __account_position_check(server_name_list)

    email_list.append('<li>Check Future Prev_Close</li>')
    __price_check(server_name_list, '1')

    EmailUtils(EmailUtils.group2).send_email_group_all(subject, '\n'.join(email_list), 'html')

    __wind_close()


def account_check_job(server_name_list):
    global email_list
    email_list = []
    subject = 'Account Check Result'

    email_list.append('<li>check Account Position</li>')
    __account_position_check(server_name_list)

    EmailUtils(EmailUtils.group2).send_email_group_all(subject, '\n'.join(email_list), 'html')


def up_down_limit_check_job():
    email_list.append('start check uplimit and downlimit:<br/>')
    udc_result = up_down_limit_check.start()
    email_list.append(udc_result)


if __name__ == '__main__':
    # db_check_job(['nanhua', 'guoxin', 'huabao', 'zhongxin'])

    global email_list
    email_list = []
    subject = 'DailyCheck Check Result'
    __wind_login()

    email_list.append('<li>check Account Position</li>')
    __account_position_check(['guoxin', ])
    __price_check(['huabao', ], '4')
    __wind_close()

    EmailUtils(EmailUtils.group2).send_email_group_all(subject, '\n'.join(email_list), 'html')