# -*- coding: utf-8 -*-

import six
import zmq
import AllProtoMsg_pb2
import time
from public.main_config import *
from data_prepare.common.config_common import ConfigCommon
import pandas as pd

def phone_trade_message(self):
    context = zmq.Context().instance()
    # print "Connecting to server"
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, b'127.0.0.1_real')
    socket.connect(socket_connect_dict)

    filename = 'phone_trade.csv'
    df = pd.read_csv(os.path.join(strategy_config_path, filename))
    msg = AllProtoMsg_pb2.PhoneTradeRequestMsg()




    msg_str = msg.SerializeToString()
    msg_type = 4
    msg_list = [six.int2byte(msg_type), msg_str]
    socket.send_multipart(msg_list)

        # print "Send New Order Message."

    time.sleep(2)
    socket.close()

if __name__ == "__main__":
    phone_trade_message()