# author : wangcwangc
# time : 2021/11/24 3:51 PM
import getopt
import subprocess
import platform
from sys import exit
from data.server import start_server
from deptree.my_function import myFunction

from deptree.solver_global import *
from deptree.solver_local import *
from create_venv.improved_pip import ImprovedPip


def external_cmd1(cmd):  # 从 MySetup.py 获取依赖信息
    # try:
    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            encoding="utf-8")
    stdout_value, stdout_error = proc.communicate(timeout=10)
    # print(stdout_value)
    return stdout_value
    # except Exception:
    #     raise Exception


# 输出安装脚本
# 按照树形结构从底向上
# 例如 pip install requests==2.26.0，确定版本
def write_script(dependency_tree, result, no_conflict_list):
    new_file = "install-local.txt"
    output_file = open(os.getcwd() + "/" + new_file, "w+", encoding='UTF-8')
    # output_file.write("import os\n\n")

    in_list = []
    for node in dependency_tree.level_order_traversal(dependency_tree):
        if node.package not in in_list:
            in_list.insert(0, node.package)
    in_list.pop()
    for item in in_list:
        if item in result.keys() and result[item] is not None and result[item] != '*':
            output_file.write("" + item + '==' + result[item] + "\n")
        else:
            # @@@
            try:
                version = list(get_labels_id(item).keys())[-1]
                output_file.write("" + item + '==' + version + "\n")
            except Exception as e:
                print(e)

    for item in no_conflict_list:
        output_file.write("" + item + '\n')

    output_file.close()
    print("install.py has been successfully output")


# 静态分析处理call graph
# 如果call graph所有路径皆可调用，则返回True
# dependency_list_child 表示该依赖的所有父依赖节点
def is_call_graph_ok(dependency_tree_child):
    print(dependency_tree_child)
    return True


# 将求解得到的时间戳重新转化回对应版本
def reverse_label(lib, package):
    try:
        # @@@
        version_list = list(get_labels_id(lib).keys())
        for key in version_list:
            if get_labels_id(lib)[key] == package:
                return key
        if package > get_labels_id(lib)[version_list[-1]]:
            return version_list[-1]
        elif package < get_labels_id(lib)[version_list[0]]:
            return version_list[0]
    except Exception as e:
        print(e)
        pass


# 接入虚拟环境, 装解出来的完全依赖树
def virtual_make(result):
    return True


# 标准化依赖格式为：name ==(operation) version
# def normalize_req(requirements):
#     dep_list = []
#     f1 = 0
#     tem = ''
#     for item in requirements:  # 迭代每一个依赖
#         if item != '' and item.startswith("#") is False:  # 当前行不是空或者不是以#开头
#             requirement = item
#             if requirement.__contains__("#"):
#                 requirement = requirement.split("#")[0]
#             if requirement.__contains__(","):
#                 tem = requirement.split(",")
#                 requirement = tem[0]
#                 if tem[1][0].isalnum() is False:
#                     f1 = 1
#             requirement = requirement.strip(" ")
#             if " " not in requirement:
#                 requirement = list(requirement)
#                 for j in range(1, len(requirement)):
#                     if requirement[j - 1].isalnum() and requirement[j].isalnum() is False and \
#                             requirement[j] != "-" and requirement[j] != "_" and requirement[j] != ".":
#                         requirement.insert(j, " ")
#                     if requirement[j - 1].isalnum() is False and requirement[j].isdigit():
#                         requirement.insert(j, " ")
#                         break
#                     if j == len(requirement) - 2 and requirement[j].isalnum() is False:
#                         requirement.insert(j + 1, " ")
#                 requirement = ''.join(requirement)
#                 # print(requirement)
#             elif len(requirement.split(" ")) == 1:
#                 tem_req = requirement.split(" ")
#                 if tem_req[1][0].isalnum() is False:
#                     requirement = list(tem_req[1])
#                     for j in range(1, len(requirement)):
#                         if requirement[j - 1].isalnum() is False and requirement[j].isdigit():
#                             requirement.insert(j, " ")
#                             break
#                 elif tem_req[0][-1].isalnum() is False:
#                     requirement = list(tem_req[0])
#                     for j in range(1, len(requirement)):
#                         if requirement[j - 1].isalnum() and requirement[j].isalnum() is False and \
#                                 requirement[j] != "-" and requirement[j] != "_" and requirement[j] != ".":
#                             requirement.insert(j, " ")
#                             break
#
#                 # if j == len(requirement) - 2 and requirement[j].isalnum() is False:
#                 #     requirement.insert(j + 1, " ")
#                 requirement = ''.join(requirement)
#                 # print(requirement)
#             if f1 == 1:
#                 req = requirement.split(' ')[0]
#                 tem_noblank = tem[1].strip(" ")
#                 tem_q = req + tem_noblank
#                 requirements.append(tem_q)
#                 f1 = 0
#
#             requirement = requirement.strip()
#             dep_list.append(requirement)
#
#     return dep_list


