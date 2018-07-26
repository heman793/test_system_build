# -*- coding: utf-8 -*-
# 将各接口返回的tradetype类型转换成系统使用的(保存版本，根据交易所的返回trade来计算)
from datetime import datetime
from model.account import Account
from model.instrument import Instrument
from model.trade import Trade
from model.position import Position
from model.server_constans import ServerConstant
import json
from tools.date_utils import DateUtils

now = datetime.now()
now_date_str = now.strftime('%Y-%m-%d')

instrument_dict = dict()


# NORMAL = 0,
# SHORT = 1,
# OPEN = 2,
# CLOSE = 3,
# CLOSE_YESTERDAY = 4,
# RedPur = 5,
# MergeSplit = 6,
# NA = 7,
# EXERCISE = 8

def __build_instrument_dict():
    query = session_common.query(Instrument)
    for instrument_db in query:
        instrument_dict[instrument_db.ticker] = instrument_db


def __calculation_position_femas(account_db, trade_list):
    position_dict = dict()
    query_position = session_portfolio.query(Position)
    for position_db in query_position.filter(Position.id == account_db.accountid, Position.date == now_date_str):
        key = '%s|%s' % (position_db.symbol, position_db.hedgeflag)
        position_dict[key] = position_db

    trade_list = sorted(trade_list, cmp=lambda x, y: cmp(x.time, y.time), reverse=False)
    for trade_db in trade_list:
        instrument_db = instrument_dict[trade_db.symbol]

        dict_key = '%s|%s' % (trade_db.symbol, trade_db.hedgeflag)
        if dict_key not in position_dict:
            print 'error trade:', trade_db.print_info()
            continue
        position_db = position_dict[dict_key]
        qty = abs(int(trade_db.qty))
        if trade_db.qty > 0:  # 买
            position_db.day_long += qty
            position_db.day_long_cost = float(position_db.day_long_cost) + qty * float(trade_db.price) * float(
                instrument_db.fut_val_pt)
        elif trade_db.qty < 0:  # 卖
            position_db.day_short += abs(qty)
            position_db.day_short_cost = float(position_db.day_short_cost) + abs(qty) * float(
                trade_db.price) * float(instrument_db.fut_val_pt)

    for (symbol, position_db) in position_dict.items():
        session_portfolio.merge(position_db)


def __calculation_position_ctp(account_db, trade_list):
    position_dict = dict()
    query_position = session_portfolio.query(Position)
    for position_db in query_position.filter(Position.id == account_db.accountid, Position.date == now_date_str):
        key = '%s|%s' % (position_db.symbol, position_db.hedgeflag)
        position_dict[key] = position_db

    trade_list = sorted(trade_list, cmp=lambda x, y: cmp(x.time, y.time), reverse=False)
    for trade_info in trade_list:
        instrument_db = instrument_dict[trade_info.symbol]

        dict_key = '%s|%s' % (trade_info.symbol, trade_info.hedgeflag)
        if dict_key not in position_dict:
            print 'error trade:', trade_info.print_info()
            continue
        position_db = position_dict[dict_key]

        qty = abs(int(trade_info.qty))

        if trade_info.qty > 0:  # 买
            if trade_info.type == 'OPEN':  # 开仓
                position_db.td_buy_long += qty
            elif trade_info.type == 'CLOSE':  # 平仓
                a = min(qty, position_db.td_sell_short)
                position_db.yd_short_remain -= max(qty - position_db.td_sell_short, 0)
                position_db.td_sell_short -= a
            elif trade_info.type == 'CLOSE_YESTERDAY':  # 平昨
                position_db.yd_short_remain -= qty

            position_db.day_long += qty
            position_db.day_long_cost = float(position_db.day_long_cost) + qty * float(trade_info.price) * float(instrument_db.fut_val_pt)
        elif trade_info.qty < 0:  # 卖
            if trade_info.type == 'OPEN':  # 开仓
                position_db.td_sell_short += qty
            elif trade_info.type == 'CLOSE':  # 平仓
                a = min(qty, position_db.td_buy_long)
                position_db.yd_long_remain -= max(qty - position_db.td_buy_long, 0)
                position_db.td_buy_long -= a
            elif trade_info.type == 'CLOSE_YESTERDAY':  # 平昨
                position_db.yd_long_remain -= qty

            position_db.day_short += abs(qty)
            position_db.day_short_cost = float(position_db.day_short_cost) + abs(qty) * float(trade_info.price) * float(instrument_db.fut_val_pt)

    for (symbol, position_db) in position_dict.items():
        session_portfolio.merge(position_db)


