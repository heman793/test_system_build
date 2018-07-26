# -*- coding: utf-8 -*-
import time
import datetime

import pandas as pd
from copy import deepcopy
from common_unit import *

Day_After_Holiday = [
    '20130923', '20131008', '20140102', '20140207', '20140408', '20140505',
    '20140603', '20140909', '20141008', '20150105', '20150225', '20150407',
    '20150504', '20150623', '20150907', '20150928', '20151008', '20160104', '20160215',
    '20160405', '20160503', '20160613', '20160819', '20160919', '20161010',
    '20170103', '20170203', '20170405', '20170502', '20170531', '20171009',
]


def get_trade_day_dataframe(path, filename):
    filepath = os.path.join(path, filename)
    # print filepath
    if not check_if_exist(filepath):
        # print "****"
        print "%s doesn't exist, please check your input again." % filepath
        return None
    df = pd.read_csv(filepath, dtype={'TRADE_DT': str})
    df['Date'] = df['TRADE_DT']
    df = df[['Date']]
    df.index = df['Date']
    return df


class DatetimeUtil(object):

    def __init__(self):
        pass

    @staticmethod
    def get_last_day(day, time_format='%Y%m%d'):
        '''
        get last day of input day
        :param day: input day string
        :param time_format: the format of input day string like '%Y%m%d' or '%Y-%m-%d'
        :return: the last day string with same format of input day
        '''
        day = datetime.datetime.strptime(day, time_format)
        day += datetime.timedelta(-1)
        return day.strftime(time_format)

    @staticmethod
    def get_next_day(day, time_format='%Y%m%d'):
        '''
        get next day of input day
        :param day: input day string
        :param time_format: the format of input day string like '%Y%m%d' or '%Y-%m-%d'
        :return: the next day string with same format of input day
        '''
        day = datetime.datetime.strptime(day, time_format)
        day += datetime.timedelta(1)
        return day.strftime(time_format)

    @staticmethod
    def get_day_unix(day, time_format='%Y%m%d %H%M%S'):
        time.strptime(day, time_format)
        return int(time.mktime(time.strptime(day, time_format)))

    @staticmethod
    def get_today(time_format='%Y%m%d'):
        return datetime.datetime.now().strftime(format=time_format)

    @staticmethod
    def get_datetime_from_unix(unix, time_format='%Y%m%d'):
        value = time.localtime(unix)
        return time.strftime(time_format, value)

    def get_next_day_unix(self, day, time_format='%Y%m%d %H%M%S'):
        return self.get_day_unix(day, time_format) + 86400

    def get_last_day_unix(self, day, time_format='%Y%m%d %H%M%S'):
        return self.get_day_unix(day, time_format) - 86400

    @staticmethod
    def pandas_value_to_unix(value):
        '''
        tranfer value of pandas
        Jet lag of 8 clock and solve the multiple situation
        :param value:
            pd.to_datetime(df['datetime']).apply(lambda x: pandas_value_to_unix(x.value))
            e.g: 2017-06-22 00:00:01 => unix_19: 1498060801000000000 => unix_10: 1498060801
        :return:
            get same unix value as function 'get_day_unix()' by same input variable
        '''
        unix_10 = value / 10 ** 9 - 8 * 3600
        return unix_10

    @staticmethod
    def pandas_localtime_to_value(unix_value, multiple=3):
        '''
        to transfer localtime unix back to value for using pd.to_datetime (for ysdata format)
        e.g  1497963540158000(length: 16) back to length 19 and add 8 clock Jet lag
        :param unix_value: localtime unix of length 16
        :param multiple: default value is 10 ** 3, if it is common unix value, multiple is 9 since
            length of common unix is 10
        :return: return value x
            pd.to_datetime(lambda x: pandas_localtime_to_value(x)) get correct time format
        '''
        unix_value *= 10 ** multiple
        unix_value += 8 * 3600 * 10 ** 9
        return unix_value


