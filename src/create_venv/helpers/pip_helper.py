# -*- coding: utf-8 -*-
# @Time    : 15:52 2022/3/12 
# @Author  : Haohao Song
# @Email   : songhaohao2021@stu.xmu.edu.cn
# @File    : pip_cmd.py
import subprocess
import sys


def pip_install(package_info):
    name_with_version = '{}=={}'.format(package_info[0], package_info[1])

    popen = subprocess.Popen(
            [sys.executable, '-m', 'pip', 'install', name_with_version, '--no-deps'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    out, err = popen.communicate()

    print(out.decode())
    print(err.decode())


def pip_list():
    popen = subprocess.Popen(
            [sys.executable, '-m', 'pip', 'list', '--format', 'json'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    out, err = popen.communicate()
    return out
