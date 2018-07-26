# -*- coding: utf-8 -*-
# 新湖交易系统持仓数据更新——讯投
from datetime import datetime
from model.order import Order
from model.trade import Trade
from model.position import Position
from model.BaseModel import *
from model.server_constans import ServerConstant
from tools.getConfig import getConfig
from tools.file_utils import FileUtils
from tools.date_utils import DateUtils

now = datetime.now()
now_date_str = now.strftime('%Y-%m-%d')
now_datetime_str = now.strftime('%Y-%m-%d %H:%M:%S')
last_trading_day = DateUtils().get_last_trading_day('%Y-%m-%d', now_date_str)
file_path = getConfig()['datafetcher_file_path']

HEDGE_FLAG_MAP = {'49': '0', }
Direction_Map = {'48': '2', '49': '3'}


def read_position_file_xt(xt_file_path, add_flag):
    print 'Start read file:' + xt_file_path
    fr = open(xt_file_path)
    order_array = []
    trade_array = []
    trading_account_array = []
    investor_position_array = []
    for line in fr.readlines():
        if 'Account_ID' in line:
            account_id = line.replace('\n', '').split(':')[1]
        else:
            base_model = BaseModel()
            for tempStr in line.split('|')[1].split(','):
                temp_array = tempStr.replace('\n', '').split(':', 1)
                setattr(base_model, temp_array[0].strip(), temp_array[1].strip())
            if 'OnQryOrder' in line:
                order_array.append(base_model)
            elif 'OnQryTrade' in line:
                trade_array.append(base_model)
            elif 'OnQryAccount' in line:
                trading_account_array.append(base_model)
            elif 'OnQryPosition' in line:
                investor_position_array.append(base_model)

    print 'AccountID:', account_id

    if add_flag:
        # 删除该账号今日记录
        del_account_position_by_id(account_id)

    (order_list, order_dict) = __get_order_list(account_id, order_array)
    trade_list = __get__trade_list(account_id, trade_array, order_dict)

    (position_dict, position_db_list) = __build_account_position(account_id, investor_position_array)

    cny_position_db = __get_account_cny(account_id, trading_account_array)
    position_db_list.append(cny_position_db)
    update_db(order_list, trade_list, position_db_list)


def __calculation_position(trade_list, position_dict):
    trade_list = sorted(trade_list, cmp=lambda x, y: cmp(x.time, y.time), reverse=False)
    for trade_info in trade_list:
        dict_key = '%s|%s' % (trade_info.symbol, trade_info.hedge_flag)
        if dict_key not in position_dict:
            print 'error trade:', trade_info.print_info()
            continue
        position_db = position_dict[dict_key]
        qty = int(trade_info.qty)
        if trade_info.direction == '0':  # 买:0
            if trade_info.offsetflag == '0':  # 开仓
                position_db.td_buy_long += qty
            elif trade_info.offsetflag == '1':  # 平仓
                a = min(qty, position_db.td_sell_short)
                position_db.yd_short_remain -= max(qty - position_db.td_sell_short, 0)
                position_db.td_sell_short -= a
            elif trade_info.offsetflag == '3':  # 平今
                position_db.td_sell_short -= qty
            elif trade_info.offsetflag == '4':  # 平昨
                position_db.yd_short_remain -= qty
        elif trade_info.direction == '1':
            if trade_info.offsetflag == '0':  # 开仓
                position_db.td_sell_short += qty
            elif trade_info.offsetflag == '1':  # 平仓
                a = min(qty, position_db.td_buy_long)
                position_db.yd_long_remain -= max(qty - position_db.td_buy_long, 0)
                position_db.td_buy_long -= a
            elif trade_info.offsetflag == '3':  # 平今
                position_db.td_buy_long -= qty
            elif trade_info.offsetflag == '4':  # 平昨
                position_db.yd_long_remain -= qty

    position_db_list = []
    for (symbol, position_db) in position_dict.items():
        position_db_list.append(position_db)
    return position_db_list


def update_db(order_list, trade_list, position_db_list):
    # for order_db in order_list:
    #     session_om.merge(order_db)
    # for trade_db in trade_list:
    #     session_om.merge(trade_db)
    for position_db in position_db_list:
        session_portfolio.merge(position_db)


def del_account_position_by_id(account_id):
    del_sql = "delete from portfolio.account_position where ID= '%s' and DATE ='%s'" % (account_id, now_date_str)
    session_portfolio.execute(del_sql)


def get_start_end_date():
    now_time = long(now.strftime('%H%M%S'))
    if (80000 < now_time < 190000) or (0 < now_time < 30000):
        last_trading_day = DateUtils().get_last_trading_day('%Y-%m-%d', now_date_str)
        start_date = last_trading_day + ' 21:00:00'
    else:
        start_date = now_date_str + ' 21:00:00'
    end_date = now.strftime('%Y-%m-%d %H:%M:%S')
    return start_date, end_date


