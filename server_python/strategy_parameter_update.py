# -*- coding: utf-8 -*-
import sys
import os
import MySQLdb
from datetime import datetime
from model.BaseModel import *
import codecs
import json
from tools.getConfig import getConfig

now = datetime.now()
todayStr = now.strftime('%Y-%m-%d')
file_path = getConfig()['datafetcher_file_path']
baseIp = getConfig()['host']
total_cancel_times = '400'


def strategy_parameter_update(cursor):
    query_sql = "select `NAME` from  strategy.strategy_parameter t where name like 'CalendarMA%' group by `NAME`"
    cursor.execute(query_sql)

    strategy_name_list = []
    for row in cursor.fetchall():
        strategy_name_list.append(row[0])

    update_param_list = []
    for strategy_name in strategy_name_list:
        query_sql = "select TIME, NAME, VALUE from strategy.strategy_parameter where NAME = %s \
            order by TIME desc limit 1"
        query_param = (strategy_name,)
        cursor.execute(query_sql, query_param)

        for row in cursor.fetchall():
            time = row[0]
            name = row[1]
            strategy_parameter_dict = json.loads(row[2])
            for (item_key, item_value) in strategy_parameter_dict.items():
                if 'CancelTotalTimes' in item_key:
                    strategy_parameter_dict[item_key] = total_cancel_times
            update_param = (json.dumps(strategy_parameter_dict), time, name)
            update_param_list.append(update_param)
    update_sql = 'update strategy.strategy_parameter set VALUE=%s where time=%s and name=%s'
    cursor.executemany(update_sql, update_param_list)

if __name__ == '__main__':
    print 'Enter strategy_parameter_update.'
    try:
        print 'BaseDB Ip:' + baseIp
        baseConn = MySQLdb.connect(host=baseIp, user='admin', passwd='adminP@ssw0rd', db='common', charset='utf8')
    except Exception, e:
        print e
        sys.exit(-1)
    baseCursor = baseConn.cursor()

    strategy_parameter_update(baseCursor)

    baseCursor.close()
    baseConn.commit()
    baseConn.close()
    print 'Exit strategy_parameter_update.'
