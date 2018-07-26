# -*- coding: utf-8 -*-
import os
os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'
from sqlalchemy import Column, Float
from sqlalchemy.types import Date
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class HolidayInfo(BaseModel):
    __tablename__ = 'holiday_list'
    holiday = Column(Date, primary_key=True)
    weight = Column(Float)

