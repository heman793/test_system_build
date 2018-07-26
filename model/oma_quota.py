# -*- coding: utf-8 -*-
import os

os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, Date
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class OmaQuota(BaseModel):
    __tablename__ = 'oma_quota'
    date = Column(Date, primary_key=True)
    investor_id = Column(CHAR(45), primary_key=True)
    symbol = Column(CHAR(45), primary_key=True)
    sell_quota = Column(Integer)
    buy_quota = Column(Integer)
