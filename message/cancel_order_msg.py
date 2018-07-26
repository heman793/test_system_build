# -*- coding: utf-8 -*-

import six
import zmq
import AllProtoMsg_pb2
import time
from public.main_config import *

def cancel_order_message(self, order_id):
    context = zmq.Context().instance()
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, b'127.0.0.1_real')
    socket.connect(socket_connect_dict)

    msg = AllProtoMsg_pb2.CancelOrderMsg()
    msg.SysOrdID = order_id
    msg_str = msg.SerializeToString()
    msg_type = 5
    msg_list = [six.int2byte(msg_type), msg_str]
    socket.send_multipart(msg_list)

    # print "Send Cancel Order Message."

    time.sleep(2)
    socket.close()

if __name__ == "__main__":
    order_id = 'ts0002'
    cancel_order_message(order_id)