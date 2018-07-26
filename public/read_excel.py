#!/usr/bin/evn python
# -*- coding: utf-8 -*-
import xlrd
import pandas as pd

class XLDatainfo(object):
    def __init__(self, path=''):
        self.path = path
        self.xl = xlrd.open_workbook(path)

    def get_sheetinfo_by_name(self,name):
        self.sheet = self.xl.sheet_by_name(name)
        return self.get_sheet_info()


    def get_sheet_info(self):
        infolist = []
        for row in range(0, self.sheet.nrows):
            info = self.sheet.row_values(row)
            infolist.append(info)
        return infolist

    def get_table_ceil_info(self, name):
        self.sheet = self.xl.sheet_by_name(name)
        tablelist = []
        for column in range(0, self.sheet.ncols):
            column = self.sheet.col_values(column)
            tablelist.append(column)
        return tablelist

    def get_column_data(self, io, sheetname, header):
        df = pd.read_excel(io, sheetname, header)
        return df

    # def get_table_byname(self,colnameindex=0,name=None):
    #     self.sheet = self.xl.sheet_by_name(name)
    #     nrows = self.sheet.nrows
    #     colnames = self.sheet.row_values(colnameindex)
    #     for rownum in range(1,nrows):
    #         row = self.sheet.row_values(rownum)
    #         list = []
    #         for i in range(len(colnames)):
    #              colname_value = row[i]
    #             list.append(colnames)
    #     return list

if __name__ == "__main__":
    path = r'/home/trader/Autotest/Auto_Test/test_data/test_stock_buy.xlsx'
    # datainfo = XLDatainfo(r'/home/trader/Autotest/Auto_Test/test_data'
    #                        r'/test_stock_buy.xlsx')
    # message = datainfo.get_sheetinfo_by_name('message')
    # testdata = datainfo.get_sheetinfo_by_name('TestData')
    parameter = get_colume_data(path, sheetname='TestData',header=None)
    # parameter2 = datainfo.get_table_byname(colnameindex=1,name='TestData')
    print(parameter)
    # print(parameter[1])
    # print (message)
    # print (testdata)
    # print (parameter)
