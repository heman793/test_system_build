# -*- coding: utf-8 -*-
from model.backtest_server_model import BackTestServerModel
from tools.getConfig import getConfig
from server_model import ServerModel


class ServerConstant:
    server_dict = dict()

    def __init__(self):
        server_model_host = ServerModel('host')
        server_model_host.ip = getConfig()['host']
        server_model_host.db_ip = getConfig()['host']
        server_model_host.db_port = getConfig()['db_port']
        server_model_host.db_user = getConfig()['db_user']
        server_model_host.db_password = getConfig()['db_password']

        server_model_125 = ServerModel('local125')
        server_model_125.ip = '172.16.11.125'
        server_model_125.db_ip = '172.16.11.125'
        server_model_125.db_port = 3306
        server_model_125.derivatives_client_folder = '/home/trader/dailyjob/DerivativesClient'
        server_model_125.python_eod_folder = '/home/trader/dailyjob/eod_aps/derivatives'
        server_model_125.etf_folder = '/home/trader/etf'
        server_model_125.etf_upload_folder = '/home/trader/dailyjob/ETF'
        server_model_125.log_file_path = '/home/trader/apps/IndexArb/log'

        server_model_40 = ServerModel('aliyun_40')
        server_model_40.ip = '121.41.22.40'
        server_model_40.db_ip = '121.41.22.40'
        server_model_40.db_port = 3306
        server_model_40.derivatives_client_folder = '/home/trader/dailyjob/DerivativesClient'
        server_model_40.python_eod_folder = '/home/trader/dailyjob/eod_aps/derivatives'
        server_model_40.etf_upload_folder = '/home/trader/dailyjob/ETF'
        server_model_40.log_file_path = '/home/trader/apps/TradePlat/log'

        server_model_118 = BackTestServerModel('local118')
        server_model_118.ip = '172.16.12.118'
        server_model_118.db_ip = '172.16.12.118'
        server_model_118.db_port = 3306
        server_model_118.derivatives_client_folder = '/home/trader/dailyjob/DerivativesClient'
        server_model_118.python_eod_folder = '/home/trader/dailyjob/eod_aps/derivatives'
        server_model_118.etf_upload_folder = '/home/trader/dailyjob/ETF'
        server_model_118.log_file_path = '/home/trader/apps/TradePlat/log'
        server_model_118.log_zip_folder_list = ['/home/backtest/dailyjob/DerivativesClient/messageFile',
                                                  '/home/backtest/dailyjob/DerivativesClient/marketFile']
        server_model_118.log_clear_folder_list = server_model_118.log_zip_folder_list

        server_model_166 = ServerModel('local166')
        server_model_166.ip = '172.16.12.166'
        server_model_166.userName = 'yangzhoujie'
        server_model_166.passWord = '123456'

        server_model_168 = ServerModel('local168')
        server_model_168.ip = '172.16.12.168'
        server_model_168.userName = 'yangzhoujie'
        server_model_168.passWord = '123456'

        server_model_196 = ServerModel('local196')
        server_model_196.ip = '172.16.12.196'
        server_model_196.userName = 'yangzhoujie'
        server_model_196.passWord = '123456'

        server_model_66 = ServerModel('local66')
        server_model_66.ip = '172.16.12.66'
        server_model_66.db_ip = '172.16.12.66'
        server_model_66.db_user = 'data'
        server_model_66.db_password = '123data'

        server_model_88 = ServerModel('local88')
        server_model_88.ip = '172.16.12.88'
        server_model_88.db_ip = '172.16.12.88'
        server_model_88.db_port = 3306
        server_model_88.db_user = 'root'
        server_model_88.db_password = '123456'
        server_model_88.derivatives_client_folder = '/home/trader/dailyjob/DerivativesClient'
        server_model_88.python_eod_folder = '/home/trader/dailyjob/eod_aps/derivatives'
        server_model_88.etf_upload_folder = '/home/trader/dailyjob/ETF'
        server_model_88.log_file_path = '/home/trader/apps/TradePlat/log'
        server_model_88.log_zip_folder_list = [
            '/home/backtest/dailyjob/DerivativesClient/messageFile',
            '/home/backtest/dailyjob/DerivativesClient/marketFile']
        server_model_88.log_clear_folder_list = server_model_88.log_zip_folder_list

        self.server_dict['host'] = server_model_host
        self.server_dict['local88'] = server_model_88
        self.server_dict['local125'] = server_model_125
        self.server_dict['local118'] = server_model_118
        self.server_dict['local166'] = server_model_166
        self.server_dict['local168'] = server_model_168
        self.server_dict['local196'] = server_model_196
        self.server_dict['aliyun_40'] = server_model_40
        self.server_dict['local66'] = server_model_66

    def get_server_model(self, server_name):
        return self.server_dict[server_name]

    def get_all_server(self):
        update_server_list = []
        update_server_str = getConfig()['update_server']

        for server_name in update_server_str.strip().split(','):
            update_server_list.append(self.server_dict[server_name])

        return update_server_list

    # def get_all_server(self):
    #     update_server_list = []
    #     for server_name in ('host',):
    #         update_server_list.append(self.server_dict[server_name])
    #     return update_server_list

if __name__ == '__main__':
    server_constant = ServerConstant()
    print server_constant.get_all_server()