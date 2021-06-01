1.python文件生成二进制可执行文件
    {
  "TARGET.ELF": "my_test",
  "TARGET.SO": "my_test.so",
  "TARGET.O": [],
  "TARGET.PYX": [],
  "TARGET.PYX -> TARGET.C": {
    "my_test.py": "main.c"
  },
  "TARGET.C": []
}

2.my_test.py为自定义脚本
3.执行python* make.shadow.py