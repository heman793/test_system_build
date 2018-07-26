# -*- coding: utf-8 -*-
import copy
import os

os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class AccountTradeRestrictions(BaseModel):
    __tablename__ = 'account_trade_restrictions'
    account_id = Column(Integer, primary_key=True)
    ticker = Column(CHAR(45), primary_key=True)
    exchange_id = Column(Integer, primary_key=True)
    hedgeflag = Column(CHAR(45), primary_key=True)
    max_open = Column(Integer)
    today_open = Column(Integer)

    max_cancel = Column(Integer)
    today_cancel = Column(Integer)

    max_large_cancel = Column(Integer)
    today_large_cancel = Column(Integer)

    max_operation = Column(Integer)
    today_operation = Column(Integer)

    option_max_long = Column(Integer)
    option_long = Column(Integer)

    option_max_short = Column(Integer)
    option_short = Column(Integer)
    
    def __init__(self):
        self.max_open = 0
        self.today_open = 0
        self.max_cancel = 0
        self.today_cancel = 0
        self.max_large_cancel = 0
        self.today_large_cancel = 0
        self.max_operation = 0
        self.today_operation = 0
        self.option_max_long = 0
        self.option_long = 0
        self.option_max_short = 0
        self.option_short = 0

    def copy(self):
        return copy.deepcopy(self)