def __calculation_position_lts(account_db, trade_list):
    trade_dict = dict()
    for trade_db in trade_list:
        if trade_db.symbol in trade_dict:
            trade_dict[trade_db.symbol].append(trade_db)
        else:
            trade_dict[trade_db.symbol] = [trade_db]

    query_position = session_portfolio.query(Position)
    for position_db in query_position.filter(Position.id == account_db.accountid, Position.date == now_date_str):
        if position_db.symbol not in trade_dict:
            continue
        if position_db.symbol not in instrument_dict:
            continue

        trade_list = trade_dict[position_db.symbol]
        trade_list = sorted(trade_list, cmp=lambda x, y: cmp(x.time, y.time), reverse=False)


        instrument_db = instrument_dict[position_db.symbol]
        if instrument_db.type_id == 16:
            l1r1 = position_db.yd_position_long
            l0r1 = 0
            l1r0 = 0
            for trade_db in trade_list:
                qty = abs(trade_db.qty)
                direction = trade_db.direction
                if direction == 'N':
                    if (instrument_db.tranche == 'A') or (instrument_db.tranche == 'B'):
                        l1r0 += qty
                    else:
                        a = min(l0r1, qty)
                        l0r1 -= a
                        l1r1 -= max(qty - a, 0)
                elif direction == '0':
                    l0r1 += qty
                elif direction == 'O':
                    if (instrument_db.tranche == 'A') or (instrument_db.tranche == 'B'):
                        a = min(l0r1, qty)
                        l0r1 -= a
                        l1r1 -= max(qty - a, 0)
                    else:
                        l1r0 += qty
                elif direction == '1':
                    a = min(l1r0, qty)
                    l1r0 -= a
                    l1r1 -= max(qty - a, 0)
                # print 'l1r1:', l1r1, 'l0r1:', l0r1, 'l1r0:', l1r0
            purchase_avail = l1r1 + l0r1
            long_avail = l1r1 + l1r0
            position_db.long_avail = long_avail
            position_db.purchase_avail = purchase_avail
        else:
            creation_redemption_unit = 1
            if (instrument_db.pcf is not None) and ('CreationRedemptionUnit' in instrument_db.pcf):
                pcf_dict = json.loads(instrument_db.pcf)
                creation_redemption_unit = int(pcf_dict['CreationRedemptionUnit'])

            l1r1 = position_db.yd_position_long
            l0r1 = 0
            l1r0 = 0
            for trade_db in trade_list:
                qty = abs(trade_db.qty)
                direction = trade_db.direction
                if direction == '2':
                    qty *= creation_redemption_unit
                    l1r0 += qty
                elif direction == '0':
                    l0r1 += qty
                elif direction == '3':
                    qty *= creation_redemption_unit
                    a = min(l0r1, qty)
                    l0r1 -= a
                    l1r1 -= max(qty - a, 0)
                elif direction == '1':
                    a = min(l1r0, qty)
                    l1r0 -= a
                    l1r1 -= max(qty - a, 0)
            purchase_avail = l1r1 + l0r1
            long_avail = l1r1 + l1r0
            if (position_db.yd_position_long > 0) and (long_avail >= 0):
                position_db.long_avail = long_avail
                position_db.purchase_avail = purchase_avail
            else:
                position_db.short_avail = position_db.yd_position_short - purchase_avail
                position_db.purchase_avail = purchase_avail

        for trade_db in trade_list:
            if trade_db.qty > 0:  # 买
                position_db.day_long += qty
                position_db.day_long_cost = float(position_db.day_long_cost) + qty * float(trade_db.price) * float(
                    instrument_db.fut_val_pt)
            elif trade_db.qty < 0:  # 卖
                position_db.day_short += abs(qty)
                position_db.day_short_cost = float(position_db.day_short_cost) + abs(qty) * float(
                    trade_db.price) * float(instrument_db.fut_val_pt)
        session_portfolio.merge(position_db)


def __get_start_end_date():
    now_time = long(now.strftime('%H%M%S'))
    if (80000 < now_time < 190000) or (0 < now_time < 30000):
        last_trading_day = DateUtils().get_last_trading_day('%Y-%m-%d', now_date_str)
        start_date = last_trading_day + ' 20:30:00'
    else:
        start_date = now_date_str + ' 20:30:00'
    end_date = now.strftime('%Y-%m-%d %H:%M:%S')
    return start_date, end_date


def __get_trade_list(account_db):
    trade_list = []
    (start_date, end_date) = __get_start_end_date()

    query = session_om.query(Trade)
    for trade_db in query.filter(Trade.account == account_db.accountid,
                                 Trade.time >= start_date,
                                 Trade.time <= end_date).order_by(Trade.trade_id):
        trade_list.append(trade_db)
    return trade_list


