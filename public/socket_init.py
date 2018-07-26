# -*- coding: utf-8 -*-
import zmq
from public.config import *

def socket_init(server_name):
    context = zmq.Context().instance()
    print "Connecting to server"
    socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.IDENTITY, b'127.0.0.1_real')
    socket.connect(socket_connect_dict)
    return socket
