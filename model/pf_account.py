# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, Float, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class PfAccount(BaseModel):
    __tablename__ = 'pf_account'
    id = Column(Integer)
    name = Column(CHAR(45), primary_key=True)
    fund_name = Column(CHAR(100), primary_key=True)
    group_name = Column(CHAR(45), primary_key=True)
    effective_date = Column(DateTime)
    description = Column(CHAR(1000))





