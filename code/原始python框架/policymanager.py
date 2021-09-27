# coding=utf-8

"""
for policy manager
"""

import os
import sys
import json
import time
import toml
import socket
import logging
import requests
import multiprocessing

import tocmp
import hflask
import tofpga
import tomysql
import wiserelf
import timemanager
import resourcechanger

from flask import Flask
from flask import request

from ResourceLib import ftp_get_resource


class HTestClass(multiprocessing.Process):
    """
    for test
    """

    def __init__(self, wiser_elf: wiserelf.WiserElf):
        multiprocessing.Process.__init__(self)
        self.wiser_elf = wiser_elf

    def run(self) -> None:
        """
        for test
        """
        while True:
            time.sleep(10)


class _HFlask(Flask):
    """
    by Flask
    """
    wiser_elf: wiserelf.WiserElf = None
    tofpga_message_creator: tofpga.CreatePostMessage = None
    tofpga_message_sender: tofpga.SendConfigToFPGA = None
    tocmp_message_creator: tocmp.CreateTcpMessage = None
    tocmp_message_sender: tocmp.SendPolicyToCMP = None
    totimemanager_policy_changer: timemanager.ChangePolicyForManagement = None

    def h_init(self, wiser_elf: wiserelf.WiserElf) -> None:
        """
        for init wiser_elf after process start
        :param wiser_elf: wiser elf class var
        """
        self.wiser_elf = wiser_elf
        self.tofpga_message_creator = tofpga.CreatePostMessage(wiser_elf)
        self.tofpga_message_sender = tofpga.SendConfigToFPGA(wiser_elf)
        self.tocmp_message_creator = tocmp.CreateTcpMessage(wiser_elf)
        self.tocmp_message_sender = tocmp.SendPolicyToCMP(wiser_elf)
        self.totimemanager_policy_changer = timemanager.ChangePolicyForManagement(wiser_elf)


h_flask = _HFlask(sys.argv[0].split("/")[-1].split(".")[0])
logging.getLogger("werkzeug").setLevel(logging.ERROR)


@h_flask.route("/config", methods=["POST"])
def flask_rout_recv_config() -> str:
    """
    for recv config message, and post send to FPGA
    :return: always 200OK, and {"result": 200/10000 /10001, message: ""} 200 is success, 10000/100001 is failed.
    """
    recv_json = None
    result_code = 200
    failed_message = ""

    try:
        recv_json = json.loads(request.data)
    except Exception:
        h_flask.wiser_elf.traceback()
        h_flask.wiser_elf.statistic("GET_UI_CONFIG_MEM_TO_JSON_FAILED")

    if recv_json:
        post_msg = h_flask.tofpga_message_creator.json_to_post_message(recv_json)
        if not h_flask.tofpga_message_sender.send_mem_to_fpga(post_msg):
            result_code = 10000
            failed_message = "SEND TO FPGA FAILED"
    else:
        result_code = 10000
        failed_message = "JSON FORMAT ERROR"

    return json.dumps({
        "result": result_code,
        "message": failed_message
    })


