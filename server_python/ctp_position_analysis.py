# -*- coding: utf-8 -*-
from datetime import datetime
from model.BaseModel import *
from model.order import Order
from model.trade import Trade
from model.position import Position
from model.instrument_commission_rate import InstrumentCommissionRate
from model.BaseModel import *
from model.eod_const import const
from model.server_constans import ServerConstant
from tools.getConfig import getConfig
from tools.file_utils import FileUtils
from tools.date_utils import DateUtils

now = datetime.now()
now_date_str = now.strftime('%Y-%m-%d')
now_datetime_str = now.strftime('%Y-%m-%d %H:%M:%S')
last_trading_day = DateUtils().get_last_trading_day('%Y-%m-%d', now_date_str)
file_path = getConfig()['datafetcher_file_path']
local_server_name = getConfig()['server_name']


def read_position_file_ctp(ctp_file_path):
    print 'Start read file:' + ctp_file_path
    fr = open(ctp_file_path)
    order_array = []
    trade_array = []
    trading_account_array = []
    investor_position_array = []
    commission_rate_array = []
    for line in fr.readlines():
        if 'Account_ID' in line:
            account_id = line.replace('\n', '').split(':')[1]
        else:
            base_model = BaseModel()
            for tempStr in line.split('|')[1].split(','):
                temp_array = tempStr.replace('\n', '').split(':', 1)
                setattr(base_model, temp_array[0].strip(), temp_array[1].strip())
            if 'OnRspQryOrder' in line:
                order_array.append(base_model)
            elif 'OnRspQryTrade' in line:
                trade_array.append(base_model)
            elif 'OnRspQryTradingAccount' in line:
                trading_account_array.append(base_model)
            elif 'OnRspQryInvestorPosition' in line:
                investor_position_array.append(base_model)
            elif 'OnRspQryInstrumentCommissionRate' in line:
                commission_rate_array.append(base_model)

    print 'AccountID:', account_id
    # 删除该账号今日记录
    del_account_position_by_id(account_id)
    del_order_trader_by_id(account_id)

    commission_rate_list = __get_commission_rate_list(commission_rate_array)
    (order_list, order_dict) = __get_order_list(account_id, order_array)
    trade_list = __get__trade_list(account_id, trade_array, order_dict)

    (position_dict, position_db_list) = __build_account_position(account_id, investor_position_array)
    # position_db_list = __calculation_position(trade_list, position_dict)

    if len(trading_account_array) > 0:
        cny_position_db = __get_account_cny(account_id, trading_account_array)
        position_db_list.append(cny_position_db)

    update_db(commission_rate_list, order_list, trade_list, position_db_list)
    update_account_trade_restrictions(account_id)


def __get_commission_rate_list(commission_rate_array):
    commission_rate_list = []
    for commission_rate_info in commission_rate_array:
        commission_rate = InstrumentCommissionRate()
        commission_rate.ticker_type = getattr(commission_rate_info, 'instrumentID', '')
        commission_rate.open_ratio_by_money = getattr(commission_rate_info, 'OpenRatioByMoney', '')
        commission_rate.open_ratio_by_volume = getattr(commission_rate_info, 'OpenRatioByVolume', '')
        commission_rate.close_ratio_by_money = getattr(commission_rate_info, 'CloseRatioByMoney', '')
        commission_rate.close_ratio_by_volume = getattr(commission_rate_info, 'CloseRatioByVolume', '')
        commission_rate.close_today_ratio_by_money = getattr(commission_rate_info, 'CloseTodayRatioByMoney', '')
        commission_rate.close_today_ratio_by_volume = getattr(commission_rate_info, 'CloseTodayRatioByVolume', '')
        commission_rate_list.append(commission_rate)
    return commission_rate_list


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


