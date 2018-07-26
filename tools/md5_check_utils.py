# -*- coding: utf-8 -*-
# md5校验
import os
from model.server_constans import ServerConstant
from tools.date_utils import DateUtils
import hashlib

date_utils = DateUtils()
today_filter_str = date_utils.get_today_str('%Y-%m-%d')
server_constant = ServerConstant()
interval_time = 60


def __read_chunks(fh):
    fh.seek(0)
    chunk = fh.read(8096)
    while chunk:
        yield chunk
        chunk = fh.read(8096)
    else:
        fh.seek(0)  # 最后要将游标放回文件开头


# 计算文件的MD5值
def __get_file_md5(file_path):
    m = hashlib.md5()
    if os.path.exists(file_path):
        with open(file_path, "rb") as fh:
            for chunk in __read_chunks(fh):
                m.update(chunk)
    else:
        return ""
    return m.hexdigest()


def get_local_file_md5(file_base_path, file_name):
    local_file_path = '%s/%s' % (file_base_path, file_name)
    local_md5_value = __get_file_md5(local_file_path)
    print 'local_file:%s, md5:%s' % (local_file_path, local_md5_value)
    return local_md5_value


def get_server_file_md5(server_model, file_base_path, file_name):
    cmd = 'cd %s;md5sum %s' % (file_base_path, file_name)
    cmd = [cmd, ]
    run_result = server_model.run_cmd(cmd)
    server_md5_value = run_result.split(' ')[0]
    print 'server_file:%s, md5:%s' % (server_model.mktcenter_file_path + '/' + file_name, server_md5_value)
    return server_md5_value


# def md5_check_mktcenter_file(server_name, date_filter_str=today_filter_str):
#     server_model = server_constant.get_server_model(server_name)
#     mktcenter_file_name = '%s_%s.dat.tar.gz' % (server_model.mktcenter_file_title, date_filter_str)
#
#     local_file_path = '%s/%s' % (server_model.mktcenter_local_save_path, mktcenter_file_name)
#     local_md5_value = get_local_file_md5(local_file_path)
#
#     server_md5_value = get_server_file_md5(server_model, server_model.mktcenter_file_path, mktcenter_file_name)
#     if local_md5_value == server_md5_value:
#         print 'file:%s download ok!' % mktcenter_file_name
#         return True
#     else:
#         print 'file:%s download has error!' % mktcenter_file_name
#         return False


def md5_check_ctp_market_file(server_model, local_file_path, server_file_path, file_name):
    local_md5_value = get_local_file_md5(local_file_path, file_name)
    server_md5_value = get_server_file_md5(server_model, server_file_path, file_name)
    if local_md5_value == server_md5_value:
        print 'file:%s download success!' % file_name
        return True
    else:
        print 'file:%s download error!' % file_name
        return False


if __name__ == '__main__':
    pass