@h_flask.route("/policy", methods=["POST"])
def flask_route_recv_policy() -> str:
    """
    for recv policy message, and tcp send to cmp
    :return: always 200OK, and {"result": 200/10000/10001, message: ""} 200 is success, 10000/100001 is failed.
    """
    recv_json = None
    result_code = 200
    message = ""

    try:
        recv_json = json.loads(request.data)
    except Exception:
        h_flask.wiser_elf.traceback()
        h_flask.wiser_elf.statistic("GET_UI_POLICY_MEM_TO_JSON_FAILED")

    if "PolicyType" in recv_json and recv_json["PolicyType"] not in ("resource_group_check", "resource_group"):
        byte_string = h_flask.tocmp_message_creator.json_to_byte_string(recv_json)
        if byte_string != b"resource_word" and (not byte_string or not h_flask.tocmp_message_sender.send_mem_to_cmp(byte_string)):
            result_code = 10000
            message = "SEND TO CMP FAILED"
        else:
            h_flask.totimemanager_policy_changer.change_format_and_send_to_manager(
                recv_json["PolicyMem"],
                "add" if recv_json["Bind_Action"] == 0x01 else "del"
            ) if recv_json["PolicyType"] == "policy_bind" and "PolicyMem" in recv_json else None
    elif "PolicyType" in recv_json and recv_json["PolicyType"] in ("resource_group_check", "resource_group"):
        resource_handle = ftp_get_resource.FtpGetResource(h_flask.wiser_elf)
        resource_handle.set_resource_original_file_and_ftp_info(recv_json)
        resource_handle.download_resource_original_file()
        result_code, message = resource_handle.run_and_return_result()
    else:
        result_code = 10000
        message = "JSON FORMAT ERROR"

    return json.dumps({
        "result": result_code,
        "message": message
    })


@h_flask.route("/set_fpga_ip_map", methods=["POST"])
def flask_route_recv_fpga_map() -> str:
    """
    for recv fpga dev map
    :return: {"result": 200/10000/10001, message: ""}
    """
    recv_json = None
    result_code = 200
    failed_message = ""

    try:
        recv_json = json.loads(request.data)
    except Exception:
        h_flask.wiser_elf.traceback()
        h_flask.wiser_elf.statistic("GET_UI_FPGA_MAP_MEM_TO_JSON_FAILED")

    if recv_json:
        h_flask.wiser_elf.get_global_config_args()["fpga_dev_map"] = recv_json
    else:
        result_code = 10000
        failed_message = "JSON FORMAT ERROR OR NO MESSAGE"

    return json.dumps({
        "result": result_code,
        "message": failed_message
    })


class HFlask(multiprocessing.Process):
    """
    for recv post message by Flask
    """
    def __init__(self, wiser_elf: wiserelf.WiserElf):
        multiprocessing.Process.__init__(self)
        h_flask.h_init(wiser_elf)

    def run(self) -> None:
        """
        start function
        """
        h_flask.run(
            host=h_flask.wiser_elf.get_static_config_args()["common"]["http_ip"],
            port=h_flask.wiser_elf.get_static_config_args()["common"]["http_port"],
        )


def create_default_path(wiser_elf: wiserelf.WiserElf) -> None:
    """
    for create default path
    :param wiser_elf: wiser elf class var
    """
    for path_point in [
        wiser_elf.get_static_config_args()["path"]["bak_path"],
        wiser_elf.get_static_config_args()["path"]["resource_word_path"],
        wiser_elf.get_static_config_args()["path"]["resource_lib_path"],
        wiser_elf.get_static_config_args()["path"]["original_feature_file_path"],
        wiser_elf.get_static_config_args()["path"]["resource_tmp_path"],
        "/home/test/proto"
    ]:
        os.makedirs(path_point) if not os.access(path_point, os.F_OK) else None


def get_fpga_dev_map(wiser_elf: wiserelf.WiserElf) -> None:
    """
    for init dev map
    :param wiser_elf: wiser elf class var
    """
    ui_address = "http://%s:%d/wangguan/index.php/api/get_fpga_ip_map" % (
        wiser_elf.get_static_config_args()["common"]["ui_ip"],
        wiser_elf.get_static_config_args()["common"]["ui_port"]
    )
    try:
        # request_post = requests.get(ui_address)
        request_post = requests.post(ui_address, json={})
    except Exception:
        wiser_elf.traceback()
        wiser_elf.statistic("GET_FPGA_MAP_JSON_FROM_UI_FAILED_CONNECT")
        return

    request_result = None

    try:
        request_result = json.loads(request_post.text)
    except Exception:
        wiser_elf.traceback()
        wiser_elf.statistic("GET_FPGA_MAP_JSON_FROM_UI_FORMAT_ERROR")

    # request_result = {"1": "10.80.3.163"}
    # request_result = {"1": "10.94.83.10"}

    if request_result:
        wiser_elf.get_global_config_args()["fpga_dev_map"] = request_result