def update_db(commission_rate_list, order_list, trade_list, position_db_list):
    for commission_rate_db in commission_rate_list:
        session_common.merge(commission_rate_db)
    for order_db in order_list:
        session_om.merge(order_db)
    for trade_db in trade_list:
        session_om.merge(trade_db)
    for position_db in position_db_list:
        session_portfolio.add(position_db)


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
        order_db.sys_id = getattr(order_info, 'OrderSysID', '')
        # sys_id为空表示交易未到达交易所即被打回
        if order_db.sys_id == '':
            continue

        order_db.account = account_id
        order_db.symbol = getattr(order_info, 'InstrumentID', '')
        if local_server_name == 'huabao':
            if not ('IH' in order_db.symbol or 'IC' in order_db.symbol or 'IF' in order_db.symbol):
                continue
        if local_server_name == 'zhongxin':
            if 'IH' in order_db.symbol or 'IC' in order_db.symbol or 'IF' in order_db.symbol:
                continue

        # 0:买，1：卖
        order_db.direction = getattr(order_info, 'Direction', '')
        # 0:开仓  1:平仓  3:平今  4:平昨
        order_db.trade_type = getattr(order_info, 'CombOffsetFlag', '')

        # 全部成交:'0' 部分成交还在队列中:'1',部分成交不在队列中:'2',未成交还在队列中:'3',
        # 未成交不在队列中:'4',撤单:'5',未知:'a',尚未触发:'b',已触发:'c'
        order_db.status = getattr(order_info, 'OrderStatus', '')

        # 已经提交:'0',撤单已经提交:'1',修改已经提交:'2',已经接受:'3',报单已经被拒绝:'4',撤单已经被拒绝:'5',改单已经被拒绝:'6'
        order_db.submit_status = getattr(order_info, 'OrderSubmitStatus', '')

        trading_day = getattr(order_info, 'InsertDate', '')
        insert_time = getattr(order_info, 'InsertTime', '')
        if (trading_day != '') and (insert_time != ''):
            insert_time_str = '%s-%s-%s %s' % (trading_day[0:4], trading_day[4:6], trading_day[6:8], insert_time)
            if insert_time > now_datetime_str:
                insert_time_str = '%s %s' % (last_trading_day, insert_time)
        else:
            insert_time_str = '%s 00:00:00' % (now_date_str,)
        order_db.insert_time = insert_time_str

        qty = getattr(order_info, 'VolumeTotalOriginal', '')
        if order_db.direction == '0':
            order_db.qty = qty
        elif order_db.direction == '1':
            order_db.qty = 0 - int(qty)
        order_db.price = getattr(order_info, 'LimitPrice', '')
        order_db.ex_qty = getattr(order_info, 'VolumeTraded', '')
        order_list.append(order_db)
        order_dict[order_db.sys_id] = order_db
    return order_list, order_dict


def __get__trade_list(account_id, trade_array, order_dict):
    trade_list = []
    for trade_info in trade_array:
        trade_db = Trade()
        trade_db.symbol = getattr(trade_info, 'InstrumentID', '')
        if local_server_name == 'huabao':
            if not ('IH' in trade_db.symbol or 'IC' in trade_db.symbol or 'IF' in trade_db.symbol):
                continue
        if local_server_name == 'zhongxin':
            if 'IH' in trade_db.symbol or 'IC' in trade_db.symbol or 'IF' in trade_db.symbol:
                continue

        trade_db.order_id = getattr(trade_info, 'OrderSysID', '')
        if trade_db.order_id not in order_dict:
            print '[Error]unfind OrderID:', trade_db.order_id
            continue

        trade_db.trade_id = getattr(trade_info, 'TradeID', '')

        trading_day = getattr(trade_info, 'TradeDate', '')
        insert_time = getattr(trade_info, 'TradeTime', '')
        if (trading_day != '') and (insert_time != ''):
            insert_time_str = '%s-%s-%s %s' % (trading_day[0:4], trading_day[4:6], trading_day[6:8], insert_time)
            if insert_time > now_datetime_str:
                insert_time_str = '%s %s' % (last_trading_day, insert_time)
        else:
            insert_time_str = '%s 00:00:00' % (now_date_str,)
        trade_db.time = insert_time_str

        order_db = order_dict[trade_db.order_id]
        qty = getattr(trade_info, 'Volume', '')
        if order_db.direction == '0':
            trade_db.qty = qty
        elif order_db.direction == '1':
            trade_db.qty = 0 - int(qty)

        trade_db.price = getattr(trade_info, 'Price', '')

        # 普通成交:'0'|期权执行:'1'|OTC成交:'2'|期转现衍生成交:'3'|组合衍生成交:'4'
        trade_db.trade_type = getattr(trade_info, 'TradeType', '')
        # 开仓:'0'|平仓:'1'|强平:'2'|平今:'3'|平昨:'4'|强减:'5'|本地强平:'6'
        trade_db.offsetflag = getattr(trade_info, 'OffsetFlag', '')

        trade_db.account = account_id
        trade_db.direction = getattr(trade_info, 'Direction', '')

        hedge_flag = getattr(trade_info, 'HedgeFlag', '')
        trade_db.hedgeflag = const.HEDGE_FLAG_MAP[hedge_flag]
        trade_list.append(trade_db)
    return trade_list


