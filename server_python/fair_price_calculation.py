# -*- coding: utf-8-*-
# 计算股票的fair_price = etf_price(当日)/etf_price(停牌日)*stock_price(停牌日)

import sys
import MySQLdb
import json
import datetime
from tools.getConfig import getConfig


def fair_price_calculation(cursor):
    update_sql = 'update common.instrument set fair_price= NULL where 1=1'
    cursor.execute(update_sql)

    query_sql = "SELECT ticker, pcf FROM common.instrument WHERE pcf != '' and type_id in ('7')"
    cursor.execute(query_sql)
    tickerEtfDict = dict()
    for h in cursor.fetchall():
        pcf = h[1]
        pcfDict = json.loads(pcf)
        if 'Components' not in pcfDict:
            continue
        stock_list = pcfDict['Components']

        for tickerDict in stock_list:
            ticker = tickerDict["Ticker"]
            allowCash = tickerDict["AllowCash"]
            # Filter Not Must Cash
            if (allowCash == 'Must'):
                continue

            if (tickerEtfDict.has_key(ticker)):
                tickerEtfDict[ticker].append(h[0])
            else:
                etfArray = []
                etfArray.append(h[0])
                tickerEtfDict[ticker] = etfArray
    print 'ETF Include Ticker Size:', len(tickerEtfDict)

    for (stock_ticker, tickerArray) in tickerEtfDict.items():
        query_sql = 'select inactive_date,prev_close from instrument where ticker = %s'
        query_param = (stock_ticker,)
        cursor.execute(query_sql, query_param)

        stockItem = cursor.fetchone()
        if (stockItem is not None) and (stockItem[0] is not None):
            d1 = stockItem[0]
            # etf取停牌日前一天的close
            d2 = d1 + datetime.timedelta(days=-1)
            inactive_date = d2.strftime('%Y-%m-%d')
            stock_prev_close = stockItem[1]
        else:
            continue

        #         print 'Suspension stock_ticker:', stock_ticker
        weight = 0
        size = 0
        for etf_ticker in tickerArray:
            query_sql = 'select prev_close from instrument where ticker = %s'
            query_param = (etf_ticker,)
            cursor.execute(query_sql, query_param)

            etfItem = cursor.fetchone()
            etf_prev_close = etfItem[0]

            query_sql = "select t.`close` from history.instrument_history_price t where t.ticker = %s and t.date <= %s order by t.date desc"
            query_param = (etf_ticker, inactive_date)
            cursor.execute(query_sql, query_param)
            hisItem = cursor.fetchone()
            if (hisItem != None):
                etf_prev_close_inactive = hisItem[0]
                weight += etf_prev_close / etf_prev_close_inactive
                size += 1
                if etf_prev_close / etf_prev_close_inactive > 1.5:
                    print 'etf_ticker:', etf_ticker, 'weight:', etf_prev_close / etf_prev_close_inactive, 'etf_prev_close:', etf_prev_close, 'etf_prev_close_inactive:', etf_prev_close_inactive
            else:
                print 'etf_ticker:%s inactive_date:%s unfind in history' % (etf_ticker, inactive_date)

        if size > 0:
            fair_price = weight / size * stock_prev_close
            update_sql = 'update common.instrument set fair_price=%s where ticker = %s'
            update_param = (fair_price, stock_ticker)
            cursor.execute(update_sql, update_param)
        else:
            print stock_ticker, '[ERROR] can not get fair_price\n'


if __name__ == '__main__':
    cfg_dict = getConfig()
    try:
        conn = MySQLdb.connect( \
            host=cfg_dict['host'], user=cfg_dict['user'], passwd=cfg_dict['password'], \
            db='common', charset='utf8')
        print 'db ip:', cfg_dict['host']
    except Exception, e:
        print e
        sys.exit()

    cursor = conn.cursor()
    fair_price_calculation(cursor)

    cursor.close()
    conn.commit()
    conn.close()
