# -*- coding: utf-8 -*-
import copy
import os

os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class StrategyChangeHistory(BaseModel):
    __tablename__ = 'strategy_change_history'
    id = Column(Integer, primary_key=True)
    enable = Column(Integer)
    name = Column(CHAR(45))
    # online/downline
    change_type = Column(CHAR(45))
    parameter_server = Column(CHAR(2000))
    update_time = Column(DateTime)
    change_server_name = Column(CHAR(45))