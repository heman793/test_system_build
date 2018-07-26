# -*- coding: utf-8 -*-
import copy
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, Float, Date
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class PfPosition(BaseModel):
    __tablename__ = 'pf_position'
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

    def __init__(self):
        self.long = 0
        self.long_avail = 0
        self.long_cost = 0
        self.short = 0
        self.short_avail = 0
        self.short_cost = 0
        self.yd_position_long = 0
        self.yd_position_short = 0
        self.yd_long_remain = 0
        self.yd_short_remain = 0

        self.delta = 1.000000
        self.gamma = 0.000000
        self.theta = 0.000000
        self.vega = 0.000000
        self.rho = 0.000000

    def merge(self, pf_position):
        self.long += pf_position.long
        self.long_cost += pf_position.long_cost
        self.long_avail += pf_position.long_avail
        self.short += pf_position.short
        self.short_cost += pf_position.short_cost
        self.short_avail += pf_position.short_avail
        self.yd_position_long += pf_position.yd_position_long
        self.yd_position_short += pf_position.yd_position_short
        self.yd_long_remain += pf_position.yd_long_remain
        self.yd_short_remain += pf_position.yd_short_remain
        self.prev_net += pf_position.prev_net
        return self

    def copy(self):
        return copy.deepcopy(self)

    def print_info(self):
        print 'date:%s,id:%s,symbol:%s,long:%s' % (self.date, self.id, self.symbol, self.long)