def toml_default_config() -> dict:
    """
    return default toml config
    :return: default toml config
    """
    return {
        "common": {
            "http_ip": "127.0.0.1",
            "http_port": 60606,
            "cmp_ip": "127.0.0.1",
            "cmp_port": 50000,
            # "fpga_ip": "127.0.0.1",
            "fpga_port": 80,
            "ui_ip": "127.0.0.1",
            "ui_port": 80,
            "policy_id_num": 10000
        },
        "path": {
            "bak_path": "bak",
            "resource_word_path": "bak/resource_word/proto",
            "resource_lib_path": "bak/resource_lib/proto",
            "original_feature_file_path": "feature_file",
            "resource_tmp_path": "resource_tmp_path"
        },
        "local_ftp": {
            "ftp_ip": "127.0.0.1",
            "ftp_port": 21,
            "ftp_username": "test",
            "ftp_password": "123456",
            "ftp_path": "/home/test",
            "resource_file_name": "resource_word.tar.gz"
        },
        "resource_change": {
            "big_type": 67,
            "sub_type_start": 70000,
            "check_file": "/home/python.txt",
            "local_dpi_proto": "dpi.proto",
        },
        "mysql": {
            "host": "127.0.0.1",
            "port": 3306,
            "user": "root",
            "password": "byzoro",
            "db": "cu",
        }
    }


def read_toml_config(wiser_elf: wiserelf.WiserElf) -> None:
    """
    for read toml config to wiser_elf, create default config when toml read error.
    :param wiser_elf: wiser_elf class var
    """
    config_name = wiser_elf.get_default_config_name()
    config_dict = {}
    if os.access(config_name, os.F_OK):
        with open(config_name) as rp:
            try:
                config_dict = toml.load(rp)
            except Exception:
                 wiser_elf.traceback()
    if config_dict:
        for config_key in config_dict:
            wiser_elf.get_static_config_args()[config_key] = config_dict[config_key]
    else:
        with open(config_name, "w") as fp:
            toml.dump(toml_default_config(), fp)
            wiser_elf.error("Create Toml Config Complete, Please Start Project again~")


def cmd_show_statistic(wiser_elf: wiserelf.WiserElf, conn: socket.socket) -> None:
    """
    cmd for show show_statistic
    @param wiser_elf: wiser elf class var
    @param conn: socket connect
    """
    statistic_msg = []
    key_name_max_len = 0
    for key_name in wiser_elf.get_statistical_args().keys():
        key_name_max_len = len(key_name) if len(key_name) > key_name_max_len else key_name_max_len
    for key_name in wiser_elf.get_statistical_args().keys():
        show_key_name = " %s" % key_name + (
            " " if key_name_max_len > len(key_name) else "") + "-" * (key_name_max_len - len(key_name) - 1) + " "
        if wiser_elf.get_statistical_args()[key_name]:
            statistic_msg.append("[%s]: [%d]" % (show_key_name, wiser_elf.get_statistical_args()[key_name]))
        else:
            False and statistic_msg.append("[%s]: [ZERO]" % show_key_name)
    conn.sendall(wiser_elf.send_last_msg("\r\n".join(statistic_msg)).encode()) if statistic_msg else None


def cmd_set_traceback_switch(wiser_elf: wiserelf.WiserElf, conn: socket.socket) -> None:
    """
    cmd set traceback print switch
    :param wiser_elf: wiser elf class var
    :param conn: socket connect
    """
    wiser_elf.cmd_base_for_set_type(conn, {
        ("global", "traceback", bool): "please input 1 or 0 or exit or jump?"
    })


