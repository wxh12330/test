#coding = utf-8
"""
修改进程名
"""

import setproctitle
import time

setproctitle.setproctitle("wxh")

while True:
    time.sleep(10)