# 将求解出的依赖版本输出到req.txt文件
def write_to_req_file(req_file_dep, dependency_list, sat_result, z3_var_to_max_object_dict, no_conflict_list):
    has_install = set()

    install_list = dict()

    for item in sat_result:
        lib = str(item)
        if lib in z3_var_to_max_object_dict:
            my_optimize_solver.upper(z3_var_to_max_object_dict[lib])
            # print(lib)
            # print(my_optimize_solver.upper_values(z3_var_to_max_object_dict[lib]))
            # 是否保留
            if not str(z3_var_to_max_object_dict[lib].upper()) == 'oo':
                answer = int(str(sat_result[item]))
                version = reverse_label(lib, answer)
                install_list[lib] = version
            else:
                install_list[lib] = list(get_labels_id(str(item)).keys())[-1]

    new_file = "install.txt"
    output_file = open(os.getcwd() + "/" + new_file, "w+", encoding='UTF-8')
    for item in dependency_list:

        if has_install.__contains__(item):
            continue

        if item not in install_list:
            if item in req_file_dep:
                version = list(get_labels_id(item).keys())[-1]
                output_file.write("" + item + '==' + version + '\n')
                continue
            else:
                continue

        has_install.add(item)

        if install_list[item] == '*':
            continue
        if item in install_list.keys() and install_list[item] is not None:
            output_file.write("" + item + '==' + install_list[item] + '\n')
        else:
            # @@@
            try:
                version = list(get_labels_id(item).keys())[-1]
                # output_file.write("pip install " + item + '==' + version + '\n')
                output_file.write("" + item + '==' + version + '\n')
            except Exception as e:
                print("add install script error : " + str(e) + " : " + item)
                output_file.write("pip install " + item + '\n')

    for item in no_conflict_list:
        output_file.write("" + item + '\n')

    output_file.close()
    print("install file has been successfully output")


# 添加本地依赖的版本约束
def add_local_dependencies():
    p = subprocess.Popen("pip freeze", shell=True, stdout=subprocess.PIPE)
    lines = p.stdout.readlines()
    deck_list = list()
    for line in lines:
        deck_list.append(line.decode().strip())
    deck_list.pop()
    deck_dict = {}
    for i in deck_list:
        i = i.split("==")
        deck_dict[i[0]] = i[1]

    for key in deck_dict:
        if key in lib_dict:
            x = Int(key)
            version = deck_dict[key]
            try:
                cmp_label = get_labels_id(key)[version]
            except Exception as e:
                print(e)
                continue
            my_optimize_solver.add(x == cmp_label)


# 判断两个集合中是否有重复元素
def is_dup_in_set(source, target):
    for s in source:
        if s in target:
            return True
    return False


# 过滤掉没有冲突子依赖的依赖
def filter_requirement_no_conflict(requirement_list):
    result = list()
    no_conflict = set()
    for requirement in requirement_list:
        for requirement_dup in requirement_list:
            if requirement.__eq__(requirement_dup):
                continue
            else:
                package_name = requirement.split(" ")[0]
                package_id = list(get_labels_id(package_name).values())[0]
                package_dep_set = get_package_all_dependency_set(package_id)

                package_name_dup = requirement_dup.split(" ")[0]
                package_id_dup = list(get_labels_id(package_name_dup).values())[0]
                package_dep_set_dup = get_package_all_dependency_set(package_id_dup)

                if is_dup_in_set(package_dep_set, package_dep_set_dup):
                    if requirement not in result:
                        result.append(requirement)
                else:
                    no_conflict.add(requirement)

    for r in result:
        if r in no_conflict:
            no_conflict.remove(r)

    return result, no_conflict