def __get_account_cny(account_id, message_array):
    if local_server_name == 'huabao' or local_server_name == 'zhongxin':
        account_money_dict = dict()
        fr = open('account_money.txt')
        for line in fr:
            l = line.strip()
            if (l == '') or (l[0] == '#'):
                continue
            else:
                [key, data] = l.split('=')
                account_money_dict[key] = data
        fr.close()


    position_db = Position()
    for trading_account in message_array:
        position_db.date = now_date_str
        position_db.id = account_id
        position_db.symbol = 'CNY'

        if local_server_name == 'huabao' and account_id == '1':
            account_money = int(account_money_dict[account_id])
            position_db.long = account_money
            position_db.long_avail = account_money
            position_db.prev_net = account_money
            position_db.update_date = datetime.now()
        elif local_server_name == 'huabao' and account_id == '2':
            account_money = int(account_money_dict[account_id])
            position_db.long = account_money
            position_db.long_avail = account_money
            position_db.prev_net = account_money
            position_db.update_date = datetime.now()
        elif local_server_name == 'zhongxin' and account_id == '1':
            other_account_money = int(account_money_dict[account_id])
            position_db.long = float(getattr(trading_account, 'Balance', '0')) - other_account_money
            position_db.long_avail = position_db.long
            position_db.prev_net = float(getattr(trading_account, 'PreBalance', '0')) - other_account_money
            position_db.update_date = datetime.now()
        elif local_server_name == 'zhongxin' and account_id == '2':
            other_account_money = int(account_money_dict[account_id])
            position_db.long = float(getattr(trading_account, 'Balance', '0')) - other_account_money
            position_db.long_avail = position_db.long
            position_db.prev_net = float(getattr(trading_account, 'PreBalance', '0')) - other_account_money
            position_db.update_date = datetime.now()
        else:
            position_db.long = getattr(trading_account, 'Balance', '0')
            position_db.long_avail = getattr(trading_account, 'Available', '0')
            position_db.prev_net = getattr(trading_account, 'PreBalance', '0')
            position_db.update_date = datetime.now()
        break
    return position_db


def __build_account_position(account_id, investor_position_array):
    position_list = []
    position_dict = dict()
    ticker_position_dict = dict()
    for investorPosition in investor_position_array:
        symbol = getattr(investorPosition, 'InstrumentID', 'NULL')
        # 过滤掉SP j1609&j1701这种的持仓数据
        if '&' in symbol:
            continue
        if local_server_name == 'huabao':
            if not ('IH' in symbol or 'IC' in symbol or 'IF' in symbol):
                continue
        if local_server_name == 'zhongxin':
            if 'IH' in symbol or 'IC' in symbol or 'IF' in symbol:
                continue

        # 转换hedgeFlag字典
        hedge_flag = getattr(investorPosition, 'HedgeFlag', '0')
        hedge_flag = const.HEDGE_FLAG_MAP[hedge_flag]

        key = '%s|%s' % (symbol, hedge_flag)
        if key in ticker_position_dict:
            ticker_position_dict.get(key).append(investorPosition)
        else:
            ticker_position_dict[key] = [investorPosition]

    for (key, ticker_position_list) in ticker_position_dict.items():
        (symbol, hedge_flag) = key.split('|')
        td_long = 0
        td_long_avail = 0
        td_long_cost = 0.0
        yd_long = 0
        yd_long_remain = 0

        td_short = 0
        td_short_avail = 0
        td_short_cost = 0.0
        yd_short = 0
        yd_short_remain = 0

        long_Frozen = 0
        short_Frozen = 0
        prev_net = 0

        posiDirection_dict = dict()
        for temp_position in ticker_position_list:
            #  1:净,2:多头,3:空头
            posiDirection = getattr(temp_position, 'PosiDirection', '0')
            if posiDirection in posiDirection_dict:
                posiDirection_dict[posiDirection].append(temp_position)
            else:
                posiDirection_dict[posiDirection] = [temp_position]

        for (posiDirection, direction_position_list) in posiDirection_dict.items():
            position = 0
            ydPosition = 0
            position_cost = 0.0
            for temp_position in direction_position_list:
                #  1:今日持仓,2:历史持仓
                positionDate = getattr(temp_position, 'PositionDate', '1')
                if positionDate == '1':
                    position = int(getattr(temp_position, 'Position', '0'))
                    position_cost = float(getattr(temp_position, 'PositionCost', '0'))
                    ydPosition = int(getattr(temp_position, 'YdPosition', '0'))
                elif positionDate == '2':
                    position += int(getattr(temp_position, 'Position', '0'))
                    position_cost = float(getattr(temp_position, 'PositionCost', '0'))
                    ydPosition += int(getattr(temp_position, 'YdPosition', '0'))
                else:
                    print 'error positionDate:', positionDate
                    continue

            if posiDirection == '1':
                td_long = position
                td_long_avail = position

                yd_long = ydPosition
                yd_long_remain = ydPosition

                td_long_cost = position_cost
            elif posiDirection == '2':
                td_long = position
                td_long_avail = position

                yd_long = ydPosition
                yd_long_remain = ydPosition

                td_long_cost = position_cost
            elif posiDirection == '3':
                td_short = position
                td_short_avail = position

                yd_short = ydPosition
                yd_short_remain = ydPosition

                td_short_cost = position_cost
            else:
                print 'error posiDirection:', posiDirection

        prev_net = yd_long - yd_short
        position_db = Position()
        position_db.date = now_date_str
        position_db.id = account_id
        position_db.symbol = symbol
        position_db.hedgeflag = hedge_flag
        position_db.long = td_long
        if symbol == '510050':
            pre_settlement_price = float(getattr(temp_position, 'PreSettlementPrice', '0'))
            position_db.long_cost = td_long * pre_settlement_price
            position_db.long_avail = yd_long_remain
        else:
            position_db.long_cost = td_long_cost
            position_db.long_avail = td_long_avail
        position_db.short = td_short
        position_db.short_cost = td_short_cost
        position_db.short_avail = td_short_avail
        position_db.yd_position_long = yd_long
        position_db.yd_position_short = yd_short
        position_db.yd_long_remain = yd_long_remain
        position_db.yd_short_remain = yd_short_remain
        position_db.prev_net = prev_net
        position_db.frozen = long_Frozen
        position_db.update_date = datetime.now()
        position_dict[key] = position_db
        position_list.append(position_db)
    return position_dict, position_list


