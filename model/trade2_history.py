# -*- coding: utf-8 -*-
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class Trade2History(BaseModel):
    __tablename__ = 'trade2_history'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime, primary_key=True)
    symbol = Column(CHAR(45))
    qty = Column(Integer)
    price = Column(Float)
    fee = Column(Float, default=0)
    trade_type = Column(CHAR(45))
    strategy_id = Column(CHAR(45))
    account = Column(CHAR(45))
    hedgeflag = Column(CHAR(10))
    order_id = Column(CHAR(10))
    # 为1表示是否自成交订单，
    self_cross = Column(Integer)

    def __init__(self):
        self.hedgeflag = 0
        self.order_id = ''
        self.self_cross = 0

    def print_info(self):
        print 'time:', self.time, ',symbol:', self.symbol, ',qty:', self.qty, ',price:', self.price, ',qty:', self.qty, \
            ',trade_type:', self.trade_type, ',strategy_id:', self.strategy_id, ',account:', self.account, ',order_id:', self.order_id

