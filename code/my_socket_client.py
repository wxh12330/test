#coding = utf-8
"""

"""

import socket
import time

client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client_socket.connect("test.sock")
while True:
    str2 = input()
    client_socket.send(str2.encode(encoding="utf-8"))
    mem = client_socket.recv(1024).decode()
    print(mem)
    if mem == "exit":
        client_socket.close()
        break