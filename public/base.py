#!/usr/bin/evn python
# -*- coding: utf-8 -*-

from public import read_excel
import pandas as pd
import numpy as np

def get_data(testfile, sheetname):
    datainfo = read_excel.XLDatainfo(
        r'/home/trader/Autotest/Auto_Test/test_data/%s'%testfile)
    Data = datainfo.get_sheetinfo_by_name(sheetname)
    return Data


def get_column_data(io, sheetname, header=0):
    df = pd.read_excel(io, sheetname, header)
    # print df
    # column_value = np.array(df[['sn', 'para']]).tolist()
    column_value = np.array(df[['para']]).tolist()
    # print column_value
    return column_value

    # return column_value

if __name__ == "__main__":
    # test = get_data(testfile="test_stock_buy.xlsx", sheetname="TestData")
    # print (test)
    path = '/home/trader/Autotest/Auto_Test/test_data/test_stock_buy.xlsx'
    test = get_column_data(io=path, sheetname='TestData')
    print test
    # print test[1][2]