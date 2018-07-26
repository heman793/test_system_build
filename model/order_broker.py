# -*- coding: utf-8 -*-
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, Float, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class OrderBroker(BaseModel):
    __tablename__ = 'order_broker'
    id = Column(Integer, primary_key=True)
    sys_id = Column(CHAR(64))
    account = Column(CHAR(32))
    symbol = Column(CHAR(32))
    direction = Column(CHAR(45))
    trade_type = Column(Integer)
    status = Column(Integer)
    submit_status = Column(Integer)
    insert_time = Column(DateTime)
    qty = Column(Integer)
    price = Column(Float)
    ex_qty = Column(Integer)
    ex_price = Column(Float)

    def to_string(self):
        return 'account:%s,sys_id:%s,symbol:%s,direction:%s,trade_type:%s,qty:%s,price:%s,status:%s' % \
               (self.account, self.sys_id, self.symbol, self.direction, self.trade_type, self.qty,self.price, self.status)
