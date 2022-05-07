# -*- coding: utf-8 -*-
# @Time    : 17:33 2022/3/12 
# @Author  : Haohao Song
# @Email   : songhaohao2021@stu.xmu.edu.cn
# @File    : utils.py
import json
import os
import sys

from create_venv.helpers import pip_helper


def _get_site_package_path():
    for path in sys.path:
        if path.endswith('site-packages'):
            return path


def site_packages_snapshot(site_package_path):
    return os.listdir(site_package_path)


def bin_snapshort():
    bin_path = os.path.split(sys.executable)[0]
    return os.listdir(bin_path)


def get_installed_packages():
    installed_packages_str = pip_helper.pip_list()
    installed_package_json = json.loads(installed_packages_str)

    installed_package_2_version = dict()
    for install_package in installed_package_json:
        installed_package_2_version.update(
            {install_package['name'].lower(): install_package['version']})

    return installed_package_2_version


def scan_file_types(dir_paths, site_package_path):
    exclude_file_types = list()

    for dir_name in dir_paths:
        if '-info' in dir_name:
            continue

        abs_path = os.path.join(site_package_path, dir_name)

        for pwd, sub_dirs, sub_files in os.walk(abs_path):

            for file_name in sub_files:
                file_name_suffix = os.path.split(file_name)[-1]

                if file_name_suffix not in ['.py', '.pyc', ]:
                    exclude_file_types.append(file_name_suffix)

    return exclude_file_types


def symbol_link_repository_with_env(name, site_package_path,
                                    package_paths_in_repository):
    for package_path in package_paths_in_repository:
        # src_path = os.path.join(self.real_lib_manager.packages_dir_path, src_name)  # todo::
        src_path = package_path
        des_path = os.path.join(site_package_path,
                                os.path.split(package_path)[-1])

        try:
            os.symlink(src_path, des_path)
            print('{} symbolic link has been built.'.format(des_path))
        except FileExistsError:
            print('Fail to create symlink for {}.'.format(name))
