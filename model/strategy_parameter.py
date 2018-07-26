# -*- coding: utf-8 -*-
import copy

from sqlalchemy import Column
from sqlalchemy.types import CHAR, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class StrategyParameter(BaseModel):
    __tablename__ = 'strategy_parameter'
    time = Column(DateTime, primary_key=True)
    name = Column(CHAR(45), primary_key=True)
    value = Column(Text)
