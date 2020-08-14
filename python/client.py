#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import socket

BUFSIZE = 1024
client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
while True:
        #msg = input(">> ").strip()
        ip_port = ('127.0.0.1', 58471)
        #client.sendto(msg.encode('utf-8'),ip_port)
        client.sendto("0 0 3 aasdff112343311".encode('utf-8'),ip_port)
        time.sleep(10000)
        client.sendto("0 0 3 客户端ytest".encode('utf-8'),ip_port)
        time.sleep(1)
        client.sendto("0 0 3 st客户端test".encode('utf-8'),ip_port)
        time.sleep(1)
        client.sendto("0 0 3 客户端est".encode('utf-8'),ip_port)
        time.sleep(1)
        client.sendto("0 0 3 st客户端st".encode('utf-8'),ip_port)
                 
        #data,server_addr = client.recvfrom(BUFSIZE)
        #print('客户端recvfrom ',data,server_addr)
        time.sleep(1)
                          
client.close()
