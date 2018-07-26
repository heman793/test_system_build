# -*- coding: utf-8 -*-

import os
import platform

data_backup_path = platform_path = ''
if platform.system() == 'Linux':
    platform_path = '/'
    data_backup_path = '/raid/data_backup/CTP_data'
elif platform.system() == 'Windows':
    platform_path = r'//172.16.12.123/share'
    data_backup_path = r'H:\data_backup\CTP_data'

data_path = os.path.join(platform_path, 'data')
future_path = os.path.join(data_path, 'future')
gta_path = os.path.join(future_path, 'gta')
adj_path = os.path.join(future_path, 'adj_factor')
stock_path = os.path.join(data_path, 'wind', 'stock')
