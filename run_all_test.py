# -*- coding:utf-8 -*-
import time
import unittest

import HTMLTestRunner
from public.main_config import *


def all_case():
    discover = unittest.defaultTestLoader.discover(test_case_path, pattern='test_*.py', top_level_dir=None)

    print discover
    return discover

if __name__ == '__main__':
    # 获取当前时间
    now = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))

    # html报告文件路径
    report_abspath = os.path.join(report_path, "result"+now+".html")

    # 打开html文件，将结果写入报告
    fp = open(report_abspath, "wb")
    runner = HTMLTestRunner.HTMLTestRunner(stream=fp, title=u'自动化测试报告，测试结果如下：', description=u'用例执行情况：',)

    # 调用add_case函数返回值
    runner.run(all_case())
    fp.close()