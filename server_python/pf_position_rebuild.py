# -*- coding: utf-8 -*-
# 每日3点后更新pf_position表数据，重新创建明日数据，并进行赋值long->long_avail->yd_positong_long->yd_long_remain
import sys
import MySQLdb
import datetime

from tools.date_utils import DateUtils
from tools.getConfig import getConfig

d1 = datetime.datetime.now()
todayStr = d1.strftime('%Y-%m-%d')
next_day_str = DateUtils().get_next_trading_day('%Y-%m-%d')

if __name__ == '__main__':
    print 'Enter pf_position_rebuild.py'
    cfg_dict = getConfig()
    try:
        conn = MySQLdb.connect( \
            host=cfg_dict['host'], user=cfg_dict['user'], passwd=cfg_dict['password'], \
            port=int(cfg_dict['db_port']), db='common', charset='utf8')
    except Exception, e:
        print e
        sys.exit(-1)

    cursor = conn.cursor()
    if next_day_str == '':
        sys.exit()

    del_sql = 'delete from portfolio.pf_position where date = %s'
    del_param = (next_day_str,)
    execute = cursor.execute(del_sql, del_param)

    insert_sql = """INSERT INTO `portfolio`.`pf_position` (
    `DATE`,
    `ID`,
    `SYMBOL`,
    `HEDGEFLAG`,
    `LONG`,
    `LONG_COST`,
    `LONG_AVAIL`,
    `SHORT`,
    `SHORT_COST`,
    `SHORT_AVAIL`,
    `CLOSE_PRICE`,
    `NOTE`,
    `DELTA`,
    `GAMMA`,
    `THETA`,
    `VEGA`,
    `RHO`,
    `YD_POSITION_LONG`,
    `YD_POSITION_SHORT`,
    `YD_LONG_REMAIN`,
    `YD_SHORT_REMAIN`,
    `PREV_NET`,
    `PURCHASE_AVAIL`,
    `LONGFROZEN`,
    `SHORTFROZEN`,
    `UPDATE_DATE`
)
select 
    %s,
    `ID`,
    `SYMBOL`,
    `HEDGEFLAG`,
    `LONG`,
    `LONG_COST`,
    `LONG_AVAIL`,
    `SHORT`,
    `SHORT_COST`,
    `SHORT_AVAIL`,
    `CLOSE_PRICE`,
    `NOTE`,
    `DELTA`,
    `GAMMA`,
    `THETA`,
    `VEGA`,
    `RHO`,
    `YD_POSITION_LONG`,
    `YD_POSITION_SHORT`,
    `YD_LONG_REMAIN`,
    `YD_SHORT_REMAIN`,
    `PREV_NET`,
    `PURCHASE_AVAIL`,
    `LONGFROZEN`,
    `SHORTFROZEN`,
    `UPDATE_DATE`
from  portfolio.pf_position t where t.date=%s"""
    insert_param = (next_day_str, todayStr)
    execute = cursor.execute(insert_sql, insert_param)
    if execute > 0:
        print 'insert number:', execute

    query_sql = 'SELECT t.id,t.SYMBOL,t.`LONG`,t.`LONG_COST`,t.`SHORT`,t.`SHORT_COST` FROM portfolio.pf_position t where t.DATE = %s'
    query_param = (next_day_str,)
    execute = cursor.execute(query_sql, query_param)
    for row in cursor.fetchall():
        account_id = row[0]
        ticker = row[1]
        long_value = float(row[2])
        long_cost_value = float(row[3])
        short_value = float(row[4])
        short_cost_value = float(row[5])
        if long_value == short_value:
            if ticker == 'CNY':
                continue
            update_sql = 'delete from portfolio.pf_position where DATE = %s and ID = %s and SYMBOL=%s'
            update_param = (next_day_str, account_id, ticker)
        elif long_value > short_value:
            long_remain = long_value - short_value
            long_cost = long_cost_value - short_cost_value
            update_sql = 'update portfolio.pf_position t set t.`LONG`=%s,t.`LONG_COST`=%s,t.LONG_AVAIL=%s,\
t.YD_POSITION_LONG=%s,t.YD_LONG_REMAIN=%s,t.`SHORT`=0, t.SHORT_COST = 0,t.SHORT_AVAIL=0,t.YD_POSITION_SHORT=0,\
t.YD_SHORT_REMAIN=0 where t.DATE = %s and t.ID = %s and t.SYMBOL=%s'
            update_param = (long_remain, long_cost, long_remain, long_remain, long_remain, next_day_str, account_id, ticker)
        else:
            short_remain = short_value - long_value
            short_cost = short_cost_value - long_cost_value
            update_sql = 'update portfolio.pf_position t set t.`LONG`=0,t.`LONG_COST`=0,t.LONG_AVAIL=0,\
t.YD_POSITION_LONG=0,t.YD_LONG_REMAIN=0,t.`SHORT`=%s, t.SHORT_COST=%s,t.SHORT_AVAIL=%s,t.YD_POSITION_SHORT=%s,t.YD_SHORT_REMAIN=%s \
where t.DATE = %s and t.ID = %s and t.SYMBOL=%s'
            update_param = (short_remain, short_cost, short_remain, short_remain, short_remain, next_day_str, account_id, ticker)

        execute = cursor.execute(update_sql, update_param)

    update_sql = 'update portfolio.pf_position t set t.YD_POSITION_LONG = t.YD_LONG_REMAIN, t.YD_POSITION_SHORT = t.YD_SHORT_REMAIN where t.DATE = %s'
    update_param = (todayStr,)
    cursor.execute(update_sql, update_param)

    update_sql = 'update portfolio.pf_position t set t.PREV_NET = t.YD_POSITION_LONG - t.YD_POSITION_SHORT where t.DATE = %s'
    update_param = (next_day_str,)
    cursor.execute(update_sql, update_param)
    cursor.close()
    conn.commit()
    conn.close()
    print 'Exit pf_position_rebuild.py'