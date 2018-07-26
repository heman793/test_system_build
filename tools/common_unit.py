# -*- coding: utf-8 -*-

from path_unit import *


def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def check_if_exist(path):
    if not os.path.exists(path):
        return False
    return True


def get_tab_day(day):
    return '-'.join([day[:4], day[4:6], day[6:8]])


def remove_file_path(file_path):
    if check_if_exist(file_path) and os.path.isfile(file_path):
        os.remove(file_path)


def create_file_name_cols(filepath, cols):
    '''
    create file with cols and save as filepath,
    if existed, will append content, not overwrite
    :param filepath: os.path.join(x, y) ......
    :param cols: title of file, e.g: ['date', 'symbol', ...., 'test']
    :return: return file object, need close after use
    '''
    if not check_if_exist(filepath):
        file_ = file(filepath, 'wb')
        line = ','.join(cols) + '\n'
        file_.write(line)
    else:
        file_ = file(filepath, 'a+')
    return file_


if __name__ == '__main__':
    pass



