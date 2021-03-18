#coding = utf-8
"""
socket通信
"""

import os
import time
import socket
import threading
import multiprocessing


LOCAL_SOCK = "test.sock"

class ListenThread(threading.Thread):
    def __init__(self, conn: socket.socket):
        threading.Thread.__init__(self)
        self.conn = conn
    def run(self) -> None:
        while True:
            content = self.conn.recv(1024).decode()
            print(content)
            try:
                if content == "exit":
                    self.conn.send("exit".encode(encoding="utf-8"))
                    self.conn.close()
                    break
                self.conn.send("ok".encode(encoding="utf-8"))
            except BrokenPipeError:
                print("connect disable!!!")
                self.conn.close()
                break




class Listener(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def init(self):
        os.remove(LOCAL_SOCK) if os.access(LOCAL_SOCK, os.F_OK) else None
        self.local_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.local_sock.bind(LOCAL_SOCK)
        self.local_sock.listen(10)

    def run(self) -> None:
        self.init()
        while True:
            conn, _ = self.local_sock.accept()
            ListenThread(conn).start()

if __name__ == '__main__':
    Listener().start()
