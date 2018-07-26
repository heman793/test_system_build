# -*- coding: utf-8 -*-
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class Account(BaseModel):
    __tablename__ = 'real_account'
    accountid = Column(Integer, primary_key=True)
    accountname	= Column(CHAR(45))
    accounttype	= Column(CHAR(45))
    accountconfig = Column(CHAR(3600))
    file_name_1	= Column(CHAR(45))
    file_content_1	= Column(CHAR(3600))
    file_name_2	= Column(CHAR(45))
    file_content_2 = Column(CHAR(3600))
    allowed_etf_list = Column(CHAR(3600))
    allow_targets = Column(CHAR(100))
    allow_margin_trading = Column(Integer)
    fund_name = Column(CHAR(45))
    enable = Column(Integer)
    accountsuffix = Column(CHAR(10))
    # accountcategory = Column(CHAR(2))
    allow_arbitrage_targets = Column(CHAR(100))
    allow_hedge_targets = Column(CHAR(100))