def cmd_send_delete_all_to_fpga(wiser_elf: wiserelf.WiserElf, conn: socket.socket) -> None:
    """
    cmd send delete all policy message to fpga
    :param wiser_elf: wiser elf class var
    :param conn: socket connect
    """
    fpga_address_list = list(map(
        lambda x: "http://%s:%d/api/policy/%s" % (
            wiser_elf.get_global_config_args()["fpga_dev_map"][x],
            wiser_elf.get_static_config_args()["common"]["fpga_port"],
            "delete"
        ),
        wiser_elf.get_global_config_args()["fpga_dev_map"]
    ))

    send_result = {}

    for fpga_address in fpga_address_list:
        try:
            post_to_fpga = requests.post(fpga_address, json={"op": "delete*",  "body": []})
            return_json = json.loads(post_to_fpga.text)
            if post_to_fpga.status_code != 200 or list(filter(lambda x: x["code"] == "0", return_json["body"])):
                send_result[fpga_address.split("/")[2]] = "Send Failed."
            else:
                send_result[fpga_address.split("/")[2]] = "Send Success."
        except Exception:
            send_result[fpga_address.split("/")[2]] = "Send Failed."

    conn.sendall(wiser_elf.send_last_msg(
        "\r\n".join(["%s -> %s" % (x, send_result[x]) for x in send_result]) if send_result else "Nothing Send."
    ).encode())


def cmd_send_reload_to_time_manager(wiser_elf: wiserelf.WiserElf, conn: socket.socket) -> None:
    """
    cmd send reload to time_manager process queue, put tuple ("policy_reset", None) to process queue
    :param wiser_elf: wiser elf class var
    :param conn: socket connect
    """
    wiser_elf.get_process_fifo_args()["->[TimeManager]"].put(("policy_reset", None))
    conn.sendall(wiser_elf.send_last_msg("Set Reload Flag Ok.").encode())


if __name__ == '__main__':
    all_args = wiserelf.WiserElf.init_all_args_var()
    wiserelf.WiserElf.add_cmd_help_msg("input [list] to show all cmd line~", all_args)
    wiserelf.WiserElf.add_cmd_config_group_to_args({
        "show statistic": cmd_show_statistic,
        "set traceback switch": cmd_set_traceback_switch,
        "send delete all to fpga": cmd_send_delete_all_to_fpga,
        "send reload to time manager": cmd_send_reload_to_time_manager
    }, all_args)

    wiserelf.WiserElf.add_cmd_config_for_toml_group_to_args({}, all_args)
    wiserelf.WiserElf.add_static_config_group_to_args({
        "policy_backup_file": "policy_backup.json",
        "token_map_backup_file": "token_map_backup.json",
        "time_point_file": "time_point_backup.json",
        "failed_send_file": "failed_send_file.json"
    }, all_args)
    wiserelf.WiserElf.add_global_config_group_to_args({
        "fpga_dev_map": {}
    }, all_args)

    wiserelf.WiserElf.add_process_fifo_group_to_args({
        "->[TimeManager]": None,
        "->[MysqlKeeper]": None,
    }, all_args)
    wiserelf.WiserElf.add_statistical_group_to_args({
        "POLICY_MANAGER_START_TIMES": 1,
    }, all_args)

    wiserelf.WiserElf.add_init_function_dict_to_args({
        "read_toml_config": read_toml_config,
        "create_default_path": create_default_path,
        "get_fpga_dev_map": get_fpga_dev_map
    }, all_args)
    wiserelf.WiserElf.add_start_function_dict_to_args({}, all_args)
    wiserelf.WiserElf.add_run_function_dict_to_args({}, all_args)
    wiserelf.WiserElf.add_stop_function_dict_to_args({}, all_args)
    wiserelf.WiserElf.add_clean_function_dict_to_args({}, all_args)

    wiserelf.WiserElf.add_process_group_to_args({
        # "HTestClass": HTestClass,
        "TimeManager": timemanager.TimeManager,
        "HFlask": HFlask,
        "ChangeResource": resourcechanger.ChangeResource,
        "MysqlKeeper": tomysql.MysqlKeeper
    }, all_args)
    wiserelf.start_shadow("local", all_args)
