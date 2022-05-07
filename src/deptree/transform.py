# author : wangcwangc
# time : 2021/11/27 5:14 PM
import json
import os
import socket
import time

from data.server import TCP_PORT, LOCAL_HOST


def read_json_file(file):
    f = open(file, 'r')
    data = json.load(f)
    return data


folder = os.path.dirname(os.path.abspath(__file__))


# id : [id1 : range, id2 : range]
# packages = read_json_file(folder + "/../data/dependency.json")
# package : version : id
# labels = read_json_file(folder + "/../data/label.json")


# id - package + version


# 根据icon返回在需求范围内的版本依赖项
# vindatabase: 比较的版本
# vfromreq: 需要的版本
def beyond_version(vindatabase, vfromreq):
    cmplist1 = vindatabase.split('.')
    cmplist2 = vfromreq.split('.')
    len1 = len(cmplist1)
    len2 = len(cmplist2)
    # if icon == 1:
    #     if cmplist1[0] >= cmplist2[0]:
    #         if len1 == 1 or len2 == 1:
    #             return True
    #         elif cmplist2[1].isalnum() is False:
    #             return True
    #         elif cmplist1[1] >= cmplist2[1]:
    #             if len2 == 2:
    #                 if len(cmplist1) == 2:
    #                     return True
    #                 elif cmplist1[2] == '0':
    #                     return True
    #             elif len1 == 2:
    #                 if cmplist2[2] == '0':
    #                     return True
    #             elif cmplist1[2] >= cmplist2[2]:
    #                 return True
    # elif icon == 2:
    #     if cmplist1[0] <= cmplist2[0]:
    #         if len1 == 1 or len2 == 1:
    #             return True
    #         elif cmplist2[1].isalnum() is False:
    #             return True
    #         elif cmplist1[1] <= cmplist2[1]:
    #             if len2 == 2:
    #                 if len(cmplist1) == 2:
    #                     return True
    #                 elif cmplist1[2] == '0':
    #                     return True
    #             elif len1 == 2:
    #                 if cmplist2[2] == '0':
    #                     return True
    #             elif cmplist1[2] <= cmplist2[2]:
    #                 return True
    # elif icon == 0:
    if cmplist1[0] == cmplist2[0]:
        if len1 == 1 or len2 == 1:
            return True
        elif cmplist2[1].isalnum() is False:
            return True
        elif cmplist1[1] == cmplist2[1]:
            if len2 == 2:
                if len(cmplist1) == 2:
                    return True
                elif cmplist1[2] == '0':
                    return True
            elif len1 == 2:
                if cmplist2[2] == '0':
                    return True
            elif cmplist1[2] == cmplist2[2]:
                return True


def label_change(icon, package):
    if type(package) == str:
        if icon == 1:
            package = str(int(package) + 1)
        elif icon == 2:
            package = str(int(package) - 1)
    elif type(package) == int:
        if icon == 1:
            package += 1
        elif icon == 2:
            package -= 1

    return package


labels_id_cache = dict()
labels_name_cache = dict()
dependencies = dict()
package_dep_set_cache = dict()


# 获取package的所有依赖摘要，包含本身
def get_package_all_dependency_set(package_id):
    package_id = str(package_id)
    if package_dep_set_cache.__contains__(package_id):
        package_dep_set = package_dep_set_cache[package_id]
        if 'error' in package_dep_set:
            return {package_id}

        package_dep_set = set(package_dep_set)
        package_dep_set.add(package_id)
        return package_dep_set

    else:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((LOCAL_HOST, TCP_PORT))

        send_data = "ds@@" + package_id
        client.send(send_data.encode())
        receive_data = client.recv(51200).decode()
        package_dep_set = json.loads(receive_data)
        if 'error' in package_dep_set:
            return {package_id}
        package_dep_set_cache[package_id] = package_dep_set
        client.close()

        package_dep_set = set(package_dep_set)
        package_dep_set.add(package_id)  # 添加package本身的id
        return package_dep_set


# get labels id dict by package name
def get_labels_id(package_name):
    if labels_id_cache.__contains__(package_name):
        package_data = labels_id_cache[package_name]
        if 'error' in package_data:
            return {}
        return package_data
    else:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((LOCAL_HOST, TCP_PORT))
        send_data = "i@@" + package_name
        client.send(send_data.encode())
        receive_data = client.recv(51200).decode()
        package_data = json.loads(receive_data)
        if 'error' in package_data:
            return {}
        labels_id_cache[package_name] = package_data
        client.close()
        return package_data


# get label name by package id
def get_labels_name(package_id):
    if labels_name_cache.__contains__(package_id):
        return labels_name_cache[package_id]
    else:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((LOCAL_HOST, TCP_PORT))
        send_data = "n@@" + package_id
        client.send(send_data.encode())
        receive_data = client.recv(51200).decode()
        labels_name_cache[package_id] = receive_data
        client.close()
        return receive_data


