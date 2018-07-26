# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()

class OrderHistory(BaseModel):
    __tablename__ = 'order_history'

    id = Column(Integer, primary_key=True)
    sys_id = Column(CHAR(45))
    account = Column(CHAR(45))
    hedgeflag = Column(CHAR(45))
    symbol = Column(CHAR(45))
    direction = Column(Integer)
    type = Column(Integer)
    trade_type = Column(Integer)
    status = Column(Integer)
    op_status = Column(Integer)
    property = Column(Integer)
    create_time = Column(DateTime)
    transaction_time = Column(DateTime)
    user_id = Column(CHAR(45))
    strategy_id = Column(CHAR(45))
    parent_ord_id = Column(CHAR(45))
    qty = Column(Integer)
    price = Column(Float)
    ex_qty = Column(Integer)
    ex_price = Column(Float)
    algo_type = Column(Integer)
