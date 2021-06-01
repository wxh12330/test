#!/usr/bin/python3.8.3
# coding=utf-8

"""
Makefile shadow for make
"""

import os
import sys
import json


def make_json_init() -> None:
    """
    create Makefile json
    """
    with open("target.json", "w") as wp:
        json.dump({
            "TARGET.ELF": "",
            "TARGET.SO": "",
            "TARGET.O": [],
            "TARGET.PYX": [],
            "TARGET.PYX -> TARGET.C": {
                "": ""
            },
            "TARGET.C": []
        }, wp)


def make_json_clean() -> None:
    """
    remove Makefile config
    """
    if os.access("target.json", os.F_OK):
        os.remove("target.json")


def make_by_json():
    """
    replace TARGET and make
    """
    with open("target.json") as rp:
        makefile_config = json.load(rp)
        makefile_config["TARGET.PYX"] = makefile_config["TARGET.PYX -> TARGET.C"].keys()
        makefile_config["TARGET.C"] = [
            *makefile_config["TARGET.C"],
            *makefile_config["TARGET.PYX -> TARGET.C"].values()
        ]
        makefile_config["TARGET.O"] = [
            *makefile_config["TARGET.O"],
            *list(map(lambda x: x.replace(".c", ".o"), makefile_config["TARGET.C"]))
        ]

    with open("Makefile.shadow") as rp:
        makefile_mem = rp.read()
        makefile_mem = makefile_mem.replace("TARGET.C", " ".join(makefile_config["TARGET.C"]))
        makefile_mem = makefile_mem.replace("TARGET.O", " ".join(makefile_config["TARGET.O"]))
        makefile_mem = makefile_mem.replace("TARGET.ELF", makefile_config["TARGET.ELF"]) \
            if "main.c" in makefile_config["TARGET.C"] else \
            makefile_mem.replace("TARGET.SO", makefile_config["TARGET.SO"])

    with open("Makefile", "w") as wp:
        wp.write(makefile_mem)

    for pyx_file in makefile_config["TARGET.PYX -> TARGET.C"]:
        print("cython -3 %s %s -o %s" % (
            pyx_file, "--embed" if makefile_config["TARGET.PYX -> TARGET.C"][pyx_file] == "main.c" else "",
            makefile_config["TARGET.PYX -> TARGET.C"][pyx_file]
        ))
        os.system("cython -3 %s %s -o %s" % (
            pyx_file, "--embed" if makefile_config["TARGET.PYX -> TARGET.C"][pyx_file] == "main.c" else "",
            makefile_config["TARGET.PYX -> TARGET.C"][pyx_file]
        ))
        print("cython -3 -a %s" % pyx_file)
        os.system("cython -3 -a %s" % pyx_file)

    os.system("make all") if "main.c" in makefile_config["TARGET.C"] else None
    os.system("make shared") if "main.c" not in makefile_config["TARGET.C"] else None


def error_message(_unknown_function: list) -> bool:
    """
    echo unknown function
    """
    print("unknown_function", _unknown_function)
    return True


if __name__ == '__main__':
    function_map = {
        "init": make_json_init,
        "clean": make_json_clean,
    }
    unknown_function = list(filter(lambda x: x not in function_map, sys.argv[1:]))
    error_message(unknown_function) and exit() if unknown_function else None

    function_list = list(filter(lambda x: x in function_map, sys.argv[1:]))
    list(map(lambda x: function_map[x](), function_list)) and exit() if function_list else None

    make_by_json()
