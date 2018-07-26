# -*- coding: utf-8 -*-
from datetime import datetime
from model.BaseModel import *
from model.server_constans import ServerConstant
from tools.getConfig import getConfig
from tools.file_utils import FileUtils
from model.order2 import Order2
from model.trade2 import Trade2
from model.position import Position
from model.account import Account
from model.eod_const import const

today_str = datetime.now().strftime('%Y-%m-%d')
file_path = getConfig()['datafetcher_file_path']

order_list = []
trade_list = []
position_list = []


def read_position_file_lts(lts_file_path):
    print 'Start read file:' + lts_file_path
    fr = open(lts_file_path)
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
                setattr(base_model, temp_array[0].strip(), temp_array[1])
            if 'OnRspQryOrder' in line:
                order_array.append(base_model)
            elif 'OnRspQryTrade' in line:
                trade_array.append(base_model)
            elif 'OnRspQryTradingAccount' in line:
                trading_account_array.append(base_model)
            elif 'OnRspQryInvestorPosition' in line:
                investor_position_array.append(base_model)

    print 'AccountID:', account_id
    account_info = get_account_info(account_id)
    # 删除该账号今日记录
    del_account_position_by_id(account_id)
    del_order_trader_by_id(account_id)

    save_order(account_id, order_array)
    save_trade(account_info, trade_array)

    save_account_cny(account_info, trading_account_array)
    save_account_position(account_info, investor_position_array)


def get_account_info(account_id):
    account_info = session_portfolio.query(Account).filter(Account.accountid == account_id).first()
    return account_info


def del_account_position_by_id(account_id):
    del_sql = "delete from portfolio.account_position where ID= '%s' and DATE ='%s'" % (account_id, today_str)
    session_portfolio.execute(del_sql)


def del_order_trader_by_id(account_id):
    del_sql = "delete from om.order_broker where ACCOUNT=%s and INSERT_TIME LIKE '%s'" % (account_id, today_str + '%')
    session_om.execute(del_sql)

    del_sql = "delete from om.trade2_broker where ACCOUNT=%s and TIME LIKE '%s'" % (account_id, today_str + '%')
    session_om.execute(del_sql)


def build_time_db(insert_date_str, insert_time_str):
    if (insert_date_str != 'NULL') and (insert_time_str != 'NULL'):
        time_db = '%s-%s-%s %s' % (insert_date_str[0:4], insert_date_str[4:6], \
                                   insert_date_str[6:8], insert_time_str)
    else:
        time_db = '%s 00:00:00' % (today_str,)
    return time_db


def save_order(account_id, order_array):
    for order_info in order_array:
        order_db = Order()
        order_db.sys_id = getattr(order_info, 'OrderSysID', '').strip()
        order_db.account = account_id
        order_db.symbol = getattr(order_info, 'InstrumentID', '')

        # LTS定义：买:'0'|卖:'1'|ETF申购:'2'|ETF赎回:'3'|现金替代，只用作回报: '4'|债券入库:'5'|债券出库:'6'|配股:'7'|转托管:'8'
        # |信用账户配股:'9'|担保品买入:'A'|担保品卖出:'B'|担保品转入:'C'|担保品转出:'D'|融资买入:'E'|融券卖出:'F'|卖券还款:'G'
        # |买券还券:'H'|直接还款:'I'|直接还券:'J'|余券划转:'K'|OF申购:'L'|OF赎回:'M'|SF拆分:'N'|SF合并:'O'|备兑:'P'
        # |证券冻结(开)/解冻(平):'Q'|行权:'R'|CB回售:'S'|CB转股:'T'|OF认购:'U'
        order_db.direction = getattr(order_info, 'Direction', '')

        order_db.trade_type = getattr(order_info, 'CombOffsetFlag', '')

        # 全部成交:'0'|部分成交还在队列中:'1'|部分成交不在队列中:'2'|未成交还在队列中:'3'|未成交不在队列中:'4'|撤单:'5'
        # |未知:'a'|尚未触发:'b'|已触发:'c'
        order_db.status = getattr(order_info, 'OrderStatus', '')
        order_db.submit_status = getattr(order_info, 'OrderSubmitStatus', '')

        insert_date_str = getattr(order_info, 'InsertDate', '')
        insert_time_str = getattr(order_info, 'InsertTime', '')
        order_db.insert_time = build_time_db(insert_date_str, insert_time_str)

        order_db.qty = getattr(order_info, 'VolumeTotalOriginal', '')
        order_db.price = getattr(order_info, 'LimitPrice', '')
        order_db.ex_qty = getattr(order_info, 'VolumeTraded', '')
        order_list.append(order_db)