def del_order_trader_by_id(account_id):
    (start_date, end_date) = get_start_end_date()
    del_sql = "delete from om.order_broker where ACCOUNT=%s and INSERT_TIME>'%s'" % (account_id, start_date)
    session_om.execute(del_sql)

    del_sql = "delete from om.trade2_broker where ACCOUNT=%s and TIME>'%s'" % (account_id, start_date)
    session_om.execute(del_sql)


def __get_order_list(account_id, order_array):
    order_list = []
    order_dict = dict()
    for order_info in order_array:
        order_db = Order()
        order_db.sys_id = getattr(order_info, 'm_strOrderSysID', '')
        # sys_id为空表示交易未到达交易所即被打回
        if order_db.sys_id == '':
            continue

        order_db.account = account_id
        order_db.symbol = getattr(order_info, 'm_strInstrumentID', '')

        # 48:买，49：卖
        order_db.direction = getattr(order_info, 'm_nDirection', '')

        # 0:开仓  1:平仓  3:平今  4:平昨
        order_db.trade_type = getattr(order_info, 'm_eOffsetFlag', '')

        # 全部成交:'0' 部分成交还在队列中:'1',部分成交不在队列中:'2',未成交还在队列中:'3',
        # 未成交不在队列中:'4',撤单:'5',未知:'a',尚未触发:'b',已触发:'c'
        order_db.status = getattr(order_info, 'EEntrustStatus', '')

        # 已经提交:'0',撤单已经提交:'1',修改已经提交:'2',已经接受:'3',报单已经被拒绝:'4',撤单已经被拒绝:'5',改单已经被拒绝:'6'
        order_db.submit_status = getattr(order_info, 'EEntrustSubmitStatus', '')

        trading_day = getattr(order_info, 'm_strInsertDate', '')
        insert_time = getattr(order_info, 'm_strInsertTime', '')
        if (trading_day != '') and (insert_time != ''):
            insert_time_str = '%s-%s-%s %s' % (trading_day[0:4], trading_day[4:6], trading_day[6:8], insert_time)
            if insert_time > now_datetime_str:
                insert_time_str = '%s %s' % (last_trading_day, insert_time)
        else:
            insert_time_str = '%s 00:00:00' % (now_date_str,)
        order_db.insert_time = insert_time_str

        qty = getattr(order_info, 'm_nTotalVolume', '')
        if order_db.direction == '0':
            order_db.qty = qty
        elif order_db.direction == '1':
            order_db.qty = 0 - int(qty)
        order_db.price = getattr(order_info, 'm_dAveragePrice', '')
        order_db.ex_qty = getattr(order_info, 'm_nTradedVolume', '')
        order_list.append(order_db)
        order_dict[order_db.sys_id] = order_db
    return order_list, order_dict


def __get__trade_list(account_id, trade_array, order_dict):
    trade_list = []
    for trade_info in trade_array:
        trade_db = Trade()
        trade_db.symbol = getattr(trade_info, 'm_strInstrumentID', '')
        trade_db.order_id = getattr(trade_info, 'm_strOrderSysID', '')
        if trade_db.order_id not in order_dict:
            print '[Error]unfind OrderID:', trade_db.order_id
            continue

        trade_db.trade_id = getattr(trade_info, 'm_strTradeID', '')

        trading_day = getattr(trade_info, 'm_strTradeDate', '')
        insert_time = getattr(trade_info, 'm_strTradeTime', '')
        if (trading_day != '') and (insert_time != ''):
            insert_time_str = '%s-%s-%s %s' % (trading_day[0:4], trading_day[4:6], trading_day[6:8], insert_time)
            if insert_time > now_datetime_str:
                insert_time_str = '%s %s' % (last_trading_day, insert_time)
        else:
            insert_time_str = '%s 00:00:00' % (now_date_str,)
        trade_db.time = insert_time_str

        order_db = order_dict[trade_db.order_id]
        qty = getattr(trade_info, 'm_nVolume', '')
        if order_db.direction == '48':
            trade_db.qty = qty
        elif order_db.direction == '49':
            trade_db.qty = 0 - int(qty)

        trade_db.price = getattr(trade_info, 'm_dAveragePrice', '')

        # 普通成交:'0'|期权执行:'1'|OTC成交:'2'|期转现衍生成交:'3'|组合衍生成交:'4'
        trade_db.trade_type = 0
        # 开仓:'0'|平仓:'1'|强平:'2'|平今:'3'|平昨:'4'|强减:'5'|本地强平:'6'
        trade_db.offsetflag = getattr(trade_info, 'm_nOffsetFlag', '')

        trade_db.account = account_id
        trade_db.direction = getattr(trade_info, 'm_nDirection', '')

        hedge_flag = getattr(trade_info, 'm_nHedgeFlag', '')
        trade_db.hedgeflag = HEDGE_FLAG_MAP[hedge_flag]
        trade_list.append(trade_db)
    return trade_list


