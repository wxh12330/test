import os
import sys
import json
import time
import socket
import logging
import requests
import multiprocessing

import process_frame as wiserelf
import my_process_test as MyTest


if __name__ == '__main__':
    all_args = wiserelf.WiserElf.init_all_args_var()
    wiserelf.WiserElf.add_cmd_help_msg("input [list] to show all cmd line~", all_args)
    wiserelf.WiserElf.add_cmd_config_group_to_args({
        "show statistic": {},
        "set traceback switch": {},
    }, all_args)

    wiserelf.WiserElf.add_cmd_config_for_toml_group_to_args({}, all_args)
    wiserelf.WiserElf.add_static_config_group_to_args({
        "policy_backup_file": "",
        "token_map_backup_file": "",
        "time_point_file": "",
        "failed_send_file": ""
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
        "read_toml_config": {},
        "create_default_path": {},
        "get_fpga_dev_map": {}
    }, all_args)
    wiserelf.WiserElf.add_start_function_dict_to_args({}, all_args)
    wiserelf.WiserElf.add_run_function_dict_to_args({}, all_args)
    wiserelf.WiserElf.add_stop_function_dict_to_args({}, all_args)
    wiserelf.WiserElf.add_clean_function_dict_to_args({}, all_args)

    wiserelf.WiserElf.add_process_group_to_args({
        "MyTest": MyTest.Mytest
    }, all_args)
    wiserelf.start_shadow("local", all_args)