def save_trade(account_info, trade_array):
    for trade_info in trade_array:
        trade_db = Trade()
        trade_db.trade_id = getattr(trade_info, 'TradeID', '').strip()

        trade_date = getattr(trade_info, 'TradeDate', '')
        trade_time = getattr(trade_info, 'TradeTime', '')
        trade_db.time = build_time_db(trade_date, trade_time)

        trade_db.symbol = getattr(trade_info, 'InstrumentID', '')
        trade_db.qty = getattr(trade_info, 'Volume', '')
        trade_db.price = getattr(trade_info, 'Price', '')
        # 普通成交:'0'|期权执行:'1'|OTC成交:'2'|期转现衍生成交:'3'|组合衍生成交:'4'|ETF申购:'5'|ETF赎回:'6'
        trade_db.trade_type = getattr(trade_info, 'TradeType', '')

        trade_db.account = account_info.accountid
        trade_db.order_id = getattr(trade_info, 'OrderSysID', '')
        # LTS定义：买:'0'|卖:'1'|ETF申购:'2'|ETF赎回:'3'|现金替代，只用作回报: '4'|债券入库:'5'|债券出库:'6'|配股:'7'|转托管:'8'
        # |信用账户配股:'9'|担保品买入:'A'|担保品卖出:'B'|担保品转入:'C'|担保品转出:'D'|融资买入:'E'|融券卖出:'F'|卖券还款:'G'
        # |买券还券:'H'|直接还款:'I'|直接还券:'J'|余券划转:'K'|OF申购:'L'|OF赎回:'M'|SF拆分:'N'|SF合并:'O'|备兑:'P'
        # |证券冻结(开)/解冻(平):'Q'|行权:'R'|CB回售:'S'|CB转股:'T'|OF认购:'U'
        trade_db.direction = getattr(trade_info, 'Direction', '')

        # 开仓:'0'|平仓:'1'|强平:'2'|平今:'3'|平昨:'4'|强减:'5'|本地强平:'6'
        trade_db.offsetflag = getattr(trade_info, 'OffsetFlag', '')

        hedge_flag = getattr(trade_info, 'HedgeFlag', '1').strip()
        if hedge_flag == '':
            trade_db.hedgeflag = '0'
        else:
            trade_db.hedgeflag = const.HEDGE_FLAG_MAP[hedge_flag]
        trade_list.append(trade_db)


def save_account_cny(account_info, message_array):
    for tradingAccount in message_array:
        position_db = Position()
        real_account_id = getattr(tradingAccount, 'AccountID', 'NULL');
        if (real_account_id[12:14] == '70') and (account_info.accountsuffix == '70'):
            pass
        elif (real_account_id[12:14] == '01') and (account_info.accountsuffix == '01'):
            pass
        else:
            continue

        position_db.date = today_str
        position_db.id = account_info.accountid
        position_db.symbol = 'CNY'
        # 结算准备金
        position_db.long = getattr(tradingAccount, 'Balance', 'NULL')

        if account_info.accountsuffix == '70':
            # 保证金可用余额
            position_db.long_avail = getattr(tradingAccount, 'Credit', 'NULL')
        else:
            # 现金
            position_db.long_avail = getattr(tradingAccount, 'Available', 'NULL')

        # 上次结算准备金
        position_db.prev_net = getattr(tradingAccount, 'PreBalance', '0')
        position_db.update_date = datetime.now()
        position_list.append(position_db)