def __get_account_cny(account_id, message_array):
    query_position = session_portfolio.query(Position)
    position_db = query_position.filter(Position.id == account_id, Position.date == now_date_str, Position.symbol == 'CNY').first()
    if position_db is None:
        position_db = Position()

    for trading_account in message_array:
        position_db.date = now_date_str
        position_db.id = account_id
        position_db.symbol = 'CNY'

        position_db.long = getattr(trading_account, 'm_dBalance', '0')
        position_db.long_avail = getattr(trading_account, 'm_dAvailable', '0')
        position_db.prev_net = getattr(trading_account, 'm_dPreBalance', '0')
        position_db.update_date = datetime.now()
    return position_db


def __build_account_position(account_id, investor_position_array):
    last_position_dict = dict()
    query_position = session_portfolio.query(Position)
    for position_db in query_position.filter(Position.id == account_id, Position.date == now_date_str):
        if position_db.symbol == 'CNY':
            continue
        last_position_dict[position_db.symbol] = position_db

    position_list = []
    position_dict = dict()
    ticker_position_dict = dict()
    for investorPosition in investor_position_array:
        symbol = getattr(investorPosition, 'm_strInstrumentID', 'NULL')
        # 过滤掉SP j1609&j1701这种的持仓数据
        if '&' in symbol:
            continue

        # 转换hedgeFlag字典
        hedge_flag = getattr(investorPosition, 'm_nHedgeFlag', '0')
        hedge_flag = HEDGE_FLAG_MAP[hedge_flag]

        key = '%s|%s' % (symbol, hedge_flag)
        if key in ticker_position_dict:
            ticker_position_dict.get(key).append(investorPosition)
        else:
            ticker_position_dict[key] = [investorPosition]

    for (key, ticker_position_list) in ticker_position_dict.items():
        (symbol, hedge_flag) = key.split('|')
        td_long = 0
        td_long_cost = 0.0
        yd_long_remain = 0

        td_short = 0
        td_short_cost = 0.0
        yd_short_remain = 0
        long_frozen = 0

        for temp_position in ticker_position_list:
            qty_value = int(getattr(temp_position, 'm_nPosition', '0'))
            qty_cost_value = float(getattr(temp_position, 'm_dPositionCost', '0'))

            #  1:净,2:多头,3:空头
            posiDirection_str = getattr(temp_position, 'm_nDirection', '0')
            posiDirection = Direction_Map[posiDirection_str]

            #  1:今日持仓,0:历史持仓
            is_today = getattr(temp_position, 'm_bIsToday', '0')
            if is_today == '0' and posiDirection == '2':
                yd_long_remain = qty_value
                td_long_cost += qty_cost_value
            elif is_today == '0' and posiDirection == '3':
                yd_short_remain = qty_value
                td_short_cost += qty_cost_value
            elif is_today == '1' and posiDirection == '2':
                td_long = qty_value
                td_long_cost += qty_cost_value
            elif is_today == '1' and posiDirection == '3':
                td_short = qty_value
                td_short_cost += qty_cost_value
            else:
                print 'error m_bIsToday:%s, posiDirection:%s' % (is_today ,posiDirection)
                continue

        prev_net = yd_long_remain - yd_short_remain

        if symbol in  last_position_dict:
            position_db = last_position_dict[symbol]
        else:
            position_db = Position()
            position_db.yd_position_long = yd_long_remain
            position_db.yd_position_short = yd_short_remain

        position_db.date = now_date_str
        position_db.id = account_id
        position_db.symbol = symbol
        position_db.hedgeflag = hedge_flag
        position_db.long = td_long + yd_long_remain
        position_db.long_cost = td_long_cost
        position_db.long_avail = td_long + yd_long_remain
        position_db.short = td_short + yd_short_remain
        position_db.short_cost = td_short_cost
        position_db.short_avail = td_short + yd_short_remain

        position_db.yd_long_remain = yd_long_remain
        position_db.yd_short_remain = yd_short_remain
        position_db.prev_net = prev_net
        position_db.frozen = long_frozen
        position_db.update_date = datetime.now()
        position_dict[key] = position_db
        position_list.append(position_db)
    return position_dict, position_list


def __account_position_enter(add_flag):
    print 'Enter XT_position_analysis add_account_position.'
    host_server_model = ServerConstant().get_server_model('host')
    global session_portfolio, session_om
    session_portfolio = host_server_model.get_db_session('portfolio')
    session_om = host_server_model.get_db_session('om')

    xt_position_file_list = FileUtils(file_path).filter_file('PROXYXH_POSITION', now_date_str)
    for xt_file in xt_position_file_list:
        read_position_file_xt('%s/%s' % (file_path, xt_file), add_flag)

    session_portfolio.commit()
    session_om.commit()
    print 'Exit XT_position_analysis add_account_position.'


def add_account_position():
    __account_position_enter(True)

def update_account_position():
    __account_position_enter(False)


if __name__ == '__main__':
    add_account_position()

