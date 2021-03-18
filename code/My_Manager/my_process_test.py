#coding = utf-8

"""
test process
"""

import time
import multiprocessing


class Mytest(multiprocessing.Process):
    """
    test process
    """
    def __init__(self, wiser_elf):
        multiprocessing.Process.__init__(self)
        self.wiser_elf = wiser_elf

    def run(self):
        while True:
            self.test()
            time.sleep(1)

    def test(self):
        pass