def get_req_file_package_name(req_list):
    result = []
    for req in req_list:
        result.append(str(req).split(' ')[0])
    return result


# 将直接依赖装入求解器并构建第一层依赖树
# 通过递归调用constraint_solving函数填充求解器和依赖树，最后输出求解结果并调用输出函数
# requirements: 从setup得到的直接依赖
# package_info: 主项目名，用于建立依赖树
def handle_dependency(requirements, package_info):
    # 标准化依赖信息
    requirement_normalize_list = normalize_req(requirements)

    # requirement_list_after_filter, no_conflict = filter_requirement_no_conflict(requirement_normalize_list)
    requirement_list_after_filter = requirement_normalize_list
    no_conflict = []
    if GLOBAL_SOLVING and len(requirement_list_after_filter) > 0:
        # 重构求解方法
        constraint_solving_refactor(requirement_list_after_filter, MyNode(package_info))
        z3_var_to_max_object_dict = dict()
        dependency_tree = global_dep_tree

        z3_vars = global_z3_vars_set
        for val in z3_vars:
            z3_var_to_max_object_dict[val] = my_optimize_solver.maximize(Int(val))

        # print(my_optimize_solver)
        # my_optimize_solver.check()
        if my_optimize_solver.check() == sat:  # 约束可解
            # print(my_optimize_solver)
            # print(my_optimize_solver.model())
            if LOCAL_REPOSITORY:
                improved_pip = ImprovedPip()
                all_packages = improved_pip.repository_manager.get_all_packages()
                package_name_set = all_packages.keys()
                for z3_var in z3_vars:
                    if z3_var in package_name_set:
                        version_list = all_packages.get(z3_var)  # 获取本地version列表
                        version_id_dict = get_labels_id(z3_var)  # 获取version id列表

                        for version in version_list:
                            my_optimize_solver.push()
                            my_optimize_solver.add(Or(Int(z3_var) == version_id_dict[version]))
                            if my_optimize_solver.check() == sat:
                                break
                            else:
                                my_optimize_solver.pop()
            # else:
            my_optimize_solver.check()
            write_to_req_file(get_req_file_package_name(requirement_list_after_filter),
                              dependency_tree.level_order_traversal(),
                              my_optimize_solver.model(),
                              z3_var_to_max_object_dict, no_conflict)
        else:
            print("These requirements can not be satisfied all. Maybe you should check again.")
    else:
        install_list = {}
        s = Optimize()

        dependency_tree = Node(package_info, package_info, 0)
        dep_count()
        con_add(requirement_normalize_list, s)

        create_dependency_tree(requirement_list_after_filter, dependency_tree, package_info)

        for item in requirement_normalize_list:
            each_name = item.split(' ')[0]
            lib_dict.append(each_name)
        dep_flag = len(requirement_normalize_list)

        # refactor
        constraint_solving(requirement_normalize_list, s, dependency_tree, dep_flag)
        if final_flag == 0:
            result = s.model()

            if s.check() == sat:
                result = s.model()
                for item in result:
                    lib = str(item)
                    answer = int(str(result[item]))
                    version = reverse_label(lib, answer)
                    install_list[lib] = version
                write_script(dependency_tree, install_list, no_conflict)

            else:
                # @@@
                print("Local environment can not satisfy these requirements")
                virtual_make(result)
        else:
            print("These requirements can not be satisfied all. Maybe you should check again.")


# 通过setup.py解析依赖树进行分析
def analysis_from_setup():
    file_path = os.path.abspath(".")
    file_names = os.listdir(file_path)  # 获取当前路径下的文件名，返回List
    has_process_setup = False
    for fileName in file_names:
        if fileName == "setup.py":
            has_process_setup = True
            setup_file = open(os.path.realpath(fileName), "r+", encoding='UTF-8')
            content = setup_file.read()
            pos = content.find("\nsetup(")
            if pos != -1:
                content = "# -*- coding: utf-8 -*-\n" + content[:pos] + myFunction + content[pos:]
                new_file = "MySetup.py"
                setup_file = open(os.getcwd() + "/" + new_file, "w+", encoding='UTF-8')
                setup_file.write(content)
            else:
                print("Can't find setup.py")
            setup_file.close()
            results = external_cmd1("python MySetup.py")
            results = results.strip('\n')
            if results:
                requirements = results.split("\n")
                name = requirements[0]
                name = name.replace('.', '-').replace('_', "-")
                if name is not None:
                    requirements = requirements[2:len(requirements)]
                    handle_dependency(requirements, name)
            break
    if not has_process_setup:
        print("Can not find setup.py, maybe it's a local package")


