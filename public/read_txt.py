#!/usr/bin/evn python
# -*- coding: utf-8 -*-
# from public.config import *

def read_from_txt(txt_path):
    ticker_value_list = list()
    with open(txt_path) as fr:
        for line in fr.readlines():
                line_item = line.strip().split(',')
                ticker_value_list.append(line_item)
    print ticker_value_list
    return ticker_value_list

if __name__ == "__main__":
    read_from_txt('D:/Auto_Test/test_data/stock_buy_balance02_200.txt')
    print(read_from_txt)