def __rebuild_trade_type_ctp(trade_list):
    for trade_db in trade_list:
        instrument_db = instrument_dict[trade_db.symbol]
        if instrument_db.type_id == 1 or instrument_db.type_id == 10:
            if trade_db.offsetflag == '0':
                trade_db.type = 'OPEN'  # OPEN
            elif trade_db.offsetflag == '1' or trade_db.offsetflag == '2' or trade_db.offsetflag == '3':
                trade_db.type = 'CLOSE'  # CLOSE
            elif trade_db.offsetflag == '4':
                trade_db.type = 'CLOSE_YESTERDAY'  # CLOSE_YESTERDAY
        else:
            trade_db.type = 'NORMAL' #NORMAL
        session_om.merge(trade_db)


def __rebuild_trade_type_femas(trade_list):
    for trade_db in trade_list:
        instrument_db = instrument_dict[trade_db.symbol]
        if instrument_db.type_id == 1 or instrument_db.type_id == 10:
            if trade_db.offsetflag == '0':
                trade_db.type = 'OPEN'  # OPEN
            elif trade_db.offsetflag == '1' or trade_db.offsetflag == '2' or trade_db.offsetflag == '3':
                trade_db.type = 'CLOSE'  # CLOSE
            elif trade_db.offsetflag == '4':
                trade_db.type = 'CLOSE_YESTERDAY'  # CLOSE_YESTERDAY
        else:
            trade_db.type = 'NORMAL' #NORMAL
        session_om.merge(trade_db)


def __rebuild_trade_type_lts(trade_list):
    for trade_db in trade_list:
        if trade_db.symbol not in instrument_dict:
            continue

        instrument_db = instrument_dict[trade_db.symbol]
        if trade_db.direction == '0': # 买
            if instrument_db.type_id == 1 or instrument_db.type_id == 10:
                if trade_db.offsetflag == '0':
                    trade_db.type = 'OPEN'  # OPEN
                elif trade_db.offsetflag == '1' or trade_db.offsetflag == '2' or trade_db.offsetflag == '3':
                    trade_db.type = 'CLOSE'  # CLOSE
                elif trade_db.offsetflag == '4':
                    trade_db.type = 'CLOSE_YESTERDAY'  # CLOSE_YESTERDAY
            else:
                trade_db.type = 'NORMAL'
        elif trade_db.direction == '1': # 卖
            trade_db.qty = -trade_db.qty
            if instrument_db.type_id == 1 or instrument_db.type_id == 10:
                if trade_db.offsetflag == '0':
                    trade_db.type = 'OPEN'  # OPEN
                elif trade_db.offsetflag == '1' or trade_db.offsetflag == '2' or trade_db.offsetflag == '3':
                    trade_db.type = 'CLOSE'  # CLOSE
                elif trade_db.offsetflag == '4':
                    trade_db.type = 'CLOSE_YESTERDAY'  # CLOSE_YESTERDAY
            else:
                trade_db.type = 'NORMAL'
        elif trade_db.direction == '2': # ETF申购
            trade_db.type = 'RedPur'
        elif trade_db.direction == '3': # ETF赎回
            trade_db.qty = -trade_db.qty
            trade_db.type = 'RedPur'
        elif trade_db.direction == 'N': # SF拆分
            if instrument_db.tranche is None or instrument_db.tranche == '': # 母基金
                trade_db.qty = -trade_db.qty
                trade_db.type = 'MergeSplit'
            elif instrument_db.tranche == 'A' or instrument_db.tranche == 'B': # 子基金
                trade_db.type = 'MergeSplit'
        elif trade_db.direction == 'O': # SF合并
            if instrument_db.tranche is None or instrument_db.tranche == '': # 母基金
                trade_db.type = 'MergeSplit'
            elif instrument_db.tranche == 'A' or instrument_db.tranche == 'B': # 子基金
                trade_db.qty = -trade_db.qty
                trade_db.type = 'MergeSplit'
        session_om.merge(trade_db)


def __rebuild_trade_type():
    query = session_portfolio.query(Account)
    for account_db in query:
        trade_list = __get_trade_list(account_db)
        if account_db.accounttype == 'CTP':
            __rebuild_trade_type_ctp(trade_list)
            __calculation_position_ctp(account_db, trade_list)
        if account_db.accounttype == 'HUABAO':
            __rebuild_trade_type_lts(trade_list)
            __calculation_position_lts(account_db, trade_list)
        if account_db.accounttype == 'FEMAS':
            __rebuild_trade_type_femas(trade_list)
            __calculation_position_femas(account_db, trade_list)


if __name__ == '__main__':
    print 'Enter rebuild_trade_calculation_position.'
    host_server_model = ServerConstant().get_server_model('host')
    session_common = host_server_model.get_db_session('common')
    session_portfolio = host_server_model.get_db_session('portfolio')
    session_om = host_server_model.get_db_session('om')

    __build_instrument_dict()
    __rebuild_trade_type()
    session_om.commit()
    session_portfolio.commit()
    print 'Exit rebuild_trade_calculation_position.'