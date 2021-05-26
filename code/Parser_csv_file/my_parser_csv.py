# coding=utf-8
"""
    解析csv格式文件
"""

import csv
import os
import IPy

FILE_PATH = "./"
FILE_FORMAT = (".csv",)
WRITH_IP_INFO_PATH = "./ip_info.txt"
WRITE_PROVINCE_INFO_PATH = "./province_info.txt"

PROVINCE_ID = {"北京": "2", "安徽": "3", "福建": "4", "甘肃": "5", "广东": "6", "广西": "7",
               "贵州": "8", "海南": "9", "河北": "10", "河南": "11", "黑龙江": "12", "湖北": "13", "湖南": "14",
               "吉林": "15", "江苏": "16", "江西": "17", "辽宁": "18", "内蒙古": "19", "宁夏": "20", "青海": "21",
               "山东": "22", "山西": "23", "陕西": "24", "上海": "25", "四川": "26", "天津": "27", "西藏": "28",
               "新疆": "29", "云南": "30", "浙江": "31", "重庆": "32", "香港": "33", "澳门": "34", "台湾": "35"}
OPERATOR_VALUE = {"移动": "1",
                  "电信": "2",
                  "联通": "3"}


class CSV(object):
    """
    解析csv文件类
    """

    @staticmethod
    def remove_csv_space(rows: list) -> int:
        """
        去除csv文件的空白行
        """
        if rows[0] == '' and rows[1] == '' and \
                rows[2] == '' and rows[3] == '' and rows[4] == '':
            return 1
        return 0

    @staticmethod
    def trans_province_to_id(rows: list) -> list:
        """
        转化中文省份为对应的id
        """
        search_id = 0
        for province_id in PROVINCE_ID:
            if rows[0] == province_id:
                search_id = 1
                rows[0] = PROVINCE_ID[province_id]
        if search_id != 1:
            rows[0] = '0'
        return rows

    @staticmethod
    def operator_to_id(rows: list) -> list:
        """
        运营商转换为对应的id,如不存在移动，电信，联通，默认为其他，即
        值转化为0
        """
        search_id = 0
        for operator_id in OPERATOR_VALUE:
            if rows[2] == operator_id:
                search_id = 1
                rows[2] = OPERATOR_VALUE[operator_id]
                rows[0] = rows[0] + rows[2]
        if search_id != 1:
            rows[2] = "0"
            rows[0] += "0"
        return rows

    @staticmethod
    def check_ip_exist(rows: list) -> int:
        """
        检测ip是否为空
        """
        if rows[3] == '' and rows[4] == '':
            return 1
        if (IPy.IP(rows[3]).version() == 4) and (IPy.IP(rows[4]).version() == 4) and (
                (len(rows[3].split(".")) != 4) or (len(rows[4].split(".")) != 4)):
            return 1
        return 0

    @staticmethod
    def csv_file_ip_legal(rows: list) -> list:
        """
        检测ip地址的合法性
        """
        if rows[3] == '':
            rows[3] = rows[4]
        elif rows[4] == '':
            rows[4] = rows[3]

        if (IPy.IP(rows[3]).version() == 4) and (IPy.IP(rows[4]).version() == 4):
            rows[2] = "1"
        elif (IPy.IP(rows[3]).version() == 6) and (IPy.IP(rows[4]).version() == 6):
            rows[2] = "2"
        return rows

    @staticmethod
    def _remove_cr_lf(one_string: str) -> str:
        """
        移除结尾\r\n
        """
        return one_string.strip()

    @staticmethod
    def _remove_space(one_string: str) -> str:
        """
        移除前后空格以及中间超过一个空格修改为一个空格
        """
        return "".join(list(filter(lambda x: x, one_string.split(" "))))

    @staticmethod
    def _remove_notes(one_string: str) -> str:
        """
        移除注释 #
        """
        return one_string.split("#")[0]

    def csv_file_handle(self):
        """
        csv文件处理
        """
        if os.path.exists(FILE_PATH):
            for files in os.listdir(FILE_PATH):
                if os.path.isfile(files):
                    self.read_csv_file(files)
        else:
            print("DIR is not exist")

    def read_csv_file(self, files: str):
        """
        读取csv文件
        """
        if files[-4:] in FILE_FORMAT:
            with open(files, "r", newline='') as csv_read:
                csv_content = csv.reader(csv_read)
                self.write_ip_and_province_info(csv_content)

    def write_ip_and_province_info(self, csv_content):
        """
        生成ip文件
        """
        with open(WRITH_IP_INFO_PATH, "w", encoding="utf-8") as write_ip:
            ip_sort_list = []
            for _, rows in enumerate(csv_content, 1):
                row_flag = self.remove_csv_space(rows)
                if row_flag == 1:
                    continue
                rows = self.trans_province_to_id(rows)
                rows = self.operator_to_id(rows)
                ip_exist = self.check_ip_exist(rows)
                if ip_exist == 1:
                    continue
                rows = self.csv_file_ip_legal(rows)
                ip_info_list = [rows[0], rows[2], rows[3], rows[4]]
                ip_sort_list.append(ip_info_list)
            finall_content = sorted(ip_sort_list, key=lambda x: x[0], reverse=False)  # 升序
            for line_content in finall_content:
                print(line_content)
                write_ip.writelines(",".join(line_content) + '\n')


if __name__ == '__main__':
    my_csv = CSV()
    my_csv.csv_file_handle()
