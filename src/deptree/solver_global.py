# author : wangcwangc
# time : 2022/1/16 11:14 AM
import multiprocessing
from multiprocessing.pool import Pool

from z3 import *

from deptree.transform import *

# 优化后的求解器，解范围内最大值
my_optimize_solver = Optimize()


# 标准化依赖格式为：name ==(operation) version
def normalize_req(requirements):
    dep_list = []
    f1 = 0
    tem = ''
    for item in requirements:  # 迭代每一行
        if item != '' and item.startswith("#") is False:  # 当前行不是空或者不是以#开头
            requirement = item
            if requirement.__contains__("#"):
                requirement = requirement.split("#")[0]  # 过滤掉注释
            if requirement.__contains__(","):
                tem = requirement.split(",")
                requirement = tem[0]
                if tem[1][0].isalnum() is False:
                    f1 = 1
            requirement = requirement.strip(" ")
            if " " not in requirement:
                requirement = list(requirement)
                for j in range(1, len(requirement)):
                    if requirement[j - 1].isalnum() and requirement[j].isalnum() is False and \
                            requirement[j] != "-" and requirement[j] != "_" and requirement[j] != ".":
                        requirement.insert(j, " ")
                    if requirement[j - 1].isalnum() is False and requirement[j].isdigit():
                        requirement.insert(j, " ")
                        break
                    if j == len(requirement) - 2 and requirement[j].isalnum() is False:
                        requirement.insert(j + 1, " ")
                requirement = ''.join(requirement)
            if f1 == 1:
                req = requirement.split(' ')[0]
                tem_q = req + tem[1]  # 组合成 req opt version 的形式
                requirements.append(tem_q)
                f1 = 0

            requirement = requirement.strip()
            dep_list.append(requirement)

    result = dict()
    for dep_per in dep_list:
        if dep_per.__contains__(' ') is False:
            temp = list()
            temp.append('*')
            result[dep_per] = temp
        else:
            req = dep_per.split(' ')[0]
            if result.__contains__(req):
                temp = result.get(req)
                temp.append(dep_per.replace(req + ' ', ''))
            else:
                temp = list()
                temp.append(dep_per.replace(req + ' ', ''))
                result[req] = temp

    return result


# 标准化依赖格式为：name ==(operation) version
def normalize_req_refactor(requirements):
    result = dict()
    dep_list = []

    for req in requirements:
        if req == '' or req.startswith("#") is True:  # 过滤空行和注释
            continue

        print(req)
        if req.__contains__(','):
            first_req = req.split(',')[0]

            print(1)
        else:
            print(2)

    return result


# def search_opt():


# 获取输入节点的所有依赖信息，并遍历解析并添加到求解器中
# package_parent_id 被解析包的id
# all_parent_node_set 所有的父节点set集合
# dep_tree_set 依赖树每一层的节点set集合
# dep_tree 依赖树
# depth 树深度
def analysis_dependency(package_parent_id, dep_tree, z3_vars_set, depth):
    dependencies_dict = get_dep(package_parent_id)

    result_expr = list()

    for dependency_id in dependencies_dict:

        dependency_name = get_labels_name(dependency_id)

        version_range = dependencies_dict[dependency_id]

        dependency_normalize = normalize_req([dependency_name + version_range])

        for package_name in dependency_normalize:
            require_item = dependency_normalize[package_name]

            if require_item[0].__contains__('*'):
                expr = judge_version_range(package_name, "", "*", dep_tree, z3_vars_set, depth)
                if isinstance(expr, list):
                    continue
                result_expr.append(expr)

            elif len(require_item) == 1:
                opt = require_item[0].split(' ')[0]
                # >号全部改成了~线
                if opt.__contains__('>'):
                    opt = '~='
                expr = judge_version_range(package_name, opt, require_item[0].split(' ')[1],
                                           dep_tree, z3_vars_set, depth)
                if isinstance(expr, list):
                    continue
                result_expr.append(expr)

            else:
                expr = judge_version_range_by_list(package_name, require_item, dep_tree, z3_vars_set, depth)
                if isinstance(expr, list):
                    continue
                result_expr.append(expr)

    if result_expr:
        return add_and(result_expr)
    else:
        return []


