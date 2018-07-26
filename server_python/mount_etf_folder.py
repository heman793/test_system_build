# -*- coding: utf-8 -*-
import os
import commands
from datetime import datetime
from tools.loggingUtils import loggingUtils
from time import sleep

logger = loggingUtils('dailyjob_0905.log')
now = datetime.now()
todayStr = now.strftime('%Y%m%d')

logger.info('4.start Mount ETF Files')


sudo_command = 'umount /home/trader/etf'
(status, output) = commands.getstatusoutput(sudo_command)
logger.info('umount result:%d  output:%s\n' % (status, output))
if (status == 0) or 'umount: /home/trader/etf: not mounted' in output:
    sudo_command = 'mount -o username=samba,password=smbshare //10.200.66.1/samba/'+ todayStr + '  /home/trader/etf'
    logger.info(sudo_command + '\n');
    (status, output) = commands.getstatusoutput(sudo_command)
    logger.info('mount result:%d  output:%s\n' % (status, output))
    if (status != 0):
        (status, output) = commands.getstatusoutput(sudo_command)
        logger.info('mount2 result:%d  output:%s\n' % (status, output))
