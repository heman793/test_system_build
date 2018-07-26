from public.main_config import *
from tools.time_unit import DatetimeUtil
import time
import datetime

def get_terminal_content(cmd):
    terminal = os.popen(cmd)
    content = terminal.read()
    terminal.close()
    return content

def get_component_file_list(app_name):
    physical_date = DatetimeUtil().get_today()
    if app_name == 'AlgoFrame':
        app_name = 'Algo'
    elif app_name == 'IndexArbStrategy':
        app_name = 'IndexArb'
    log_name_str = 'screenlog_%s_%s' % (app_name.lower(), physical_date)
    all_file_list = os.listdir(platform_log_path)
    component_file_list = filter(lambda x: x.lower().startswith(log_name_str),
                                 all_file_list)
    component_file_list.sort()
    return component_file_list

def check_strategy_start_log(Strategy_name):
    app_name = 'StrategyLoader'
    component_file_list = get_component_file_list(app_name)
    read_log_cmd = 'grep -E "Start Strategy: %s" %s' % (
        Strategy_name, os.path.join(platform_log_path, component_file_list[-1]))
    print read_log_cmd
    content = get_terminal_content(read_log_cmd)
    print content
    while 'Start Strategy' not in content:
        time.sleep(2)
        component_file_list = get_component_file_list(app_name)
        if len(component_file_list) > 0:
            content = get_terminal_content(read_log_cmd)
            # print content
    if content is not None:
        return True
    else:
        return False

def check_strategy_stop_log(Strategy_name):
    app_name = 'StrategyLoader'
    component_file_list = get_component_file_list(app_name)
    read_log_cmd = 'grep -E "Stop Strategy: %s" %s' % (
        Strategy_name, os.path.join(platform_log_path, component_file_list[-1]))
    content = get_terminal_content(read_log_cmd)
    # print content
    while 'Stop Strategy' not in content:
        time.sleep(1)
        component_file_list = get_component_file_list(app_name)
        if len(component_file_list) > 0:
            content = get_terminal_content(read_log_cmd)
            print content
    if content is not None:
        return True
    else:
        return False

if __name__ == '__main__':
    Strategy_name = 'BBreaker.rb_1min_para1'
    check_strategy_start_log(Strategy_name)
    # check_strategy_stop_log(Strategy_name)