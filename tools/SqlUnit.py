# import pymssql
import MySQLdb


def get_66_db(db='dump_wind'):
    conn_66 = MySQLdb.connect(
        host="172.16.12.66",
        user="data",
        passwd="123data",
        db="%s" % db,
        charset="GBK"
    )
    return conn_66


def get_126_db(db='strategy'):
    # db = jobs, strategy
    conn = MySQLdb.connect(
        host="172.16.10.126",
        user="viewer",
        passwd="viewer",
        db="%s" % db
    )
    return conn


def get_118_db(db='aggregation'):
    # db = dump_wind, aggregation
    conn_118 = MySQLdb.connect(
        host="172.16.12.118",
        user="data",
        passwd="123data",
        db="%s" % db,
        charset="GBK"
    )
    return conn_118


# def get_zhongtou_db():
#     # a demon for pymssql connection
#     # the infomation is not useful any more
#     conn = pymssql.connect(
#         host="10.137.35.121",
#         user="sa",
#         password="Cjis8888",
#         port="1433"
#     )
#     return conn

if __name__ == '__main__':
    import pandas as pd
    conn = get_126_db()
    sql = "select * from strategy_parameter"
    df = pd.read_sql(sql, conn)
    print df.head()
    conn.close()
