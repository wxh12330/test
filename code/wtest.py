
import os
import multiprocessing


class Wtest(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self) -> None:
        pass

if __name__ == '__main__':
    test = Wtest()
    test.start()
    #print(test.pid)
    print(test)
    a = multiprocessing.Manager()
    print(os.getpid())
    print(a._process.pid)
    print(a._process)

    a = []
    a.append(">".join(["qqq"]))
    print(a)

    import IPy
    a = {}
    ip = IPy.IP("192.168.1.1/24", make_net=1)
    a["sss"] = [x for x in ip]
    print(a)

    b = ["10", "2", "3"]
    c = [*b, "5"]
    print(c)

    e = {"a": 1, "b": 2}
    d = {**e, "c": 3}
    print(d)

    f = (1, 2, 3)
    g = [*f]
    print(g)

    h = ">".join([*["ss", "ww"], *["aa", "bb"]])
    print(h)

    aa = {"q": 2, "f": 3, "p": 4}
    bb = aa.keys()
    print(*bb)

    ff = {}
    ff["s"] = []
    ff["s"] = "dddd"
    print(ff)

    import multiprocessing
    multiprocessing.Manager()

    import datetime

    print(datetime.datetime.now())

    import re
    node = "cpu0:36, cpu31:36, cpu20:1"
    print(str(int(max(re.split(':|,|cpu[0-9]+', node)))))