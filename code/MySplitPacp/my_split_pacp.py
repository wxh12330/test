# coding=utf-8

"""
    大文件pacp报文的切割
"""

import  os
import struct


class SpitPcap():
    """
    spit pcap
    """
    num = 0

    def __init__(self):
        self.data = 0
        self.one_pcap_file = 0
        self.spit_pcap_len = 1000
        self.sum = 0
        self.i = 1

    def get_spit_pcap(self)->None:
        with open("./pkt_20210228103430.pcap", "rb") as self.pcapfd:
            self.data = self.pcapfd.read(24)
            self.data_pckhdr = self.pcapfd.read(16)
            while self.data_pckhdr:
                (self.iplensave, ) = struct.unpack("=L", self.data_pckhdr[-4:])
                print(self.iplensave)
                self.data_pckhdr_tmp = self.data_pckhdr

                if self.i:
                    self.tmp = self.pcapfd.read(self.iplensave)
                    self.data_off = self.data_pckhdr + self.tmp
                    self.i -= 1
                else:
                    self.tmp = self.pcapfd.read(self.iplensave)
                    self.data_off = self.data_off + self.data_pckhdr_tmp + self.tmp
                self.sum = self.iplensave + self.sum
                if self.sum >= self.spit_pcap_len:
                    self.one_pcap_file = self.data +  self.data_off
                    self.write_file()
                    self.sum = 0
                    self.one_pcap_file = 0
                    self.i = 1
                self.data_pckhdr = self.pcapfd.read(16)
                if self.data_pckhdr:
                    pass
                elif self.sum < self.spit_pcap_len:
                    self.one_pcap_file = self.data + self.data_off
                    self.write_file()
                    self.sum = 0
                    self.one_pcap_file = 0
                    break


    def write_file(self)->None:
        """
        write file
        """
        self.num += 1
        self.curtime = self.num
        if os.access("./save_file", os.F_OK):
            pass
        else:
            os.mkdir("./save_file")
        self.save_path = "./save_file/" + str(self.curtime) + ".pcap"
        with open(self.save_path, "ab+") as fd:
            fd.write(self.one_pcap_file)
            print(len(self.one_pcap_file))
        print("write success")


my_spit_file = SpitPcap()
my_spit_file.get_spit_pcap()