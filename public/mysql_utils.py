import sys
import MySQLdb

server_ip = '172.16.12.98'
user = 'root'
password = 'asdasd123'
db = 'portfolio'


class MySqlUtils:
    server_ip = None
    user = 'root'
    password = 'asdasd123'
    conn = None
    cursor = None

    def __init__(self, server_ip=None):
        if server_ip is None:
            self.server_ip = server_ip
            self.user = user
            self.password = password
        else:
            self.server_ip = server_ip

    def __enter__(self):
        try:
            self.conn = MySQLdb.connect(\
                host=self.server_ip, user=self.user, passwd=self.password, \
                db=self.db, charset='utf8')
            print 'connect to db:', self.server_ip
        except Exception, e:
            print e
            sys.exit()
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, type, value, traceback):
        self.cursor.close()
        self.conn.commit()
        self.conn.close()

    def query_all(self, query_sql, query_param=None):
        if query_param is None:
            self.cursor.execute(query_sql)
        else:
            self.cursor.execute(query_sql, query_param)
        return self.cursor.fetchall()

    def query_one(self, query_sql, query_param=None):
        if query_param is None:
            self.cursor.execute(query_sql)
        else:
            self.cursor.execute(query_sql, query_param)
        return self.cursor.fetchone()

    def insert(self, insert_sql, insert_param=None):
        self.cursor.executemany(insert_sql, insert_param)

    def insert_many(self, insert_sql, insert_param_list=None):
        self.cursor.executemany(insert_sql, insert_param_list)

if __name__ == '__main__':
    MySqlUtils(server_ip='172.16.12.98')