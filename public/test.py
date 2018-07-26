from tools.time_unit import DatetimeUtil
from data_prepare.instrument.instrument_update import InstrumentUpdate
from public.main_config import *
from data_prepare.common.config_common import ConfigCommon
from ysdata.data_info import FutureData
from ysdata.future_info import *


def execute_db_sql_with_result(db, conn=None):
    if conn is None:
        conn = get_conn_db(db)
    cur = conn.cursor()
    sql_list = ["select prev_close, ticker from instrument where ticker "
                "='000001'",
                "select prev_close, ticker from instrument where ticker "
                "='600000'"]
    map(lambda sql: cur.execute(sql), sql_list)

    result = cur.fetchone()
    print result
    msg_list = []
    for msg in result:
        # print msg
        msg_list.append(msg)
        print msg_list
    return msg_list
    cur.close()
    conn.commit()
    conn.close()

if __name__ == '__main__':
    common_cfg = ConfigCommon().get_ini_input_dict()
    execute_db_sql_with_result(db='common')