# 只保留package_name的树
class MyNode(object):
    def __init__(self, host_name):
        self.host_name = host_name
        self.tree = list()
        self.tree.append(set())

    def __str__(self):
        return 'package : %s, children : ' % (
            self.host_name) + str(self.tree)

    def __repr__(self):
        return self.__str__()

    def insert(self, package_name, depth):
        if len(self.tree) <= depth:
            temp = set()
            temp.add(package_name)
            self.tree.append(temp)
        else:
            self.tree[depth].add(package_name)

    def level_order_traversal(self):
        result_list = []

        for temp_set in self.tree[::-1]:
            for package_name in temp_set:
                result_list.append(package_name)

        return result_list

    def get_node_set(self, depth):  # 获这一层之前的所有节点
        if depth < 0:
            return set()
        else:
            result = set()
            for i in range(0, depth):
                try:
                    result.update(self.tree[i])
                except IndexError:
                    break

        return result


# 添加定义语句和取最大值语句
def add_declare_and_max(var_list, expr_str_list):
    temp_list = []
    for var in var_list:
        temp_list.append('(declare-const ' + var + ' Int)')
    # for expr in expr_str_list:
    #     temp_list.append("(assert %s)" % expr)
    temp_list.append("(assert %s)" % add_and(expr_str_list))
    for var in var_list:
        temp_list.append('(maximize ' + var + ')')
    return ''.join(temp_list)


# 添加and语句
def add_and(expr_str_list):
    return "(and %s)" % (''.join(expr_str_list))


# 添加or语句
def add_or(expr_str_list):
    return "(or %s)" % (''.join(expr_str_list))


# 通用模糊匹配
def matching_version(version, version_id_dict):
    version_to_id = ''
    if version in version_id_dict:
        version_to_id = version_id_dict[version]
    else:
        data = ''
        # 模糊匹配 寻找id
        for x in list(version_id_dict.keys()):
            if x.startswith(version):
                data = x
                break
        if data != '':
            version_to_id = version_id_dict[data]
        else:
            version_keys = version_id_dict.keys()
            if version_keys:
                version_to_id = version_id_dict[list(version_keys)[-1]]
    return version_to_id


# 特殊模糊匹配 ~=
def matching_version_unusual(version, version_id_dict):
    version_pre = version[::-1].replace(version.split('.')[-1], '', 1)[::-1]
    version_to_id = ''
    data = ''

    # 从匹配到第一个开始算，一直到匹配的最后一个的下一个是~=的上界
    start = False
    for x in list(version_id_dict.keys()):
        if x.startswith(version_pre):
            start = True
            continue
        elif start:
            data = x
            break
        else:
            continue

    if data != '':
        version_to_id = version_id_dict[data]
    else:
        version_keys = version_id_dict.keys()
        if version_keys:
            version_to_id = version_id_dict[list(version_keys)[-1]]

    return version_to_id


