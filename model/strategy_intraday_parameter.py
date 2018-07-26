# -*- coding: utf-8 -*-
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Date, Integer
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class Strategy_Intraday_Parameter(BaseModel):
    __tablename__ = 'strategy_intraday_parameter'
    date = Column(Date, primary_key=True)
    strategy_name = Column(CHAR(100), primary_key=True)
    ticker = Column(CHAR(45), primary_key=True)
    parameter = Column(CHAR(45))
    initial_share = Column(Integer)





