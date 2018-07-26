# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, Float, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class AccountPosition(BaseModel):
    __tablename__ = 'account_position'
    date = Column(Date, primary_key=True)
    id = Column(Integer, primary_key=True)
    symbol = Column(CHAR(45), primary_key=True)
    hedgeflag = Column(CHAR(10), primary_key=True)
    long = Column(Float, default=0)
    long_cost = Column(Float, default=0)
    long_avail = Column(Float, default=0)
    day_long = Column(Float, default=0)
    day_long_cost = Column(Float, default=0)
    short = Column(Float, default=0)
    short_cost = Column(Float, default=0)
    short_avail = Column(Float, default=0)
    day_short = Column(Float, default=0)
    day_short_cost = Column(Float, default=0)
    fee = Column(Float, default=0)
    close_price = Column(Float)
    note = Column(CHAR(3600))
    delta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    vega = Column(Float)
    rho = Column(Float)
    yd_position_long = Column(Float, default=0)
    yd_position_short = Column(Float, default=0)
    yd_long_remain = Column(Float, default=0)
    yd_short_remain = Column(Float, default=0)
    prev_net = Column(Float, default=0)
    purchase_avail = Column(Float, default=0)
    frozen = Column(Float, default=0)
    update_date = Column(DateTime, default=datetime.datetime)

    td_buy_long = 0
    td_sell_short = 0
    td_pur_red = 0
    td_merge_split = 0

    def __init__(self):
        self.td_buy_long = 0
        self.td_sell_short = 0
        self.td_pur_red = 0
        self.td_merge_split = 0
        self.long = 0
        self.long_cost = 0.0
        self.long_avail = 0
        self.yd_position_long = 0
        self.yd_long_remain = 0
        self.short = 0
        self.short_cost = 0.0
        self.short_avail = 0
        self.yd_position_short = 0
        self.yd_short_remain = 0

    def print_info(self):
        print 'yd_position_long:', self.yd_position_long, ',td_buy_long:', self.td_buy_long, \
',td_sell_short:', self.td_sell_short,',td_pur_red:', self.td_pur_red, ',td_merge_split:', self.td_merge_split





