#!/usr/bin/evn python
# -*- coding: utf-8 -*-
import getpass
import MySQLdb
from tools.logger_unit import LogUnit
from tools.time_unit import CalendarUtil
from tools.common_unit import *
import logging

calendar = CalendarUtil()

project_path = '/home/trader/Autotest/Auto_Test'
test_data_path = os.path.join(project_path, 'test_data')
report_path = '/home/trader/Autotest/Auto_Test/report'
test_case_path = os.path.join(project_path, 'test_case')
cta_test_case_path = os.path.join(project_path, )
socket_connect_dict = 'tcp://172.16.12.88:17103'

# windows setting
windows_ip = '172.16.11.180'
windows_port = 8888

# Sql Information Setting
sql_server = '172.16.12.88'
sql_user = 'root'
sql_password = '123456'

# Sql Information Setting
# sql_server = '172.16.20.125'
# sql_user = 'admin'
# sql_password = 'adminP@ssw0rd'

# eod_aps config setting
eod_aps_config_filename = 'public/eod_aps_config.txt'
datafetcher_file_path = '/nas/data_share/price_files'
etf_file_path = '/nas/data_share/index_weight'

# src_data_path
lts_data_path = '/raid/data_backup/LTS_data'
future_data_path = '/data/future/backtest/all_type/quotes'
src_volume_profile_path = '/data/daily/stock/volume_profile'
parameter_dict_filepath_default = '/dailyjob/StockIntraday/parameter_dict_20170816.csv'

# AutoTest Platform Basic Config
#user_path = '/home/%s' % getpass.getuser()
user_path = '/home/trader'

# critical path setting: project_path
project_path = os.path.join(user_path, 'Autotest/Auto_Test')
platform_path = '/home/trader/apps/TradePlat'
platform_log_path = '/home/trader/apps/TradePlat/log'
volume_profile_path = os.path.join(platform_path, 'volume_profile')
template_path = os.path.join(project_path, 'template')
config_template_path = os.path.join(template_path, 'config_template')
script_template_path = os.path.join(template_path, 'script_template')
version_path = os.path.join(project_path, 'TestType')
test_log_path = os.path.join(project_path, 'log')
test_data_path = os.path.join(project_path, 'data')
future_quote_data_path = os.path.join(platform_path, 'quote')
future_strategy_para_path = os.path.join(version_path, 'future_Config')
atp_strategy_para_path = os.path.join(version_path, 'all_Config')
strategyloader_file_path = '/home/trader/apps/TradePlat/cfg'
# DataBase Setting
fund_name = 'steady_return'
stock_account = '109178005300-PROXY-steady_return-'
future_account = '030730-CTP-steady_return-'
strategy = 'default'

# linux setting config
control_port_num = 17103  # no need to update

# windows setting config




# Strategy Detail Config
# ================================== common config =============================================
# AutoTestOrder.csv / strategy_loader_parameter_list.csv /
# ================================== detail config =============================================
# parameter_dict.csv
#strategy_chosen : StkIntraday,CTA,All
strategy_chosen = 'All'
file_log_name = '%s_create_file_list.log' % strategy_chosen
platform_log_name = '%s_platform_msg.log' % strategy_chosen
component_log_name = '%s_component.log' % strategy_chosen
sql_log_name = '%s_sql.log' % strategy_chosen
DATAFETCHER_MESSAGEFILE_FOLDER = '/home/trader/dailyjob/DataFetcher/messageFile'
ETF_FILE_PATH ='/nas/data_share/index_weight'

logging_level = logging.INFO
logging_level = logging.DEBUG
sql_logger = LogUnit().create_logger(test_log_path, sql_log_name, logging_level=logging_level, to_stream=False)
platform_logger = LogUnit().create_logger(test_log_path, platform_log_name, logging_level=logging_level, to_stream=True)
file_logger = LogUnit().create_logger(test_log_path, file_log_name, logging_level=logging_level, to_stream=False)


def get_log_format_string(string, tag='='):
    copy_num = 30
    output_string = '%s %s %s' % (tag * copy_num, string, tag * copy_num)
    return output_string


def get_conn_db(db):
    conn_info = MySQLdb.connect(
        host=sql_server,
        user=sql_user,
        passwd=sql_password,
        db="%s" % db,
        charset="GBK"
    )
    return conn_info

def get_conn_db_return(db):
    conn_info = MySQLdb.connect(
        host=sql_server,
        user=sql_user,
        passwd=sql_password,
        db="%s" % db,
        charset="GBK",
        cursorclass = MySQLdb.cursors.DictCursor
    )
    return conn_info


def write_script_from_template():
    """
    initial process, create script once if you change your project root path
    run this function after modifying setting
    :return:
    """
    log_template_path = os.path.join(platform_log_path, 'screenlog_%t_`date +%Y%m%d-%H%M%S`.log')
    screen_path = os.path.join(user_path, '.screenrc')
    log_file_name = 'echo "logfile %s" > %s' % (log_template_path, screen_path)
    print log_file_name
    for filename in os.listdir(script_template_path):
        src_filepath = os.path.join(script_template_path, filename)
        des_filepath = os.path.join(platform_path, 'script', filename)
        file_src = file(src_filepath, 'rb')
        file_des = file(des_filepath, 'wb')
        line = file_src.readline()
        file_des.write(line)
        while line:
            line = file_src.readline()
            if line.startswith('echo'):
                file_des.writelines(log_file_name+'\n')
            else:
                file_des.writelines(line)
        file_src.close()
        file_des.close()


if __name__ == '__main__':
    write_script_from_template()
    pass