# 通过requirement.txt解析依赖树进行分析
# file : requirement.txt 路径
def analysis_from_req(file):
    file_path = os.path.realpath(file)
    system_platform = platform.system()
    package_info = "host"
    if system_platform == "Windows":
        package_info = file_path.split('\\')[-2]
    elif system_platform == "Linux":
        package_info = file_path.split('/')[-2]

    try:
        req = open(file_path, "r+", encoding='UTF-8')
        content = req.read()
    except Exception as exception:
        print(exception)
        return

    if content:
        requirements = content.strip('\n')
        requirements = requirements.split('\n')
        handle_dependency(requirements, package_info)

    print("req.txt : " + file)


# 检测服务端是否启动
# todo 没有启动的话，开启一个子线程去启动
def server_is_start():
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        conn.connect((LOCAL_HOST, TCP_PORT))
        conn.close()
        print('%s:%s server is started' % (LOCAL_HOST, TCP_PORT))
        return True
    except ConnectionRefusedError:
        return False


def read_file(file_path):
    file = open(file_path, "r")
    data = file.read().splitlines()
    return data


# 创建本地仓库和虚拟环境安装目标packages
# install_packages_file : 求解结果的输出文件，默认当前路径下的相对路径install.txt
def create_smart_venv_to_install_packages(install_packages_file):
    print(install_packages_file)
    install_packages = read_file(install_packages_file)
    package_info_list = []
    for package in install_packages:
        if package:
            package_name = package.split('==')[0]
            package_version = package.split('==')[1]
            package_info_list.append((package_name, package_version))
    try:
        improved_pip = ImprovedPip()
        improved_pip.install_sequential_packages(package_info_list, False)
    except Exception as Exc:
        print("ERROR : " + str(Exc))


# 是否使用全局求解器，默认false
GLOBAL_SOLVING = False

# 是否存在本地仓库
LOCAL_REPOSITORY = False


def main():
    start = time.time()
    opts, args = getopt.getopt(sys.argv[1:], "hr:sgv:e")
    req_file = "requirements.txt"
    # req_file = ""
    # os.chdir("../../test/CoinMarketCap-Historical-Prices")
    install_req_file = "install.txt"
    need_create_venv = False

    for opt, arg in opts:
        if opt == "-h":
            print("-r 指定requirement.txt路径，不指定则默认解析setup.py")
            print("-s 开启依赖信息获取服务")
            print("-g 开启全局求解器")
            print("-v 指定求解后的依赖文件，使用智能虚拟环境安装")
            print("-e 选择此参数，说明环境中存在本地仓库")
            exit(0)
        if opt == "-r":
            req_file = arg
        if opt == "-s":
            print('Waiting for the server to start')
            start_server()
            exit(0)
        if opt == "-g":
            print("use global constraint solving")
            global GLOBAL_SOLVING
            GLOBAL_SOLVING = True
        if opt == "-v":
            print("use smart-pip venv to install packages")
            install_req_file = arg
            need_create_venv = True
        if opt == "-e":
            global LOCAL_REPOSITORY
            LOCAL_REPOSITORY = True

    if not need_create_venv:
        if server_is_start() is False:
            print('server disabled. please exec shell "PySI -s" first.')
            return

        if req_file == "":
            # 无参数运行setup.txt
            analysis_from_setup()
        else:
            # 有参数运行req.txt
            if os.path.exists(req_file) is False:
                print("文件不存在")
                exit(2)
            analysis_from_req(req_file)

        end = time.time()
        print("solve time:" + str(end - start))

    else:
        if os.path.exists(install_req_file) is False:
            print("文件不存在")
            exit(2)
        try:
            create_smart_venv_to_install_packages(install_req_file)
        except Exception as exc:
            print("ERROR : " + str(exc))

        end = time.time()
        print("install time:" + str(end - start))


# 命令行入口
# 有参数-r requirement.txt 通过文件解析依赖
# 无参数则默认通过setup.py解析依赖
if __name__ == '__main__':
    main()
    GLOBAL_SOLVING = True
    LOCAL_REPOSITORY = True
    main()
    # print(add_or(['(a)', '(b)', '(c)']))
