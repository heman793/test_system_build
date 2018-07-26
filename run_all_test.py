# -*- coding:utf-8 -*-
import time
import unittest
import pytest



from public.main_config import *


def all_case():
    discover = unittest.defaultTestLoader.discover(test_case_path,
                                                   pattern='test_*.py',
                                                   top_level_dir=None)

    print discover
    return discover

if __name__ == '__main__':
    # 获取当前时间
    now = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))

    # html报告文件路径
    html = os.path.join(report_path, "result"+now+".html")

    # 打开html文件，将结果写入报告
    fp = open(html, "wb")
    runner = pytest.main()

    fp.close()