def save_account_position(account_info, investor_position_array):
    tick_position_dict = dict()
    for investor_position in investor_position_array:
        symbol = getattr(investor_position, 'InstrumentID', 'NULL')

        # 投机:'1'|套保:'3'
        # hedge_flag = getattr(investor_position, 'HedgeFlag', '0')
        # hedge_flag = const.HEDGE_FLAG_MAP[hedge_flag]
        hedge_flag = 0

        key = '%s|%s' % (symbol, hedge_flag)
        if key in tick_position_dict:
            tick_position_dict.get(key).append(investor_position)
        else:
            tick_position_dict[key] = [investor_position]

    for (key, tickPositionList) in tick_position_dict.items():
        (symbol, hedge_flag) = key.split('|')

        td_long = 0
        td_long_cost = 0.0
        td_long_avail = 0

        td_short = 0
        td_short_cost = 0.0
        td_short_avail = 0

        yd_long = 0
        yd_long_remain = 0

        yd_short = 0
        yd_short_remain = 0

        prev_net = 0
        purchase_avail = 0

        long_frozen = 0
        short_frozen = 0

        save_flag = False
        for position_message in tickPositionList:
            real_account_id = getattr(position_message, 'AccountID', 'NULL')
            if (real_account_id[12:14] == '70') and (account_info.accountsuffix == '70'):
                save_flag = True
            elif (real_account_id[12:14] == '01') and (account_info.accountsuffix == '01'):
                save_flag = True
            else:
                continue

            position = float(getattr(position_message, 'Position', '0'))
            positionCost = float(getattr(position_message, 'PositionCost', '0'))
            ydPosition = float(getattr(position_message, 'YdPosition', '0'))

            # todayPurRedVolume = getattr(position_message, 'TodayPurRedVolume', '0')
            # todayPosition = getattr(position_message, 'TodayPosition', '0')
            openVolume = float(getattr(position_message, 'OpenVolume', '0'))
            closeVolume = float(getattr(position_message, 'CloseVolume', '0'))
            long_frozen = getattr(position_message, 'LongFrozen', '0')
            short_frozen = getattr(position_message, 'ShortFrozen', '0')

            long_flag = True
            # 净:'1'|多头:'2'|空头:'3'|备兑:'4'
            posi_direction = getattr(position_message, 'PosiDirection', '0')
            if posi_direction == '2':
                long_flag = True
            elif posi_direction == '3':
                long_flag = False
            elif (posi_direction == '1') and (ydPosition < 0):
                long_flag = False
            elif (posi_direction == '1') and (ydPosition >= 0):
                long_flag = True
            else:
                print 'Error in OnRspQryInvestorPosition'

            if long_flag:
                td_long = position
                td_long_cost = positionCost
                yd_long = ydPosition
                if (ydPosition - closeVolume) > 0:
                    yd_long_remain = ydPosition - closeVolume
                else:
                    yd_long_remain = 0
            else:
                td_short = abs(position)
                td_short_cost = abs(positionCost)
                yd_short = abs(ydPosition)
                if (abs(ydPosition) - openVolume) > 0:
                    yd_short_remain = abs(ydPosition) - openVolume
                else:
                    yd_short_remain = 0

        if save_flag:
            td_long_avail = yd_long
            td_short_avail = yd_short

            purchase_avail = yd_long
            prev_net = int(yd_long) - int(yd_short)

            position_db = Position()
            position_db.date = today_str
            position_db.id = account_info.accountid
            position_db.symbol = symbol
            position_db.hedgeflag = hedge_flag
            position_db.long = td_long
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
            position_db.purchase_avail = purchase_avail
            position_db.frozen = long_frozen
            position_db.update_date = datetime.now()
            position_list.append(position_db)


def update_db():
    for order_db in order_list:
        session_om.add(order_db)
    for trade_db in trade_list:
        session_om.add(trade_db)
    for position_db in position_list:
        session_portfolio.add(position_db)


if __name__ == '__main__':
    print 'Enter Lts_position_analysis.'
    host_server_model = ServerConstant().get_server_model('host')
    session_portfolio = host_server_model.get_db_session('portfolio')
    session_om = host_server_model.get_db_session('om')

    lts_position_file_list = FileUtils(file_path).filter_file('HUABAO_POSITION', today_str)
    for lts_file in lts_position_file_list:
        read_position_file_lts('%s/%s' % (file_path, lts_file))

    update_db()
    session_portfolio.commit()
    session_om.commit()
    print 'Exit Lts_position_analysis.'
