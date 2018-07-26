# -*- coding: utf-8 -*-
import os


if __name__ == '__main__':
    os.chdir('/home/trader/dailyjob/DerivativesClient')
    os.popen('screen -r DerivativesClient_market -X quit')
    os.popen('./script/start.market_ctp.sh')


