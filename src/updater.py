#!/usr/bin/env python

import c3_cloud
import os
import mapper
import signal
from pathlib import Path


if __name__ == '__main__':
    if Path("./.pid").is_file():
        f = open("./.pid", "r")
        pid = int(f.readline())
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            print("info: no running instance found.")
        else:
            print("info: Quitting running c3_cloud semantic mapper instance (pid {})...".format(pid))
    else:
        print("info: no .pid file found.")

    print("creating database...")
    mapper.init(recreate_database=True)
    print("database rebuilt.")
    print("launching new semantic mapper instance...")
    c3_cloud.run()
