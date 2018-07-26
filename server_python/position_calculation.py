# -*- coding: utf-8-*-
# 根据trader数据计算lts各账户的LONG_AVAIL和purchase_avail

import sys
import MySQLdb
import datetime
import json
from tools.getConfig import getConfig

now = datetime.datetime.now()
todayStr = now.strftime('%Y-%m-%d')


def baseCalculation(account_id, ticker, yd_long, yd_short, creationRedemptionUnit):
    query_sql = "select qty,direction from om.trade2_broker where time like %s and account = %s and symbol = %s"
    query_param = ('%' + todayStr + '%', account_id, ticker)
    cursor.execute(query_sql, query_param)

    l1r1 = yd_long
    l0r1 = 0
    l1r0 = 0
    for traderItem in cursor.fetchall():
        qty = traderItem[0]
        direction = traderItem[1]
        if direction == '2':
            qty = qty * creationRedemptionUnit
            l1r0 += qty
        elif direction == '0':
            l0r1 += qty
        elif direction == '3':
            qty = qty * creationRedemptionUnit
            a = min(l0r1, qty)
            l0r1 -= a
            l1r1 -= max(qty - a, 0)
        elif direction == '1':
            a = min(l1r0, qty)
            l1r0 -= a
            l1r1 -= max(qty - a, 0)
    redpuravail = l1r1 + l0r1
    longavail = l1r1 + l1r0

    if (yd_long > 0) and (longavail >= 0):
        print 'account_id:', account_id, 'ticker:', ticker, 'longavail:', longavail, 'redpuravail', redpuravail
        update_sql = "update portfolio.account_position t set t.LONG_AVAIL=%s,t.purchase_avail=%s where t.DATE = %s and t.id = %s and SYMBOL = %s"
        update_param = (longavail, redpuravail, todayStr, account_id, ticker)
    else:
        shortavail = yd_short - redpuravail
        update_sql = "update portfolio.account_position t set t.SHORT_AVAIL=%s,t.purchase_avail=%s where t.DATE = %s and t.id = %s and SYMBOL = %s"
        update_param = (shortavail, redpuravail, todayStr, account_id, ticker)
    cursor.execute(update_sql, update_param)


def structuredFundCalculation(account_id, ticker, yd_long, ticker_tranche):
    query_sql = "select qty,direction from om.trade2_broker where time like %s and account = %s and symbol = %s"
    query_param = ('%' + todayStr + '%', account_id, ticker)
    cursor.execute(query_sql, query_param)

    print 'account_id:', account_id, ',ticker:', ticker, ',yd_position:', yd_long
    l1r1 = yd_long
    l0r1 = 0
    l1r0 = 0
    for traderItem in cursor.fetchall():
        qty = traderItem[0]
        direction = traderItem[1]
        if direction == 'N':
            if (ticker_tranche == 'A') or (ticker_tranche == 'B'):
                l1r0 += qty
            else:
                a = min(l0r1, qty)
                l0r1 -= a;
                l1r1 -= max(qty - a, 0)
        elif direction == '0':
            l0r1 += qty
        elif direction == 'O':
            if (ticker_tranche == 'A') or (ticker_tranche == 'B'):
                a = min(l0r1, qty)
                l0r1 -= a;
                l1r1 -= max(qty - a, 0)
            else:
                l1r0 += qty
        elif direction == '1':
            a = min(l1r0, qty)
            l1r0 -= a;
            l1r1 -= max(qty - a, 0)
        print  'l1r1:', l1r1, 'l0r1:', l0r1, 'l1r0:', l1r0
    redpuravail = l1r1 + l0r1
    longavail = l1r1 + l1r0
    print 'account_id:', account_id, 'longavail:', longavail, 'redpuravail', redpuravail, '\n'
    update_sql = "update portfolio.account_position t set t.LONG_AVAIL=%s,t.purchase_avail=%s where t.DATE = %s and t.id = %s and SYMBOL = %s"
    update_param = (longavail, redpuravail, todayStr, account_id, ticker)
    cursor.execute(update_sql, update_param)


if __name__ == '__main__':
    cfg_dict = getConfig()
    try:
        conn = MySQLdb.connect( \
            host=cfg_dict['host'], user='admin', passwd='adminP@ssw0rd', \
            db='common', charset='utf8')
        print 'db ip:', cfg_dict['host']
    except Exception, e:
        print e
        sys.exit()
    cursor = conn.cursor()

    #     update_sql = "update om.trade2_broker t, om.order_broker o  set t.TIME = o.INSERT_TIME where t.ORDER_ID = o.sys_id and t.Direction in ('O','N') and o.INSERT_TIME like %s"
    #     update_param = (todayStr + '%',)
    #     cursor.execute(update_sql, update_param)

    query_sql = 'select id,symbol,yd_position_long,yd_position_short from portfolio.account_position t where t.DATE = %s'
    query_param = (todayStr,)
    cursor.execute(query_sql, query_param)
    for h in cursor.fetchall():
        account_id = h[0]
        ticker = h[1]
        yd_long = h[2]
        yd_short = h[3]
        if ticker == 'CNY':
            continue

        query_sql = 'select AccountType from portfolio.real_account where AccountID = %s'
        query_param = (account_id,)
        cursor.execute(query_sql, query_param)
        accountType = cursor.fetchone()[0]
        if accountType != 'HUABAO':
            continue

        # 申赎单位
        creationRedemptionUnit = 1
        query_sql = 'select pcf,type_id,tranche from common.instrument where ticker =%s'
        query_param = (ticker,)
        cursor.execute(query_sql, query_param)
        tickerItem = cursor.fetchone()
        if tickerItem is None:
            continue

        pcf = tickerItem[0]
        ticker_type = tickerItem[1]
        ticker_tranche = tickerItem[2]
        if (pcf is not None) and ('CreationRedemptionUnit' in pcf):
            pcfDict = json.loads(pcf)
            creationRedemptionUnit = int(pcfDict['CreationRedemptionUnit'])
            # 单独处理分级基金
        if ticker_type == 16:
            structuredFundCalculation(account_id, ticker, yd_long, ticker_tranche)
        else:
            baseCalculation(account_id, ticker, yd_long, yd_short, creationRedemptionUnit)

    cursor.close()
    conn.commit()
    conn.close()
