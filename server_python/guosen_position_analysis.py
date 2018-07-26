# -*- coding: utf-8 -*-
from datetime import datetime
from model.BaseModel import *
from model.server_constans import ServerConstant
from tools.getConfig import getConfig
from tools.file_utils import FileUtils
from model.position import Position

now = datetime.now()
today_str = now.strftime('%Y-%m-%d')
file_path = getConfig()['datafetcher_file_path']

order_list = []
trade_list = []
position_list = []


def read_position_file_guosen(guosen_file_path):
    print 'Start read file:' + guosen_file_path
    fr = open(guosen_file_path)
    trading_account_array = []
    investor_position_array = []
    for line in fr.readlines():
        if 'Account_ID' in line:
            account_id = line.replace('\n', '').split(':')[1]
        else:
            base_model = BaseModel()
            item_array = line.split('|')[1].split('')
            for i in range(0, len(item_array)):
                if i == len(item_array) - 1:
                    continue
                item = item_array[i].split('=', 1)
                if item[0] == '702':
                    group = []
                    cross_size = int(item[1])
                    for j in range(0, cross_size):
                        group.append('%s|%s' % (item_array[i + 1 + 2 * j], item_array[i + 2 + 2 * j]))
                    setattr(base_model, 'GroupA', group)
                    i += cross_size
                elif item[0] == '753':
                    group = []
                    cross_size = int(item[1])
                    for j in range(0, cross_size):
                        group.append('%s|%s' % (item_array[i + 1 + 2 * j], item_array[i + 2 + 2 * j]))
                    setattr(base_model, 'GroupB', group)
                    i += cross_size
                else:
                    setattr(base_model, item[0].strip(), item[1])

            msg_type = getattr(base_model, '35', '0')
            if msg_type == 'UAP':
                posReqType = getattr(base_model, '724', '0')
                posReqResult = getattr(base_model, '728', '0')
                if posReqResult != '0':
                    print 'The returned message is wrong:', line
                    continue

                if posReqType == '9':
                    trading_account_array.append(base_model)  # 资金
                elif posReqType == '0':
                    investor_position_array.append(base_model)  # 股份

    # 删除该账号今日记录
    del_account_position_by_id(account_id)
    del_order_trader_by_id(account_id)
    save_account_cny(account_id, trading_account_array)
    save_account_position(account_id, investor_position_array)
    update_db()


def update_db():
    for order_db in order_list:
        session_om.add(order_db)
    for trade_db in trade_list:
        session_om.add(trade_db)
    for position_db in position_list:
        session_portfolio.add(position_db)


def del_account_position_by_id(account_id):
    del_sql = "delete from portfolio.account_position where ID= '%s' and DATE ='%s'" % (account_id, today_str)
    session_portfolio.execute(del_sql)


def del_order_trader_by_id(account_id):
    del_sql = "delete from om.order_broker where ACCOUNT=%s and INSERT_TIME LIKE '%s'" % (account_id, today_str + '%')
    session_om.execute(del_sql)

    del_sql = "delete from om.trade2_broker where ACCOUNT=%s and TIME LIKE '%s'" % (account_id, today_str + '%')
    session_om.execute(del_sql)


def save_account_cny(account_id, message_array):
    for trading_account in message_array:
        position_db = Position()
        position_db.date = today_str
        position_db.id = account_id
        position_db.symbol = getattr(trading_account, '15', '0')

        td_long = 0
        td_long_avail = 0
        group_array = getattr(trading_account, 'GroupB', '0')
        for group in group_array:
            (title_column, value_column) = group.split('|')
            title = title_column.split('=')[1]
            value = value_column.split('=')[1]
            if title == 'F':
                td_long = value
            elif title == 'FAV':
                td_long_avail = value
        position_db.long = td_long
        position_db.long_avail = td_long_avail
        position_db.prev_net = td_long
        position_db.update_date = datetime.now()
        position_list.append(position_db)


def save_account_position(account_id, investor_position_array):
    for investorPosition in investor_position_array:
        symbol = getattr(investorPosition, '55', '0')
        hedge_flag = 0

        td_long = 0
        td_long_cost = 0.0
        td_long_avail = 0

        yd_long = 0
        yd_long_remain = 0

        td_short = 0
        td_short_cost = 0.0
        td_short_avail = 0

        yd_short = 0
        yd_short_remain = 0

        prev_net = 0
        purchase_avail = 0

        long_Frozen = 0
        short_Frozen = 0

        purchase_avail = 0

        groupAArray = getattr(investorPosition, 'GroupA', '0')

        for group in groupAArray:
            (title_column, value_column) = group.split('|')
            title = title_column.split('=')[1]
            value = int(value_column.split('=')[1])
            if title == 'SQ':  # 当前拥股数
                td_long = value
            # elif (title == 'SB'): #股份余额
            #                 td_long = value
            #             elif (title == 'SBQ'): #今日买入数量
            #                 td_long = value
            elif title == 'SAV':  # 股份可用余额
                td_long_avail = value
                yd_long_remain = value
                purchase_avail = value
            elif title == 'LB':  # 昨日余额
                yd_long = value
            elif title == 'SS':  # 卖出冻结数
                long_Frozen += value
            elif title == 'SF':  # 人工冻结数
                long_Frozen += value

        groupBArray = getattr(investorPosition, 'GroupB', '0')
        for group in groupBArray:
            (title_column, value_column) = group.split('|')
            title = title_column.split('=')[1]
            value = value_column.split('=')[1]
            # if title == 'PC':  # 持仓成本
            #     td_long_cost = value
            if title == 'SMV':  # 持仓成本
                td_long_cost = value

        prev_net = yd_long - yd_short

        position_db = Position()
        position_db.date = today_str
        position_db.id = account_id
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
        position_db.frozen = long_Frozen
        position_db.update_date = datetime.now()
        position_list.append(position_db)


if __name__ == '__main__':
    print 'Enter guosen_position_analysis.'
    host_server_model = ServerConstant().get_server_model('host')
    session_portfolio = host_server_model.get_db_session('portfolio')
    session_om = host_server_model.get_db_session('om')

    guosen_position_file_list = FileUtils(file_path).filter_file('GUOXIN_POSITION', today_str)
    for guosen_file in guosen_position_file_list:
        read_position_file_guosen('%s/%s' % (file_path, guosen_file))

    session_portfolio.commit()
    session_om.commit()
    print 'Exit guosen_position_analysis.'