def judge_version_range_by_list(package_name, opt_list, dep_tree, z3_vars_set, depth=0):
    version_id_dict = get_labels_id(package_name)
    result_expr = list()  # 表达式
    version_id_list = list(version_id_dict.values())  # 获取version id的list
    dep_constraint = list()  # 当钱包的子依赖约束
    version_id_exclude = []
    version_id_start = list(version_id_dict.values())[0]
    version_id_end = list(version_id_dict.values())[-1]

    # x = Int(package_name)  # 定义SMT变量
    if package_name not in z3_vars_set:
        z3_vars_set.add(package_name)

    # 确定版本范围
    for opt in opt_list:
        if opt.startswith('>'):
            version = opt.split(' ')[1]
            version_id_start = matching_version(version, version_id_dict)
        elif opt.startswith('<'):
            version = opt.split(' ')[1]
            version_id_end = matching_version(version, version_id_dict)
        elif opt.startswith('!'):
            version = opt.split(' ')[1]
            version_id_exclude.append(matching_version(version, version_id_dict))
        elif opt.startswith('~'):
            version = opt.split(' ')[1]
            version_id_start = matching_version(version, version_id_dict)
            version_id_end = matching_version_unusual(version, version_id_dict)

    start_index = version_id_list.index(version_id_start)
    end_index = version_id_list.index(version_id_end)

    result_expr.append("(< %s %s)" % (package_name, version_id_end))  # (< a 最大值)
    result_expr.append("(>= %s %s)" % (package_name, version_id_start))  # (>= a 1)
    if dep_tree.get_node_set(depth).__contains__(package_name):
        return add_and(result_expr)
    dep_tree.insert(package_name, depth)

    for version_id in version_id_list[start_index:end_index].__reversed__():
        if version_id in version_id_exclude:
            result_expr.append("(not (= %s %s))" % (package_name, version_id))
            continue

        temp = analysis_dependency(version_id, dep_tree, z3_vars_set, depth + 1)

        if isinstance(temp, list):
            dep_constraint.append("(= %s %s)" % (package_name, version_id))
            continue
        else:
            dep_constraint.append("(and (= %s %s) %s)" % (package_name, version_id, temp))

    if dep_constraint:
        return "(and %s %s)" % (add_and(result_expr), add_or(dep_constraint))
    else:
        return add_and(result_expr)