# get dependencies dict by package id
def get_dep(package_id):
    if dependencies.__contains__(package_id):
        dependency_data = dependencies[package_id]
        if 'error' in dependency_data:
            return {}
        return dependency_data
    else:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((LOCAL_HOST, TCP_PORT))
        send_data = "d@@" + str(package_id)
        client.send(send_data.encode())

        receive_data = client.recv(51200).decode()
        dependency_data = json.loads(receive_data)
        dependencies[package_id] = dependency_data
        if 'error' in dependency_data:
            return {}
        client.close()
        return dependency_data


# pname: 库名
# major_v: 该库该项依赖的版本
# flag: 是否需要按版本比较
# icon: 该项依赖的符号，0为等于，1为大于类，2为小于类
def transform(pname=None, major_v=None, flag=0, icon=0):
    i = 0
    k = 0
    requirement = []
    requirements = []
    try:
        package_list = list(get_labels_id(pname).keys())
        if not package_list:
            return []
        if flag == 0:
            major_v = package_list[-1]
            return major_v

        else:
            for i in range(1, len(package_list)):
                if package_list[i] == major_v:
                    break

            if icon == 1:
                for j in range(i, len(package_list)):
                    package = get_labels_id(pname)[package_list[j]]
                    deps = get_dep(package)
                    for dep in deps:
                        dependency = get_labels_name(dep)
                        version = deps[dep]
                        if version == '*':
                            version = ''
                        # print('\t' + dependency + version)
                        dv = str(dependency + version)
                        requirement.append(dv)
                    requirements.append(requirement)
                    requirement = []
            elif icon == 2:
                for j in range(1, i):
                    package = get_labels_id(pname)[package_list[j]]
                    # print(labels_name[str(package)])
                    deps = get_dep(package)
                    for dep in deps:
                        dependency = get_labels_name(dep)
                        version = deps[dep]
                        if version == '*':
                            version = ''
                        # print('\t' + dependency + version)
                        dv = str(dependency + version)
                        requirement.append(dv)
                    requirements.append(requirement)
                    # print(requirement)
                    requirement = []
            elif icon == 3:
                for j in range(i + 1, len(package_list)):
                    package = get_labels_id(pname)[package_list[j]]
                    # print(labels_name[str(package)])
                    deps = get_dep(package)
                    for dep in deps:
                        dependency = get_labels_name(dep)
                        version = deps[dep]
                        if version == '*':
                            version = ''
                        # print('\t' + dependency + version)
                        dv = str(dependency + version)
                        requirement.append(dv)
                    requirements.append(requirement)
                    # print(requirement)
                    requirement = []
            elif icon == 4:
                for j in range(1, i - 1):
                    package = get_labels_id(pname)[package_list[j]]
                    # print(labels_name[str(package)])
                    deps = get_dep(package)
                    for dep in deps:
                        dependency = get_labels_name(dep)
                        version = deps[dep]
                        if version == '*':
                            version = ''
                        # print('\t' + dependency + version)
                        dv = str(dependency + version)
                        requirement.append(dv)
                    requirements.append(requirement)
                    # print(requirement)
                    requirement = []
            elif icon == 5:
                mv = major_v.split('.')
                print(mv)
                mv_0 = mv[0]
                mv_1 = str(int(mv_0) + 1)

                for k in range(1, len(package_list)):
                    pv = package_list[k].split('.')
                    if pv[0] == mv_1:
                        break
                for j in range(i, k):
                    package = get_labels_id(pname)[package_list[j]]
                    # print(labels_name[str(package)])
                    deps = get_dep(package)
                    for dep in deps:
                        dependency = get_labels_name(dep)
                        version = deps[dep]
                        if version == '*':
                            version = ''
                        # print('\t' + dependency + version)
                        dv = str(dependency + version)
                        requirement.append(dv)
                    requirements.append(requirement)
                    # print(requirement)
                    requirement = []
            elif icon == 0:
                package = get_labels_id(pname)[major_v]
                deps = get_dep(package)
                for dep in deps:
                    dependency = get_labels_name(dep)
                    version = deps[dep]
                    if version == '*':
                        version = ''
                    # print('\t' + dependency + version)
                    dv = str(dependency + version)
                    requirement.append(dv)
                requirements.append(requirement)
    except KeyError:
        pass

    real_req = []
    # print(requirements)
    for i in requirements:
        if i not in real_req:
            real_req.append(i)
    return real_req


if __name__ == '__main__':
    #     requirements = transform("packaging", "19.0", 1, 0)
    #     print(requirements)
    #     for item in requirements[0]:
    #         req = item.split('==')
    #         if len(req) == 1:
    #             continue
    #         r = transform(req[0], req[1], 1, 0)
    #         print(req[0])
    #         print(r)
    print(get_labels_id('djangorestframework'))
    print(get_package_all_dependency_set('2104853'))
    print(get_labels_name('2104853'))
    print(get_dep('2104853'))
    # for item in requirements:
    #     print(item)
    # start = time.time()
    # get_dep('2850260')
    # print(time.time() - start)
    # start = time.time()
    # for i in range(10000):
    #     get_dep('2850260')
    # print(time.time() - start)
