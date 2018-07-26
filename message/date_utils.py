# -*- coding: utf-8 -*-
import datetime
import time
import re
from dateutil.parser import parse
from model.holiday_info import HolidayInfo
from model.server_constans import ServerConstant


class DateUtils:
    now = datetime.datetime.now()
    holiday_list = []

    def __init__(self):
        self.holiday_list = self.get_holiday_list()

    # 获取当前日期
    @staticmethod
    def get_today():
        return datetime.datetime.today().date()

    # 获取当前日期
    @staticmethod
    def get_now():
        return datetime.datetime.now()

    # 获取当前日期
    @staticmethod
    def get_today_str(format_str='%Y%m%d'):
        return datetime.datetime.now().strftime(format_str)

    # 是否是夜盘
    @staticmethod
    def is_night_market():
        now_time = long(datetime.datetime.now().strftime('%H%M%S'))
        if now_time > 200000:
            return True
        else:
            return False


    # 获取前几天
    def get_last_days(self, last_num, format_str='%Y%m%d'):
        last_day = self.now + datetime.timedelta(days=-last_num)
        return last_day.strftime(format_str)

    # 获取节假日列表
    @staticmethod
    def get_holiday_list(format_str='%Y-%m-%d'):
        holiday_list = []
        host_server_model = ServerConstant().get_server_model('host')
        session_common = host_server_model.get_db_session('history')
        query = session_common.query(HolidayInfo)
        for holiday_info_db in query:
            holiday_list.append(holiday_info_db.holiday.strftime(format_str))
        return holiday_list

    # 获取前一交易日
    def get_last_trading_day(self, format_str, date_str=None):
        if date_str is None:
            start_date = datetime.datetime.now()
        else:
            start_date = datetime.datetime.strptime(date_str, format_str)
        last_day = start_date + datetime.timedelta(days=-1)
        if len(self.holiday_list) == 0:
            self.holiday_list = self.get_holiday_list()
        while last_day.strftime(format_str) in self.holiday_list:
            last_day = last_day + datetime.timedelta(days=-1)
        return last_day.strftime(format_str)

    # 获取后一交易日
    def get_next_trading_day(self, format_str='%Y-%m-%d', date_str=None):
        if date_str is None:
            start_date = datetime.datetime.now()
        else:
            start_date = datetime.datetime.strptime(date_str, format_str)

        next_day = start_date + datetime.timedelta(days=1)
        if len(self.holiday_list) == 0:
            self.holiday_list = self.get_holiday_list()
        while next_day.strftime(format_str) in self.holiday_list:
            next_day = next_day + datetime.timedelta(days=1)
        return next_day.strftime(format_str)

    # 是否是交易日
    def is_trading_day(self, date_str=None):
        if date_str is None:
            date_str = self.now.strftime('%Y-%m-%d')

        if len(self.holiday_list) == 0:
            self.holiday_list = self.get_holiday_list()
        if date_str in self.holiday_list:
            return False
        return True

    # 把datetime转成字符串
    @staticmethod
    def datetime_toString(dt):
        return dt.strftime("%Y-%m-%d")

    # 把字符串转成datetime
    @staticmethod
    def string_toDatetime(string):
        return datetime.datetime.strptime(string, "%Y-%m-%d")

    # 把字符串转成datetime
    @staticmethod
    def string_toDatetime2(string):
        return parse(string)

    # 把时间戳转成字符串形式
    @staticmethod
    def timestamp_toString(stamp):
        return time.strftime("%Y-%m-%d-%H", time.localtime(stamp))

    # 把datetime类型转外时间戳形式
    @staticmethod
    def datetime_toTimestamp(dateTim):
        return time.mktime(dateTim.timetuple())

    # 把字符串转成时间戳形式
    @staticmethod
    def string_toTimestamp(strTime):
        return time.mktime(DateUtils.string_toDatetime(strTime).timetuple())

    @staticmethod
    def get_microsecond_number(time_str):
        return ((int(time_str[11:13]) * 60 + int(time_str[14:16])) * 60 + int(time_str[17:19])) * 1000000 + int(
            time_str[20:26])

    @staticmethod
    def get_seconds_number(time_str):
        return ((int(time_str[:10].replace('-', '')) * 100 + int(time_str[11:13])) * 60 + int(
            time_str[14:16])) * 60 + int(time_str[17:19])

    @staticmethod
    def count_time_number(time_str):
        return int(time_str.split(':')[0]) * 60 + int(time_str.split(':')[1])

    @staticmethod
    def get_interval_seconds(start_time_str, end_time_str):
        d1 = datetime.datetime.strptime(end_time_str[:19], "%Y-%m-%d %H:%M:%S")
        d2 = datetime.datetime.strptime(start_time_str[:19], "%Y-%m-%d %H:%M:%S")
        return (d1 - d2).seconds

    @staticmethod
    def get_interval_days(start_time_str, end_time_str):
        d1 = datetime.datetime.strptime(end_time_str[:19], "%Y-%m-%d %H:%M:%S")
        d2 = datetime.datetime.strptime(start_time_str[:19], "%Y-%m-%d %H:%M:%S")
        return (d1 - d2).days


    def get_trading_day_list(self, start_date, end_date):
        trading_day_list = []
        for i in range((end_date - start_date).days + 1):
            temp_day = start_date + datetime.timedelta(days=i)
            if self.is_trading_day(temp_day.strftime("%Y-%m-%d")):
                trading_day_list.append(temp_day)
        return trading_day_list


    # 查询间隔多个交易日
    def get_interval_trading_day_list(self, start_date, interval_num, format_str='%Y%m%d'):
        trading_day_list = [start_date.strftime(format_str)]
        next_day = start_date
        while len(trading_day_list) < abs(interval_num):
            if interval_num > 0:
                next_day = next_day + datetime.timedelta(days=1)
            else:
                next_day = next_day + datetime.timedelta(days=-1)
            if self.is_trading_day(next_day.strftime("%Y-%m-%d")):
                trading_day_list.append(next_day.strftime(format_str))
        return trading_day_list


    def get_between_day_list(self, start_date, end_date):
        trading_day_list = []
        for i in range((end_date - start_date).days + 1):
            temp_day = start_date + datetime.timedelta(days=i)
            trading_day_list.append(temp_day)
        return trading_day_list

    def get_match_date_str(self, line_str):
        reg = re.compile(r'^(0?[0-9]|1[0-9]|2[0-3]):(0?[0-9]|[1-5][0-9]):(0?[0-9]|[1-5][0-9])$')
        regMatch = reg.match(line_str)
        if regMatch:
            line_dict = regMatch.groupdict()
            print line_dict


if __name__ == '__main__':
    # d1 = datetime.datetime.strptime('2017-08-11', "%Y-%m-%d")
    date_utils = DateUtils()
    date_utils.get_match_date_str('23:59:08')

