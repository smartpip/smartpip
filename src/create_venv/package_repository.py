# -*- coding: utf-8 -*-
# @Time    : 16:28 2022/3/12 
# @Author  : Haohao Song
# @Email   : songhaohao2021@stu.xmu.edu.cn
# @File    : package_repository.py
import os
import pathlib
import platform
import shutil

from create_venv.helpers.compatibility_helper.wheel import wheel


class PackagesBill(object):
    def __init__(self, bill_path):
        self.bill_path = bill_path
        self._check_bill_path()

        self.package_infos = None

    def _check_bill_path(self):
        if not os.path.exists(self.bill_path):
            pathlib.Path(self.bill_path).touch()

    def add_package(self, package_info, package_dir_path, tag_info):
        with open(self.bill_path, 'a', encoding='utf8') as fw:
            # name, version, tags, dir_name\n
            fw.write('{}::::{}::::{}::::{}\n'.format(package_info[0],
                                                     package_info[1], tag_info,
                                                     package_dir_path))

    def del_package(self, package_info):
        target_name = package_info[0]
        target_version = package_info[1]

        if self.package_infos is None:
            self.get_packages()

        # modify
        matched_idx = -1
        for idx, record in enumerate(self.package_infos):
            candidate_name, candidate_version, wheel_tags, candidate_dir_path = record

            matched_name = target_name == candidate_name
            matched_version = target_version == candidate_version

            if matched_name and matched_version:
                matched_idx = idx

        if matched_idx != -1:
            # os.rmdir(self.package_infos[matched_idx][-1])
            # todo Operation not permitted
            file_path = pathlib.Path(self.package_infos[matched_idx][-1])
            try:
                file_path.unlink()
            except OSError as e:
                print("Error: %s : %s" % (file_path, e.strerror))

            del self.package_infos[matched_idx]

            # write back
            with open(self.bill_path, 'w', encoding='utf8') as fw:
                for candidate_name, candidate_version, wheel_tags, candidate_dir_path in self.package_infos:
                    fw.write('{}::::{}::::{}::::{}\n'.format(candidate_name,
                                                             candidate_version,
                                                             wheel_tags,
                                                             candidate_dir_path))

        else:
            print('NOT FOUND PAKCAGE!')

    def get_packages(self):
        package_infos = list()
        with open(self.bill_path, 'r', encoding='utf8') as fr:
            for line in fr:
                name, version, tags, path = line.strip().split('::::')
                package_infos.append((name, version, tags, path))
        self.package_infos = package_infos
        return package_infos

    def search_package(self, package_info):
        target_name = package_info[0]
        target_version = package_info[1]

        if self.package_infos is None:
            self.get_packages()

        matched_dirs = list()
        for record in self.package_infos:
            candidate_name, candidate_version, wheel_tags, candidate_dir_path = record

            matched_name = target_name == candidate_name
            matched_version = target_version == candidate_version

            # Check whether platform is compatible.
            artificial_whl_filename = 'improved_pip-0.0.1-{}.whl'.format(
                    wheel_tags)

            is_compatible = True
            if wheel_tags:
                is_compatible = wheel.is_compatible(artificial_whl_filename,
                                                    None)

            if False not in [matched_name, matched_version, is_compatible]:
                matched_dirs.append(candidate_dir_path)

        return matched_dirs


class RepositoryManager(object):
    def __init__(self):
        self.repository_dir = self._get_repository_dir()
        self._check_repository_dir()

        bill_path = os.path.join(self.repository_dir, 'packages.bill')
        self.packages_bill = PackagesBill(bill_path=bill_path)

    def _get_repository_dir(self):
        if platform.system() == 'Windows':
            return os.path.join(os.path.expanduser('~'),
                                'AppData/Local/ipip/site-packages/')
        # elif platform.system() == 'Linux':
        else:
            return os.path.join(os.path.expanduser('~'),
                                '.local/share/site-packages/')

    def _check_repository_dir(self):
        if not os.path.exists(self.repository_dir):
            os.makedirs(self.repository_dir)

    def clean_respository(self):
        assert os.path.exists(self.repository_dir)
        shutil.rmtree(self.repository_dir)

    def rename_dir(self, old_name, new_name):
        raise NotImplementedError

    def fix_name_conflict(self):
        raise NotImplementedError

    def get_all_packages(self):
        all_packages_infos = self.packages_bill.get_packages()
        all_packages = dict()
        for info in all_packages_infos:
            if all_packages.__contains__(info[0]):
                versions = all_packages.get(info[0])
                versions.add(info[1])
            else:
                versions = set()
                versions.add(info[1])
                all_packages[info[0]] = versions

        return all_packages


if __name__ == '__main__':
    repository = RepositoryManager()
    # pbill.del_package(('requests', '2.22.0'))
    print(repository.get_all_packages())