# 判断一个依赖的版本范围，并遍历解析范围内的所有依赖
# package_name 依赖的名字
# opt 比较符号 < > = != <= >=
# version 版本 可能不存在于依赖的版本列表中
# all_parent_node_set 输入依赖的所有父节点，用于过滤循环依赖
# dep_tree 构建简答依赖树，每层做set处理
# depth 当前依赖树递归深度
def judge_version_range(package_name, opt, version, dep_tree, z3_vars_set, depth=0):
    version_id_dict = get_labels_id(package_name)
    if version != "*":

        version_to_id = matching_version(version, version_id_dict)
        if version_to_id == '':
            return []
        # version 所对应的id，或者最近的id，可能有问题<=时

        result_expr = list()  # 表达式
        version_id_list = list(version_id_dict.values())  # 获取version id的list
        index = version_id_list.index(version_to_id)

        dep_constraint = list()  # 当钱包的子依赖约束

        # x = Int(package_name)  # 定义SMT变量
        if package_name not in z3_vars_set:
            z3_vars_set.add(package_name)

        if opt == '>':

            result_expr.append("(<= %s %s)" % (package_name, list(version_id_dict.values())[-1]))  # (<= a 最大值)
            result_expr.append("(>= %s %s)" % (package_name, version_to_id))  # (>= a 1)

            if dep_tree.get_node_set(depth).__contains__(package_name):
                return add_and(result_expr)
            dep_tree.insert(package_name, depth)

            for version_id in version_id_list[index + 1:].__reversed__():
                temp = analysis_dependency(version_id, dep_tree, z3_vars_set, depth + 1)

                if isinstance(temp, list):
                    dep_constraint.append("(= %s %s)" % (package_name, version_id))
                    continue
                else:
                    dep_constraint.append("(and (= %s %s) %s )" % (package_name, version_id, temp))

            if dep_constraint:
                return "(and %s %s)" % (add_and(result_expr), add_or(dep_constraint))
            else:
                return add_and(result_expr)

        elif opt == '>=' or opt == '^=':

            result_expr.append("(<= %s %s)" % (package_name, list(version_id_dict.values())[-1]))  #
            result_expr.append("(>= %s %s)" % (package_name, version_to_id))

            if dep_tree.get_node_set(depth).__contains__(package_name):
                return add_and(result_expr)
            dep_tree.insert(package_name, depth)

            for version_id in version_id_list[index:].__reversed__():
                temp = analysis_dependency(version_id, dep_tree, z3_vars_set, depth + 1)

                if isinstance(temp, list):
                    dep_constraint.append("(= %s %s)" % (package_name, version_id))
                    continue
                else:
                    dep_constraint.append("(and (= %s %s) %s)" % (package_name, version_id, temp))
            if dep_constraint:
                return "(and %s %s)" % (add_and(result_expr), add_or(dep_constraint))
            else:
                return add_and(result_expr)

        elif opt == '~=':
            upper_version_id = matching_version_unusual(version, version_id_dict)

            result_expr.append("(< %s %s)" % (package_name, upper_version_id))  #
            result_expr.append("(>= %s %s)" % (package_name, version_to_id))

            index = version_id_list.index(version_to_id)
            upper_index = version_id_list.index(upper_version_id)

            if dep_tree.get_node_set(depth).__contains__(package_name):
                return add_and(result_expr)
            dep_tree.insert(package_name, depth)

            for version_id in version_id_list[index:upper_index].__reversed__():
                temp = analysis_dependency(version_id, dep_tree, z3_vars_set, depth + 1)

                if isinstance(temp, list):
                    dep_constraint.append("(= %s %s)" % (package_name, version_id))
                    continue
                else:
                    dep_constraint.append("(and (= %s %s) %s)" % (package_name, version_id, temp))
            if dep_constraint:
                return "(and %s %s)" % (add_and(result_expr), add_or(dep_constraint))
            else:
                return add_and(result_expr)

        elif opt == '<':
            result_expr.append("(< %s %s)" % (package_name, version_to_id))
            if dep_tree.get_node_set(depth).__contains__(package_name):
                return add_and(result_expr)
            dep_tree.insert(package_name, depth)

            for version_id in version_id_list[:index].__reversed__():
                temp = analysis_dependency(version_id, dep_tree, z3_vars_set, depth + 1)

                if isinstance(temp, list):
                    dep_constraint.append("(= %s %s)" % (package_name, version_id))
                    continue
                else:
                    dep_constraint.append("(and (= %s %s) %s)" % (package_name, version_id, temp))

            if dep_constraint:
                return "(and %s %s)" % (add_and(result_expr), add_or(dep_constraint))
            else:
                return add_and(result_expr)

        elif opt == '<=':
            result_expr.append("(<= %s %s)" % (package_name, version_to_id))
            if dep_tree.get_node_set(depth).__contains__(package_name):
                return add_and(result_expr)
            dep_tree.insert(package_name, depth)

            for version_id in version_id_list[:index + 1].__reversed__():
                temp = analysis_dependency(version_id, dep_tree, z3_vars_set, depth + 1)

                if isinstance(temp, list):
                    dep_constraint.append("(= %s %s)" % (package_name, version_id))
                    continue
                else:
                    dep_constraint.append("(and (= %s %s) %s)" % (package_name, version_id, temp))

            if dep_constraint:
                return "(and %s %s)" % (add_and(result_expr), add_or(dep_constraint))
            else:
                return add_and(result_expr)

        elif opt == '!=':
            result_expr.append("(not (= %s %s))" % (package_name, version_to_id))
            # if dep_tree.get_node_set(depth).__contains__(package_name):
            #     return add_and(result_expr)
            # dep_tree.insert(package_name, depth)
            #
            # for version_id in version_id_list.__reversed__():
            #     if version_to_id == version_id:
            #         continue
            #
            #     temp = analysis_dependency(version_id, dep_tree, z3_vars_set, depth + 1)
            #
            #     if isinstance(temp, list):
            #         dep_constraint.append("(= %s %s)" % (package_name, version_id))
            #         continue
            #     else:
            #         dep_constraint.append("(and (= %s %s) %s)" % (package_name, version_id, temp))
            #
            # if dep_constraint:
            #     return "(and %s %s)" % (add_and(result_expr), add_or(dep_constraint))
            # else:
            return add_and(result_expr)

        elif opt == '==':
            result_expr.append("(= %s %s)" % (package_name, version_to_id))
            if dep_tree.get_node_set(depth).__contains__(package_name):
                return add_and(result_expr)
            dep_tree.insert(package_name, depth)

            dep_constraint = analysis_dependency(version_to_id, dep_tree, z3_vars_set, depth + 1)

            if isinstance(dep_constraint, list):
                return add_and(result_expr)
            else:
                return "(and %s %s)" % (add_and(result_expr), add_and(dep_constraint))

    else:
        version_id_list = list(version_id_dict.values())
        result_expr = list()

        result_expr.append("(<= %s %s)" % (package_name, version_id_list[-1]))
        result_expr.append("(>= %s %s)" % (package_name, version_id_list[0]))

        if dep_tree.get_node_set(depth).__contains__(package_name):
            return add_and(result_expr)

        dep_tree.insert(package_name, depth)

        if package_name not in z3_vars_set:
            z3_vars_set.add(package_name)

        if not version_id_list:
            return "(> %s 0)" % package_name

        dep_constraint = []

        for version_id in version_id_list.__reversed__():

            temp = analysis_dependency(version_id, dep_tree, z3_vars_set, depth + 1)

            if isinstance(temp, list):
                dep_constraint.append("(= %s %s)" % (package_name, version_id))
                continue
            else:
                dep_constraint.append("(and (= %s %s) %s)" % (package_name, version_id, temp))

        if dep_constraint:
            return "(and %s %s)" % (add_and(result_expr), add_or(dep_constraint))
        else:
            return add_and(result_expr)


