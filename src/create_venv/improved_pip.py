# -*- coding: utf-8 -*-
# @Time    : 14:53 2022/1/10 
# @Author  : Haohao Song
# @Email   : songhaohao2021@stu.xmu.edu.cn
# @File    : utils.py
import os
import shutil
import sys

from create_venv import utils
from create_venv.helpers import pip_helper
from create_venv.package_repository import RepositoryManager

'''
Features:
- compatibility: tag
- skim packages which generates executable in /bin/ and use C extensions.
===========================================

Usages:
- Create a instance of ImprovedPip().
- Call API, e.g., install_sequential_packaegs(), uninstall()
===========================================

ipip = ImprovedPip()
ipip.install_sequential_packages(package_infos, True)

for package_info in package_infos:
    ipip.uninstall(package_info)
'''


class ImprovedPip(object):
    def __init__(self):
        self.site_package_path = utils._get_site_package_path()
        self.repository_manager = RepositoryManager()

    def move_to_global_repository(self, package_info, new_installed_dirs):
        package_name = package_info[0]

        info_dir_name = None
        for install_dir in new_installed_dirs:
            if '-info' in install_dir:
                info_dir_name = install_dir
                break

        target_paths = list()

        if info_dir_name is None:  # if does not find WHEEL, place these folder into root path
            self.move_to_root_repository(new_installed_dirs, package_info,
                                         target_paths)
        else:  # if find WHEEL, palce name/tag/ path
            self.move_to_tag_repository(info_dir_name, new_installed_dirs,
                                        package_info, package_name,
                                        target_paths)
        return target_paths

    def move_to_root_repository(self, new_installed_dirs, package_info,
                                target_paths):
        for install_dir in new_installed_dirs:
            private_repository_path = os.path.join(self.site_package_path,
                                                   install_dir)

            public_repository_path = self.repository_manager.repository_dir
            public_repository_dir_path = os.path.join(public_repository_path,
                                                      install_dir)

            if not os.path.exists(public_repository_dir_path):
                shutil.move(private_repository_path, public_repository_path)

            if os.path.exists(private_repository_path):
                shutil.rmtree(private_repository_path)

            target_paths.append(
                    os.path.join(public_repository_path, install_dir))

            self.repository_manager.packages_bill.add_package(package_info,
                                                              public_repository_dir_path,
                                                              'py3-none-any')  # default tags

    def move_to_tag_repository(self, info_dir_name, new_installed_dirs,
                               package_info, package_name, target_paths):
        tag_info = ''
        wheel_file_path = os.path.join(self.site_package_path, info_dir_name,
                                       'WHEEL')
        if os.path.exists(wheel_file_path):
            with open(wheel_file_path, 'r', encoding='utf8') as fr:
                for line in fr:
                    if 'Tag' in line:
                        tag_info = line.lower().replace('tag:', '').strip()
        public_repository_path = os.path.join(
                self.repository_manager.repository_dir, package_name, tag_info)
        if not os.path.exists(public_repository_path):
            os.makedirs(public_repository_path)
        for install_dir in new_installed_dirs:
            private_repository_path = os.path.join(self.site_package_path,
                                                   install_dir)

            public_repository_dir_path = os.path.join(public_repository_path,
                                                      install_dir)
            if not os.path.exists(public_repository_dir_path):
                shutil.move(private_repository_path, public_repository_path)

            if os.path.exists(private_repository_path):
                shutil.rmtree(private_repository_path)

            target_paths.append(
                    os.path.join(public_repository_path, install_dir))

            self.repository_manager.packages_bill.add_package(package_info,
                                                              public_repository_dir_path,
                                                              tag_info)

    def install_sequential_packages(self, package_infos,
                                    is_no_python_extension_silent):
        '''
        Install packages and organize their folder.

        :param package_infos: list of tuple. e.g, [('syncrfolder','0.1.3'),...]
        :param is_no_python_extension_silent: bool. whether move compiled package or not.
        :return:
        '''
        package_version_dct = utils.get_installed_packages()

        for package_info in package_infos:
            name = package_info[0].strip()
            version = package_info[1].strip()

            # skim installed wheel
            matched_name = name.lower() in package_version_dct
            matched_version = version == package_version_dct.get(name,
                                                                 'N').strip()

            if matched_name and matched_version:
                print('{} {} has been installed.'.format(name, version))
                continue

            # if name match and version not match, uninstall from venv
            if matched_name and not matched_version:
                print(
                        '{} has been installed but not {}.'.format(name,
                                                                   version))
                self.uninstall(
                        (name, package_version_dct.get(name, 'N').strip()))

            # reuse public repository
            package_paths_in_global_repository = self.repository_manager.packages_bill.search_package(
                    package_info)

            # install from pip
            if len(package_paths_in_global_repository) == 0:
                before_package_snapshot = set(
                        utils.site_packages_snapshot(self.site_package_path))
                before_bin_snapshort = set(utils.bin_snapshort())

                print('Installing from pip...')
                try:
                    pip_helper.pip_install(package_info)
                except Exception as exc:
                    print("ERROR : " + str(exc))
                    continue

                after_package_snapshot = set(
                        utils.site_packages_snapshot(self.site_package_path))
                new_installed_dir = after_package_snapshot - before_package_snapshot

                # 1. skim install binary package
                # after_bin_snapshot = set(utils.bin_snapshort())
                # installed_bin = after_bin_snapshot - before_bin_snapshort
                # if len(installed_bin) > 0:
                #     continue

                # 2. skim package which use C Extension.
                # if not is_no_python_extension_silent:
                #     exclude_file_types = utils.scan_file_types(
                #         new_installed_dir, self.site_package_path)
                #     if len(exclude_file_types) > 0:
                #         continue

                # move to global repository
                try:
                    package_paths_in_global_repository = self.move_to_global_repository(
                            package_info, new_installed_dir)
                except Exception as Exc:
                    print("move_to_global_repository error : " + str(Exc))
                    continue
            else:
                print('Reuse packages from global repository.')
            try:
                utils.symbol_link_repository_with_env(name,
                                                      self.site_package_path,
                                                      package_paths_in_global_repository)
            except Exception as Exc:
                print("ERROR : " + str(Exc))

    def uninstall(self, package_info):
        package_paths_in_real_lib = self.repository_manager.packages_bill.search_package(
                package_info)
        package_names_in_real_lib = [os.path.split(dir_path)[-1] for dir_path
                                     in package_paths_in_real_lib]

        if len(package_names_in_real_lib) == 0:
            print('{} {} has not intalled from improved_pip yet.'.format(
                    package_info[0], package_info[1]))
            sys.exit(0)

        print('Removing {} {} symbol ...'.format(package_info[0],
                                                 package_info[1]))
        for symbol_name in package_names_in_real_lib:
            symbol_link_path = os.path.join(self.site_package_path,
                                            symbol_name)

            # print('path',symbol_link_path,os.path.exists(symbol_link_path),os.path.islink(symbol_link_path))

            # if os.path.exists(symbol_link_path) and os.path.islink(symbol_link_path):
            if os.path.islink(symbol_link_path):
                os.unlink(symbol_link_path)
                print('{} has been removed.'.format(symbol_link_path))

    def permanently_clean(self):
        self.repository_manager.clean_respository()


if __name__ == '__main__':
    package_infos = [
        ('requests', '2.22.0'),
    ]
    # ('syncfolder', '0.1.3')
    # ('m3u8', '0.9.0'),
    # ('iso8601', '0.1.16'),
    # ('pycryptodome', '3.11.0'),
    # ('m3u8_to_mp4', '0.1.2'),

    ipip = ImprovedPip()
    # ipip.uninstall(package_infos[0])
    ipip.install_sequential_packages(package_infos, True)
    # ipip.uninstall(package_infos[0])
    # for package_info in package_infos:
    #     ipip.uninstall(package_info)
