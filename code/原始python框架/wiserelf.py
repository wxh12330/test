# coding=utf-8

"""
a manager for python multiprocessing
"""

import os
import sys
import tty
import toml
import queue
import signal
import socket
import termios
import threading
import traceback
import setproctitle
import multiprocessing


class CitrusError(BaseException):
    """
    Self Error by BaseException
    """
    pass

class WiserElf(object):
    """
    class manager for multiprocessing
    """

    _umask = 0o22

    _init_functions = {}
    _start_functions = {}
    _run_functions = {}
    _stop_functions = {}
    _clean_functions = {}
    _process_list = {}
    _global_config = {}
    _static_config = {}
    _cmd_config = {}
    _cmd_config_for_toml = {}
    _process_fifo = {}
    _statistical = {}

    _cmd_help_msg = "No Help Msg!"

    _default_all_args = {
        "init_functions": {},
        "start_functions": {},
        "run_functions": {},
        "stop_functions": {},
        "clean_functions": {},

        "cmd_config": {},
        "cmd_config_for_toml": {},

        "process_list": {},
        "global_config": {},
        "static_config": {},
        "process_fifo": {},
        "statistical": {},

        "cmd_help": "",
    }

    _is_daemon = True

    _project_name = "luna"
    _config_name = "luna.toml"
    _socket_name = "luna.sock"

    def __init__(self, all_args):
        self._all_args = all_args
        self._init_all_args_to_every_args()
        self._init_project_name(sys.argv[0])
        self._init_config_name()
        self._init_local_socket_name()
        self.start_map = {
            "start": self._start,
            "stop": self._stop,
            "check": self._restart,
            "restart": self._restart,
            "status": self._status,
            "control": self._control,
            "config": self._config,
            "version": self._version,
            "help": self.help,
        }

    def _init_project_name(self, script_path: str) -> None:
        """
        init default config name by python script path
        :param script_path: python script complete path
        """
        self._project_name = script_path.split("/")[-1].split(".")[0]

    def _init_config_name(self) -> None:
        """
        init default config name
        """
        self._config_name = self._project_name + ".toml"

    def _init_local_socket_name(self) -> None:
        """
        init local socket name
        """
        self._socket_name = self._project_name + ".sock"

    def set_ps_show_name(self, name: str) -> None:
        """
        for set process name
        :param name: process name, complete is PROCESS_NAME.project_name.python
        """
        setproctitle.setproctitle("%s.%s.python" % (name.upper(), self._project_name))

    def _init_all_args_to_every_args(self) -> None:
        """
        init all_args to wiser_elf
        """
        self._init_functions = self.get_init_functions_args()
        self._start_functions = self.get_start_functions_args()
        self._run_functions = self.get_run_functions_args()
        self._stop_functions = self.get_stop_functions_args()
        self._clean_functions = self.get_clean_functions_args()

        self._process_list = self.get_process_list_args()
        self._global_config = self.get_global_config_args()
        self._static_config = self.get_static_config_args()
        self._cmd_config = self.get_cmd_config_args()
        self._cmd_config_for_toml = self.get_cmd_config_for_toml_args()
        self._process_fifo = self.get_process_fifo_args()
        self._statistical = self.get_statistical_args()

        self.add_cmd_help_msg(self._cmd_help_msg, self._all_args) if not self.get_cmd_help_msg() else None
        self._cmd_help_msg = self.get_cmd_help_msg()

    def is_only_check(self) -> None:
        """
        for check is only
        """
        try:
            only_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            only_socket.connect(self.get_local_socket_name())
        except Exception:
            pass
        else:
            only_socket.close()
            self.message("is running, please check it, bye~")
            exit(0)

    def _init(self) -> None:
        """
        for init every function
        """
        self.is_only_check()
        for function_name in self._init_functions:
            self._init_functions[function_name](self)

    def _wiser_elf_init_for_start(self) -> None:
        """
        init for start
        """
        signal.signal(signal.SIGHUP, lambda signum, frame: None)
        signal.signal(signal.SIGINT, lambda signum, frame: None)
        signal.signal(signal.SIGQUIT, lambda signum, frame: None)

        try:
            pid = os.fork()
            sys.exit(1) if pid else None
        except OSError as err:
            self.message("fork *1 failed: %d (%s)" % (err.errno, err.strerror))
            sys.exit(1)

        os.setsid()
        os.umask(self._umask)

        try:
            _pid = os.fork()
            sys.exit(1) if _pid else None
        except OSError as err:
            self.message("fork *2 failed: %d (%s)" % (err.errno, err.strerror))
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()

    def _wiser_elf_run_for_start(self) -> None:
        """
        run for start
        """
        for fifo_name in self._process_fifo:
            self._process_fifo[fifo_name] = multiprocessing.Queue(maxsize=100)

        self.set_ps_show_name("_Manager")
        global_manager = multiprocessing.Manager()
        global_config = global_manager.dict()
        statistical = global_manager.dict()

        global_config_tmp = self.get_global_config_args()
        statistical_tmp = self.get_statistical_args()
        for config_name in global_config_tmp:
            global_config[config_name] = global_config_tmp[config_name]
        for statistic_name in statistical_tmp:
            statistical[statistic_name] = statistical_tmp[statistic_name]
        self._global_config = global_config
        self._statistical = statistical
        self.add_global_config_group_to_args(global_config, self._all_args)
        self.add_statistical_group_to_args(statistical, self._all_args)

        self._add_process_to_process_list(
            process_name="_Daemon",
            process_class=None,
            process_pid=os.getpid(),
            process_var=self,
            is_daemon_check=False
        )
        self._add_process_to_process_list(
            process_name="_Manager",
            process_class=None,
            process_pid=global_manager._process.pid,
            process_var=global_manager._process,
            is_daemon_check=False
        )
        for process_name in self._all_args["process_list"]:
            if process_name != "_Manager" and process_name != "_Daemon":
                self.set_ps_show_name(process_name)
                processor = self._all_args["process_list"][process_name](self)
                processor.start()
                self.message("[%s]:[%d] [start]...[ok]" % (process_name, processor.pid))
                self._add_process_to_process_list(
                    process_name=process_name,
                    process_class=self._all_args["process_list"][process_name],
                    process_pid=processor.pid,
                    process_var=processor,
                    is_daemon_check=True
                )
        self.set_ps_show_name("_Daemon")

        for function_name in self._start_functions:
            self._start_functions[function_name](self)

    def _read_control_msg_from_fifo(self, action_type: str) -> None:
        """
        read cmd msg from fifo, now only stop all
        :param action_type: msg from control process send message fifo
        """
        if action_type == "stop all process":
            for process_name in self._process_list:
                if process_name != "_Daemon":
                    self._process_list[process_name]["process_var"].terminate()
            exit(0)
        elif action_type == "all process status":
            result_list = ["[_Daemon] ->> [RUNNING], Pid is [%d]" % os.getpid()]
            for process_name in self._process_list:
                if process_name != "_Daemon":
                    processor_dict = self._process_list[process_name]
                    processor_status = "RUNNING" if processor_dict["process_var"].is_alive() else "*TERMINATE"
                    result_list.append("[%s] ->> [%s], Pid is [%d]" % (
                        process_name,
                        processor_status,
                        processor_dict["process_pid"]
                    ))
            self._process_fifo["->[Listener]"].put("\r\n".join(result_list))

    def _wiser_elf_daemon_for_start(self) -> None:
        """
        for check fifo and every process status
        """
        while True:
            for function_name in self._run_functions:
                self._run_functions[function_name](self)
            try:
                self._read_control_msg_from_fifo(self._process_fifo["[Listener]->"].get(timeout=1))
            except queue.Empty:
                for process_name in self._process_list:
                    self._restart_for_terminate_process(process_name) if self._is_daemon else None

    def _start(self) -> None:
        """
        for start every function
        """
        self._init()
        self._wiser_elf_init_for_start()
        self._wiser_elf_run_for_start()
        self._wiser_elf_daemon_for_start()

    def _restart_for_terminate_process(self, process_name) -> None:
        """
        for restart process
        :param process_name: process key name
        """
        self.set_ps_show_name(process_name)
        if self._process_list[process_name]["is_daemon_check"]:
            if not self._process_list[process_name]["process_var"].is_alive():
                self._process_list[process_name]["process_var"].terminate()

                processor = self._process_list[process_name]["process_class"](self)
                processor.start()
                self.message("[%s]:[%d] [restart]...[ok]" % (process_name, processor.pid))
                self._add_process_to_process_list(
                    process_name=process_name,
                    process_class=self._process_list[process_name]["process_class"],
                    process_pid=processor.pid,
                    process_var=processor,
                    is_daemon_check=True
                )
        self.set_ps_show_name("_Daemon")

    def _add_process_to_process_list(
            self, process_name: str, process_class, process_pid: int, process_var, is_daemon_check: bool
    ) -> None:
        """
        for add a process to process list
        :param process_name: process name
        :param process_class: class name
        :param process_pid: process id
        :param process_var: process var
        :param is_daemon_check: is do daemon check
        """
        self._process_list[process_name] = {
            "process_class": process_class,
            "process_pid": process_pid,
            "process_var": process_var,
            "is_daemon_check": is_daemon_check
        }

    def _stop(self) -> None:
        """
        go to control function, args[once is True, type is stop]
        """
        for function_name in self._stop_functions:
            self._stop_functions[function_name](self)
        self._control(once=True, function_type="stop")
        for function_name in self._clean_functions:
            self._clean_functions[function_name](self)
        self.message("Already kill all........and bye!")

    def stop(self) -> None:
        """
        go to control function, args[once is True, type is stop]
        """
        self._stop()

    def _restart(self) -> None:
        """
        stop and start again
        """
        self._stop()
        self._start()

    def _clean(self) -> None:
        """
        for clean config
        """
        for function_name in self._clean_functions:
            self._clean_functions[function_name](self)

    def re_init(self) -> None:
        """
        for init again, no useful
        """
        self._clean()
        self._init()

    def _control(self, once=False, function_type="keep") -> None:
        """
        for send cmd to local socket
        :param once: is one cmd
        :param function_type: type [keep or other]
        """
        Control(self).link(once, function_type)

    def _start_config(self, config_dict: dict) -> None:
        """
        for start config toml file
        :param config_dict: config mem
        """
        control = Control(self)

        def list_cmd() -> None:
            """
            show cmd list
            """
            control.print_with_flush("\r\n".join([
                "list",
                "show all config",
                "save_config",
                "set CONFIG VALUE",
                "exit"
            ]))

        def show_all_config() -> None:
            """
            show now toml config
            """
            control.print_with_flush(toml.dumps(config_dict))
            control.print_with_flush("\r\n")

        def save_config() -> None:
            """
            save toml config to file
            """
            with open(self._config_name, "w") as wp:
                toml.dump(config_dict, wp)
            control.print_with_flush("save config ok.\r\n")

        def set_config_value(*arg) -> bool:
            """
            for set config key value
            :param arg: set key and value
            :return: success: True， failed： False
            """
            config_dict_shadow = config_dict
            key_point_list = arg[0].split(".")
            for key_point in key_point_list:
                if key_point in config_dict_shadow:
                    config_dict_shadow = config_dict_shadow[key_point] \
                        if key_point_list[-1] != key_point else config_dict_shadow
                else:
                    return False

            if type(config_dict_shadow[key_point_list[-1]]) == dict:
                return False
            elif type(config_dict_shadow[key_point_list[-1]]) == list:
                if len(config_dict_shadow[key_point_list[-1]]) and type(config_dict_shadow[key_point_list[-1]]) != str:
                    return False
                else:
                    config_dict_shadow[key_point_list[-1]] = list(arg[1:])
                    return True
            elif type(config_dict_shadow[key_point_list[-1]]) == int:
                try:
                    config_dict_shadow[key_point_list[-1]] = int(arg[1])
                except Exception:
                    return False
                return True
            elif type(config_dict_shadow[key_point_list[-1]]) == str:
                config_dict_shadow[key_point_list[-1]] = arg[1]
                return True

        cmd_string = ""
        function_dict = {
            "list": list_cmd,
            "show all config": show_all_config,
            "save config": save_config,
            "exit": exit
        }

        print(self.get_cmd_help_msg())
        while True:
            control.print_with_flush(">>>")
            cmd_string = control.input_new_chr(cmd_string)
            cmd_string = " ".join(filter(lambda x: x, cmd_string.split(" ")))
            if cmd_string in function_dict:
                function_dict[cmd_string]()
            else:
                cmd_point = cmd_string.split(" ")
                if len(cmd_point) >= 3 and cmd_point[0] == "set":
                    control.print_with_flush("set success~" if set_config_value(*cmd_point[1:]) else "Failed.")
                else:
                    control.print_with_flush("Error Input!")
                control.print_with_flush("\r\n")

            cmd_string = ""

    def _config(self) -> None:
        """
        for config toml file
        """
        self._init()
        self.error("No Config, [%s] is not exist." % self._config_name) \
            if not os.access(self._config_name, os.F_OK) else None

        config_dict = {}
        with open(self._config_name) as rp:
            try:
                config_dict = toml.load(rp)
            except Exception:
                self.error("[%s] is not a toml, please check it." % self._config_name)

        self._start_config(config_dict)

    def _version(self) -> None:
        """
        for show version by version file
        """
        for file_point in os.listdir("./"):
            if "version" in file_point and "version" == file_point.split(".")[0] and len(file_point) > len("version."):
                self.message("[VERSION]: %s" % file_point[len("version."):], level="point")

    def _status(self) -> None:
        """
        go to control function, args[once is True, type is status]
        """
        self._control(once=True, function_type="status")

    def error(self, error_msg: str) -> None:
        """
        for raise a error message
        :param error_msg: a string
        """
        raise CitrusError("*--> [%s]" % error_msg)

    @staticmethod
    def message(msg: str, level: str = "info") -> None:
        """
        show a message by print function
        :param msg: a string
        :param level: level in [error: red, warning: yellow, warn:yellow, info: no color, point: blue, special: blue]
        """
        print("\r\33[K..> %s%s%s" % (
            {
                "error": "\33[31m",
                "warn": "\33[33m",
                "warning": "\33[33m",
                "info": "",
                "point": "\33[34m",
                "special": "\33[35m""SPECIAL START\r\n""\33[34m"
            }[level if level in ["error", "warn", "warning", "info", "point", "special"] else "info"],
            msg,
            ("" if msg and msg[-1] == "\n" else "\r\n") + "\33[35mSPECIAL END\33[0m" if level == "special" else "\33[0m"
        ))

    def get_traceback(self) -> None:
        """
        for get tracback message and print it with blue color
        """
        self.message(traceback.format_exc(), level="special")

    @staticmethod
    def create_abs_path_string(root_path: str, *args) -> str:
        """
        for create abs path to complete path string
        :param root_path: root path
        :param args: every path point
        :return: abs path
        """
        return "/".join([root_path, *args])

    def help(self) -> None:
        """
        help message
        """
        print("*--> Invalid Argument!!")
        print("Usage: %s <%s>" % (sys.argv[0].split("/")[-1].split(".")[0], "|".join(self.start_map.keys())))
        exit(1)

    @staticmethod
    def no_use(*args, **kwargs) -> None:
        """
        for set no use
        :param args: *
        :param kwargs: *
        """
        pass

    @classmethod
    def init_all_args_var(cls) -> dict:
        """
        init all_args
        :return: all args dict
        """
        return cls._default_all_args

    @classmethod
    def add_process_group_to_args(cls, process_group: dict, all_args: dict) -> None:
        """
        add a process group to all args
        :param process_group: process group {name, class type, pid, var}
        :param all_args: all args
        """
        all_args["process_list"] = {"_Listener": Listener, **process_group}

    def get_process_list_args(self) -> dict:
        """
        for get process list var
        :return: process list var in wiser_elf
        """
        return self._all_args["process_list"]

    def traceback(self) -> None:
        """
        print traceback message with special color
        """
        self.get_global_config_args()["traceback"] and self.message(traceback.format_exc(), level="special")

    def set_traceback(self, status: bool) -> None:
        """
        set traceback print status
        :param status: True / False
        """
        self.get_global_config_args()["traceback"] = status

    @classmethod
    def add_global_config_group_to_args(cls, global_config_group: dict, all_args: dict) -> None:
        """
        add a global config group to args
        :param global_config_group: global config {key: value}
        :param all_args: all args
        """
        all_args["global_config"] = {"traceback": True, **global_config_group} \
            if isinstance(global_config_group, dict) else global_config_group

    def get_global_config_args(self) -> dict:
        """
        for get global config var
        :return: global config var in wiser_elf
        """
        return self._all_args["global_config"]

    @classmethod
    def add_static_config_group_to_args(cls, static_config_group: dict, all_args: dict) -> None:
        """
        add a static config group to args
        :param static_config_group: static config {key: value}
        :param all_args: all args
        """
        all_args["static_config"] = static_config_group

    def get_static_config_args(self) -> dict:
        """
        for get static config var
        :return: static config var in wiser_elf
        """
        return self._all_args["static_config"]

    def cmd_base_for_set_type(self, conn:socket.socket, where_and_message: dict) -> None:
        """
        cmd base to set value for set type cmd
        :param conn: socket connect
        :param where_and_message: key is where, value is point message
        """
        for key_point in where_and_message:
            (big_type, big_key, change_type) = key_point
            big_type = {"global": self.get_global_config_args(), "static": self.get_static_config_args()}[big_type] \
                if big_type in ["global", "static"] else big_type
            if big_type is self.get_global_config_args() or big_type is self.get_static_config_args():
                conn.send(self.send_keep_msg(where_and_message[key_point]).encode())
                return_mem = conn.recv(1024).decode()
                if return_mem == "exit":
                    conn.sendall(self.send_last_msg("bye~").encode())
                    return
                elif return_mem == "jump":
                    continue
                else:
                    config_shadow = big_type
                    big_type_point = big_key.split(".")
                    for value_get in big_type_point:
                        try:
                            if value_get is big_type_point[-1]:
                                config_shadow[value_get] = change_type(int(return_mem)) \
                                    if change_type == bool else change_type(return_mem)
                            else:
                                config_shadow = config_shadow[value_get]
                        except Exception:
                            self.traceback()
                            conn.sendall(self.send_last_msg("Error, nothing set.").encode())
                            return
            else:
                self.message("Invalid Big Type.", level="error")
                conn.sendall(self.send_last_msg("now over~").encode())
                return

        conn.sendall(self.send_last_msg("set complete~").encode())

    @classmethod
    def add_cmd_config_group_to_args(cls, cmd_config_group: dict, all_args: dict) -> None:
        """
        add a cmd config group to args
        :param cmd_config_group: cmd config {key: function}
        :param all_args: all args
        """
        all_args["cmd_config"] = cmd_config_group
        all_args["cmd_config"]["list"] = None
        all_args["cmd_config"]["exit"] = None

    def get_cmd_config_args(self) -> dict:
        """
        for get cmd config var
        :return: cmd config var
        """
        return self._all_args["cmd_config"]

    @classmethod
    def add_cmd_config_for_toml_group_to_args(cls, cmd_config_for_toml_group: dict, all_args: dict) -> None:
        """
        add a cmd config for toml group to args, now not need
        :param cmd_config_for_toml_group: cmd config {key: function}
        :param all_args: all args
        """
        all_args["cmd_config_for_toml"] = cmd_config_for_toml_group
        # all_args["cmd_config_for_toml"]["list"] = None
        # all_args["cmd_config_for_toml"]["exit"] = None
        # all_args["cmd_config_for_toml"]["set CONFIG VALUE"] = None
        # all_args["cmd_config_for_toml"]["save config"] = None

    def get_cmd_config_for_toml_args(self) -> dict:
        """
        for get cmd config for toml var
        :return: cmd config var
        """
        return self._all_args["cmd_config_for_toml"]

    @classmethod
    def add_process_fifo_group_to_args(cls, process_fifo_group: dict, all_args: dict) -> None:
        """
        add a process fifo group to args
        :param process_fifo_group: process fifo config {key: fifo}
        :param all_args: all args
        """
        all_args["process_fifo"] = process_fifo_group
        all_args["process_fifo"]["[Listener]->"] = None
        all_args["process_fifo"]["->[Listener]"] = None

    def get_process_fifo_args(self) -> dict:
        """
        for get process fifo var
        :return: process fifo var in wiser_elf
        """
        return self._all_args["process_fifo"]

    @classmethod
    def add_statistical_group_to_args(cls, statistic_group: dict, all_args: dict) -> None:
        """
        for add statistical group to args
        :param statistic_group: statistical {key: value}
        :param all_args: all args
        """
        all_args["statistical"] = statistic_group

    def get_statistical_args(self) -> dict:
        """
        for get statistic var
        :return: statistic var in wiser_elf
        """
        return self._all_args["statistical"]

    @classmethod
    def add_init_function_dict_to_args(cls, init_functions: dict, all_args: dict) -> None:
        """
        for add init function var
        :param init_functions: init function dict
        :param all_args: all args
        """
        all_args["init_functions"] = init_functions

    def get_init_functions_args(self) -> dict:
        """
        for get init functions var
        :return: init functions var in wiser_elf
        """
        return self._all_args["init_functions"]

    @classmethod
    def add_start_function_dict_to_args(cls, start_function: dict, all_args: dict) -> None:
        """
        for add start function var
        :param start_function: start function dict
        :param all_args: all args
        """
        all_args["start_functions"] = start_function

    def get_start_functions_args(self) -> dict:
        """
        for get start functions var
        :return: start functions var in wiser_elf
        """
        return self._all_args["start_functions"]

    @classmethod
    def add_run_function_dict_to_args(cls, run_function: dict, all_args: dict) -> None:
        """
        for add run function var
        :param run_function: run function dict
        :param all_args: all args
        """
        all_args["run_functions"] = run_function

    def get_run_functions_args(self) -> dict:
        """
        for get run functions var
        :return: run functions var in wiser_elf
        """
        return self._all_args["run_functions"]

    @classmethod
    def add_stop_function_dict_to_args(cls, stop_function: dict, all_args: dict) -> None:
        """
        for add stop function var
        :param stop_function: stop function dict
        :param all_args: all args
        """
        all_args["stop_functions"] = stop_function

    def get_stop_functions_args(self) -> dict:
        """
        for get stop functions var
        :return: stop functions var in wiser_elf
        """
        return self._all_args["stop_functions"]

    @classmethod
    def add_clean_function_dict_to_args(cls, clean_function: dict, all_args: dict) -> None:
        """
        for add clean function var
        :param clean_function: clean function dict
        :param all_args: all args
        """
        all_args["clean_functions"] = clean_function

    def get_clean_functions_args(self) -> dict:
        """
        for get clean functions var
        :return: clean functions var in wiser_elf
        """
        return self._all_args["clean_functions"]

    def to_do_daemon(self, is_daemon: bool) -> None:
        """
        set daemon status by is_daemon
        :param is_daemon: status
        """
        self._is_daemon = is_daemon

    def get_default_config_name(self) -> str:
        """
        for get default config name
        :return: default config name
        """
        return self._config_name

    def get_local_socket_name(self) -> str:
        """
        for get local socket name
        :return: local socket name
        """
        return self._socket_name

    @classmethod
    def add_cmd_help_msg(cls, msg: str, all_args: dict) -> None:
        """
        for add cmd help msg var
        :param msg: help msg
        :param all_args: all args
        """
        all_args["cmd_help"] = msg

    def get_cmd_help_msg(self) -> str:
        """
        for get cmd help msg
        :return: cmd help msg
        """
        return self._all_args["cmd_help"]

    @staticmethod
    def send_last_msg(msg: str) -> str:
        """
        for send last msg by local socket add string "last"
        @param msg: original string
        @return: "last:" + string
        """
        return "last:" + msg

    @staticmethod
    def send_keep_msg(msg: str) -> str:
        """
        for send keep msg by local socket add string "keep"
        @param msg: original string
        @return: "keep:" + string
        """
        return "keep:" + msg

    def statistic(self, statistic_name) -> None:
        """
        statistic + 1
        @param statistic_name: statistic name
        """
        self.get_statistical_args()[statistic_name] = \
            (self.get_statistical_args()[statistic_name] if statistic_name in self.get_statistical_args() else 0) + 1