def start_req(require, dep_tree):
    z3_vars_set = set()
    require_item = require.split(" ")
    package_name = require_item[0]
    if len(require_item) == 3:  # pip == 21
        opt = require.split(" ")[1]
        version_range = require.split(" ")[2]
        result = judge_version_range(package_name, opt, version_range, dep_tree, z3_vars_set)
    elif len(require_item) == 2:
        # error item
        result = ''
    else:  # pip
        result = judge_version_range(package_name, "", "*", dep_tree, z3_vars_set)

    return z3_vars_set, dep_tree, result


global_z3_vars_set = set()
global_dep_tree = MyNode('host')
global_expr_results = list()


def assemble_dep_tree(dep_tree):
    num = 0
    for nodes in dep_tree.tree:
        for package_name in nodes:
            global_dep_tree.insert(package_name, num)
        num += 1


def call_back_assemble(args):
    global_z3_vars_set.update(args[0])
    assemble_dep_tree(args[1])
    if args[2]:
        global_expr_results.append(args[2])


# 使用新的求解器求解依赖约束
# requirement_list 项目的依赖信息
# dep_tree 依赖树
def constraint_solving_refactor(requirement_list, dep_tree):
    req_pool = Pool(multiprocessing.cpu_count())  # 进程池大小设置为CPU数
    result_pool = []
    for require in requirement_list:
        result_pool.append(req_pool.apply_async(func=start_req, args=(require, dep_tree,), callback=call_back_assemble))

    req_pool.close()
    req_pool.join()

    final_expr_str = add_declare_and_max(global_z3_vars_set, global_expr_results)
    # print(final_expr_str)
    my_optimize_solver.add(z3.parse_smt2_string(final_expr_str))


if __name__ == '__main__':
    deps = normalize_req(['a<2', 'b<3,>1', 'c==3', 'd>=0.22.0,!=1.0.0,!=0.23.0', '#', '', 'abc'])
    print(list(deps.keys())[0])
    print(list(deps.keys())[-1])
    for dep in deps:
        print(dep)
        print(deps[dep])