def update_account_trade_restrictions(account_id):
    (start_date, end_date) = get_start_end_date()
    cancle_order_dict = dict()
    order_dict = dict()
    query = session_om.query(Order)
    for order_db in query.filter(Order.account == account_id,
                                 Order.insert_time >= start_date,
                                 Order.insert_time <= end_date):
        if order_db.status == 5:
            symbol = order_db.symbol
            if 'IC' in symbol:
                symbol = 'SH000905'
            elif 'IF' in symbol:
                symbol = 'SHSZ300'
            elif 'IH' in symbol:
                symbol = 'SSE50'
            if symbol in cancle_order_dict:
                cancle_order_dict[symbol].append(order_db)
            else:
                cancle_order_dict[symbol] = [order_db]
        order_dict[order_db.sys_id] = order_db

    for (symbol, order_db_list) in cancle_order_dict.items():
        update_sql = "update portfolio.account_trade_restrictions set TODAY_CANCEL = %s where \
                TICKER = '%s' and ACCOUNT_ID = %s" % (len(order_db_list), symbol, account_id)
        session_portfolio.execute(update_sql)

    open_trade_dict = dict()
    query = session_om.query(Trade)
    for trade_db in query.filter(Trade.account == account_id,
                                 Trade.time >= start_date,
                                 Trade.time <= end_date):
        order_id = trade_db.order_id
        if order_id not in order_dict:
            print 'Error order_id:', order_id
            continue
        order_db = order_dict[order_id]
        # 开仓
        if order_db.trade_type != 0:
            continue

        symbol = trade_db.symbol
        if 'IC' in symbol:
            symbol = 'SH000905'
        elif 'IF' in symbol:
            symbol = 'SHSZ300'
        elif 'IH' in symbol:
            symbol = 'SSE50'

        if symbol in open_trade_dict:
            open_trade_dict[symbol] += abs(int(trade_db.qty))
        else:
            open_trade_dict[symbol] = abs(int(trade_db.qty))
    for (symbol, today_open) in open_trade_dict.items():
        update_sql = "update portfolio.account_trade_restrictions set TODAY_OPEN = %s where \
                TICKER = '%s' and ACCOUNT_ID = %s" % (today_open, symbol, account_id)
        session_portfolio.execute(update_sql)


if __name__ == '__main__':
    print 'Enter ctp_position_analysis.'
    host_server_model = ServerConstant().get_server_model('host')
    session_common = host_server_model.get_db_session('common')
    session_portfolio = host_server_model.get_db_session('portfolio')
    session_om = host_server_model.get_db_session('om')

    update_sql = "update portfolio.account_trade_restrictions set TODAY_OPEN = 0, TODAY_CANCEL=0 where 1=1"
    session_portfolio.execute(update_sql)

    ctp_position_file_list = FileUtils(file_path).filter_file('CTP_POSITION', now_date_str)
    for ctp_file in ctp_position_file_list:
        read_position_file_ctp('%s/%s' % (file_path, ctp_file))

    session_common.commit()
    session_portfolio.commit()
    session_om.commit()
    print 'Exit ctp_position_analysis.'