class CalendarUtil(DatetimeUtil):

    def __init__(self, day_path=future_path, filename="future_night.csv"):
        DatetimeUtil.__init__(self)
        self.calendar = get_trade_day_dataframe(day_path, filename)

    def check_if_trade_day(self, day):
        if day in self.calendar.index:
            return True
        return False

    def get_last_trade_day(self, day, time_format="%Y%m%d"):
        '''
        get last trade date string, without hour, minute and second
        :param day: input day string
        :param time_format: the format of input day string like '%Y%m%d' or '%Y-%m-%d'
        :return: the last trade day string with same format of input day
        '''
        day = datetime.datetime.strptime(day, time_format)
        day = day.strftime('%Y%m%d')
        df = self.calendar[self.calendar['Date'] < day]
        # print df
        day = df['Date'].iloc[-1]
        day = datetime.datetime.strptime(day, '%Y%m%d')
        day = day.strftime(time_format)
        # print day
        return day

    def get_next_trade_day(self, day, time_format='%Y%m%d'):
        '''
        get mext trade date string, without hour, minute and second
        :param day: input day string
        :param time_format: the format of input day string like '%Y%m%d' or '%Y-%m-%d'
        :return: the last trade day string with same format of input day
        '''
        day = datetime.datetime.strptime(day, time_format)
        day = day.strftime('%Y%m%d')
        df = self.calendar[self.calendar['Date'] > day]
        day = df['Date'].iloc[0]
        day = datetime.datetime.strptime(day, '%Y%m%d')
        day = day.strftime(time_format)
        return day

    def get_next_trade_day_unix(self, day, time_format='%Y%m%d %H%M%S'):
        day = self.get_next_trade_day(day, time_format)
        return self.get_day_unix(day, time_format)

    def get_last_trade_day_unix(self, day, time_format='%Y%m%d %H%M%S'):
        day = self.get_last_trade_day(day, time_format)
        return self.get_day_unix(day, time_format)

    def get_action_trade_day(self):
        time_format = '%Y%m%d %H:%M:%S'
        result_day = self.get_today(time_format)
        hour = int(result_day[9:11])
        time_map = {
            True: result_day[:8], False: self.get_next_trade_day(result_day[:8])
        }
        return time_map[hour < 20]

    # Very complex, since 'summer season' and 'winter season'
    # @staticmethod
    # def internation_day(day, time_format, zone):
    #     pass

    @staticmethod
    def create_datetime_idx(period_list, freq, label='right'):
        '''
        :param period_list: [[start1, end1], [start2, end2]]
        :param freq: '1min', '5s' and many more
        :param label: 'right' => '9:31' - '15:00', 'left' => '9:30' - '14:59',
                      None => '9:30' - '15:00'
        :return: pd_date_range, datetime index
        '''
        idx_result = ''
        for ind in range(len(period_list)):
            period = period_list[ind]
            idx = pd.date_range(period[0], period[1], freq=freq, closed=label)
            if ind == 0:
                idx_result = deepcopy(idx)
            else:
                idx_result = idx_result.append(idx)
        return idx_result

if __name__ == '__main__':
    dunit = DatetimeUtil()
    # print dunit.get_today()
    calendar = CalendarUtil()
    # print calendar.get_today()
    # date = '2017-06-23'
    # my_format = '%Y-%m-%d'
    # time_str = '2017-06-22 00:00:01.500005'
    # time_str_fomrat = '%Y-%m-%d %H:%M:%S.%f'
    # # print calendar.get_action_trade_day()
    # # print calendar.get_last_trade_day(time_str, time_str_fomrat)
    # time_str = '2017-06-22 00:00:01.500005'
    # print DatetimeUtil().get_day_unix(time_str, time_str_fomrat)
    # df = pd.DataFrame([time_str])
    # df.columns = ['date']
    # df['date'] = pd.to_datetime(df['date']).apply(lambda x: dunit.pandas_value_to_unix(x.value))
    # df['temp'] = df['date']
    # test = 1370131200
    # df['temp'].iloc[0] = test
    # df['temp'] = pd.to_datetime(df['temp'].apply(lambda x: dunit.pandas_localtime_to_value(x, 9)))

    plist = [
        ['2017-06-17 09:30:00', '2017-06-17 11:30:00'],
        ['2017-06-17 13:00:00', '2017-06-17 15:00:00']
    ]
    # print calendar.create_datetime_idx(plist, '1min')
