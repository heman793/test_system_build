# -*- coding: utf-8 -*-
import copy
import os

os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, Float, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class StrategyOnline(BaseModel):
    __tablename__ = 'strategy_online'
    id = Column(Integer, primary_key=True)
    enable = Column(Integer)
    strategy_type = Column(CHAR(45))
    target_server = Column(CHAR(45))
    assembly_name = Column(CHAR(45))
    strategy_name = Column(CHAR(45))
    instance_name = Column(CHAR(45))
    name = Column(CHAR(45))
    parameter = Column(CHAR(1000))
    parameter_server = Column(CHAR(1000))
    # minbar或者quote
    data_type = Column(CHAR(45))
    # 设置加载多少天的数据
    date_num = Column(Integer)
    # local_server = Column(CHAR(100))

    def copy(self):
        return copy.deepcopy(self)


class StrategyServerParameter(BaseModel):
    __tablename__ = 'strategy_server_parameter'
    date = Column(Date, primary_key=True)
    server_name = Column(CHAR(100), primary_key=True)
    strategy_name = Column(CHAR(100), primary_key=True)
    account_name = Column(CHAR(100), primary_key=True)
    max_long_position = Column(Integer)
    max_short_position = Column(Integer)
    qty_per_trade = Column(Integer)


class StrategyServerParameterChange(BaseModel):
    __tablename__ = 'strategy_server_parameter_change'
    date = Column(Date, primary_key=True)
    server_name = Column(CHAR(100), primary_key=True)
    strategy_name = Column(CHAR(100), primary_key=True)
    account_name = Column(CHAR(100), primary_key=True)
    max_long_position = Column(CHAR(100))
    max_short_position = Column(CHAR(100))
    qty_per_trade = Column(CHAR(100))
