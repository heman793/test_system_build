# -*- coding: utf-8 -*-
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class TradeBroker(BaseModel):
    __tablename__ = 'trade2_broker'
    id = Column(Integer, primary_key=True)
    trade_id = Column(CHAR(255))
    time = Column(DateTime)
    symbol = Column(CHAR(45))
    qty = Column(Integer)
    price = Column(Float)
    trade_type = Column(CHAR(45))
    account = Column(CHAR(45))
    order_id = Column(CHAR(45))
    direction = Column(CHAR(45))
    offsetflag = Column(CHAR(45))
    type = Column(CHAR(45))
    hedgeflag = Column(CHAR(10))

    def print_info(self):
        print 'trade_id:', self.trade_id, ',account:', self.account, ',time:', self.time, ',symbol:', self.symbol, ',qty:', self.qty, \
',trade_type:', self.trade_type, ',direction:', self.direction, ',offsetflag:', self.offsetflag
