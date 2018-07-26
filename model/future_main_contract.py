# -*- coding: utf-8 -*-
import os

os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, Float, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class FutureMainContract(BaseModel):
    __tablename__ = 'future_main_contract'
    ticker_type = Column(CHAR(20), primary_key=True)
    exchange_id = Column(Integer, primary_key=True)
    pre_main_symbol = Column(CHAR(11))
    main_symbol = Column(CHAR(11))
    update_flag = Column(CHAR(11))