class Control(object):
    """
    cmd client to link service by local socket(unix socket)
    """

    _local_socket = None
    _alone = True

    def __init__(self, wiser_elf: WiserElf):
        self.wiser_elf = wiser_elf

    def connect_to_local_socket(self) -> None:
        """
        for connect to local socket
        """
        try:
            self._local_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._local_socket.connect(self.wiser_elf.get_local_socket_name())
        except Exception:
            self._alone = True

    def once_connect(self, function_type: str) -> None:
        """
        send once
        @param function_type: get msg type
        """
        if self._alone:
            self.wiser_elf.message("No Process!")
            exit(0)
        else:
            if function_type == "stop":
                self._local_socket.sendall("stop all process".encode())
            elif function_type == "status":
                self._local_socket.sendall("all process status".encode())
            else:
                self._local_socket.sendall(function_type.encode())
            return_msg = self._local_socket.recv(1024).decode()
            self.wiser_elf.message(return_msg) if return_msg else None

    @staticmethod
    def get_input_chr() -> str:
        """
        get one chr
        @return: one chr
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
            input_chr = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return input_chr

    @staticmethod
    def print_with_flush(one_str: str) -> None:
        """
        for print string with flush()
        @param one_str: one string
        """
        sys.stdout.write(one_str)
        sys.stdout.flush()

    def input_new_chr(self, msg) -> str:
        """
        for get new chr to msg
        @param msg: original msg
        @return: new msg
        """
        while True:
            one_chr = self.get_input_chr()
            if ord(one_chr) == 8:
                self.print_with_flush("\33[1D\33[K") if len(msg) else None
                msg = msg[0:-1] if len(msg) else msg
            elif ord(one_chr) == 10 or ord(one_chr) == 13:
                self.print_with_flush("\r\n")
                break
            elif 32 <= ord(one_chr) <= 126:
                msg += one_chr
                self.print_with_flush(one_chr)
        return msg

    def keep_connect(self) -> None:
        """
        keep connect
        """
        msg = ""
        print(self.wiser_elf.get_cmd_help_msg())
        self.wiser_elf.message("No Process!") if self._alone else None
        exit(0) if self._alone else None
        while True:
            self.print_with_flush(">>>")
            msg = self.input_new_chr(msg)
            msg = " ".join(filter(lambda x: x, msg.split(" ")))
            if msg == "exit":
                break
            elif msg:
                while True:
                    try:
                        self._local_socket.sendall(msg.encode())
                    except BrokenPipeError:
                        self.wiser_elf.message("Connect is over, See you!")
                        return
                    return_mem = self._local_socket.recv(65536).decode()
                    self.print_with_flush(return_mem[5:])
                    if return_mem[0:5] == "last:":
                        self.print_with_flush("\r\n")
                        break
                    else:
                        while True:
                            msg = self.input_new_chr("")
                            if msg:
                                break
                            else:
                                self.print_with_flush("length is 0, input again?")
            msg = ""

    def is_alone(self) -> bool:
        """
        check local socket file is exist
        @return: bool exist or not exist
        """
        self._alone = not os.access(self.wiser_elf.get_local_socket_name(), os.F_OK)
        return self._alone

    def link(self, once=False, function_type="keep") -> None:
        """
        start function
        :param once: is once
        :param function_type: type [keep or other]
        """
        self.connect_to_local_socket() if not self.is_alone() else None
        if not once:
            self.keep_connect()
        else:
            self.once_connect(function_type)


class ListenPoint(threading.Thread):
    """
    cmd server point
    """

    def __init__(self, conn: socket.socket, wiser_elf: WiserElf):
        threading.Thread.__init__(self)
        self.wiser_elf = wiser_elf
        self.conn = conn

    def get_wiser_elf(self) -> WiserElf:
        """
        for get wiser elf class var
        @return: wiser elf class var
        """
        return self.wiser_elf

    def get_conn(self) -> socket.socket:
        """
        for get socket connect
        @return: socket connect
        """
        return self.conn

    def hear(self, msg) -> None:
        """
        hear a msg by local socket
        """
        msg = " ".join(filter(lambda x: x, msg.split(" ")))
        if msg == "stop all process":
            self.wiser_elf.get_process_fifo_args()["[Listener]->"].put("stop all process")
            self.conn.sendall(self.wiser_elf.get_process_fifo_args()["->[Listener]"].get().encode())
            exit(0)
        elif msg == "all process status":
            self.wiser_elf.get_process_fifo_args()["[Listener]->"].put("all process status")
            self.conn.sendall(self.wiser_elf.get_process_fifo_args()["->[Listener]"].get().encode())
        elif msg in self.wiser_elf.get_cmd_config_args():
            if msg == "list":
                self.conn.sendall(
                    self.wiser_elf.send_last_msg("\r\n".join(self.wiser_elf.get_cmd_config_args().keys())).encode()
                )
            else:
                self.wiser_elf.get_cmd_config_args()[msg](self.wiser_elf, self.conn)
        else:
            self.conn.sendall(self.wiser_elf.send_last_msg("Error Input!").encode())

    def run(self) -> None:
        """
        for run thread
        """
        while True:
            recv_mem = self.conn.recv(1024).decode()
            if recv_mem:
                self.hear(recv_mem)
            else:
                self.conn.close()
                break


class Listener(multiprocessing.Process):
    """
    cmd server by local socket(unix socket)
    """

    _socket_name = ""
    _local_socket = None

    def __init__(self, wiser_elf: WiserElf):
        multiprocessing.Process.__init__(self)
        self.wiser_elf = wiser_elf
        self._socket_name = self.wiser_elf.get_local_socket_name()

    def _init_local_socket_service(self) -> None:
        """
        for init local socket service
        """
        os.remove(self._socket_name) if os.access(self._socket_name, os.F_OK) else None
        self._local_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._local_socket.bind(self._socket_name)
        self._local_socket.listen(100)

    def run(self) -> None:
        """
        for run process
        """
        self._init_local_socket_service()
        while True:
            conn, _ = self._local_socket.accept()
            ListenPoint(conn, self.wiser_elf).start()


def start_shadow(work_path: str, all_args: dict) -> None:
    """
    for really start every function
    :param work_path: work path is root path, pwd is work path
    :param all_args: all args, is dict
    """
    wiser_elf = WiserElf(all_args)
    work_path = "/".join(sys.argv[0].split("/")[:-1]) if not work_path or work_path == "local" else work_path
    os.chdir(work_path) if os.access(work_path, os.F_OK) else os.mkdir(work_path) or os.chdir(work_path)
    wiser_elf.help() or wiser_elf.error("len(sys.argv) < 2") \
        if len(sys.argv) < 2 else wiser_elf.message("argv is " + str([sys.argv[0].split("/")[-1], *sys.argv[1:]]))
    wiser_elf.start_map[sys.argv[1]]() if sys.argv[1] in wiser_elf.start_map.keys() else wiser_elf.help()
