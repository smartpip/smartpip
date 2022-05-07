# author : wangcwangc
# time : 2022/1/16 11:14 AM
from z3 import *
from deptree.transform import *

stack = []  # 状态栈
flag_list = [0]  # constraint_solving 函数中的flag栈，用于回退时指定新的起点
lib_dict = []  # 记录所有出现过的库名，最后对照用

global depth_cnt
depth_cnt = 0

global final_flag
final_flag = 0


def dep_count():
    global depth_cnt
    depth_cnt += 1


def final_flag_change():
    global final_flag
    final_flag = 1


# 构建依赖树
# dependency_list : 第一层直接依赖，顺序为声明顺序
# 返回树形结构 dependency tree
def create_dependency_tree(requirements, dep_tree, package_info):
    for requirement in requirements:
        part = requirement.split(' ')
        tem_pkg = part[0]

        if dep_tree.package == package_info:
            dep_tree.insert(tem_pkg, requirement, dep_tree.depth + 1)
        else:
            for node in dep_tree.level_order_traversal(dep_tree):
                if node.package == package_info and node.depth == depth_cnt:
                    node.insert(tem_pkg, requirement, node.depth + 1)
                    break


# 回退依赖树状态
def pop_dependency_tree(dep_tree, package_info):
    for node in dep_tree.level_order_traversal(dep_tree):
        if node.package == package_info and node.depth == depth_cnt:
            node.clean()


# 树节点结构定义
class Node(object):
    def __init__(self, package, constrain, depth):
        self.package = package
        self.constrain = constrain
        self.depth = depth
        self.children = []

    def insert(self, package, constrain, depth):
        self.children.append(Node(package, constrain, depth))

    def clean(self):
        self.children = []

    def level_order_traversal(self, root):
        queue = [root]
        lib_list = []

        while queue:
            now_node = queue.pop(0)
            lib_list.append(now_node)
            for item in now_node.children:
                queue.append(item)

        return lib_list

    def show(self, root):
        for item in self.level_order_traversal(root):
            print(item.package, item.constrain)


# 标准化依赖格式为：name ==(operation) version
def normalize_req(requirements):
    dep_list = []
    f1 = 0
    tem = ''
    for item in requirements:  # 迭代每一个依赖
        if item != '' and item.startswith("#") is False:  # 当前行不是空或者不是以#开头
            requirement = item
            if requirement.__contains__("#"):
                requirement = requirement.split("#")[0]
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
                # print(requirement)
            elif len(requirement.split(" ")) == 1:
                tem_req = requirement.split(" ")
                if tem_req[1][0].isalnum() is False:
                    requirement = list(tem_req[1])
                    for j in range(1, len(requirement)):
                        if requirement[j - 1].isalnum() is False and requirement[j].isdigit():
                            requirement.insert(j, " ")
                            break
                elif tem_req[0][-1].isalnum() is False:
                    requirement = list(tem_req[0])
                    for j in range(1, len(requirement)):
                        if requirement[j - 1].isalnum() and requirement[j].isalnum() is False and \
                                requirement[j] != "-" and requirement[j] != "_" and requirement[j] != ".":
                            requirement.insert(j, " ")
                            break

                # if j == len(requirement) - 2 and requirement[j].isalnum() is False:
                #     requirement.insert(j + 1, " ")
                requirement = ''.join(requirement)
                # print(requirement)
            if f1 == 1:
                req = requirement.split(' ')[0]
                tem_noblank = tem[1].strip(" ")
                tem_q = req + tem_noblank
                requirements.append(tem_q)
                f1 = 0

            requirement = requirement.strip()
            dep_list.append(requirement)

    return dep_list


# 向s中添加依赖项并判定是否可解
# liblist: 装入的依赖项，一起装入方便回退
# 有问题
def con_add(liblist, s):
    # 有问题，匹配不到
    temp = []
    for item in liblist:
        part = item.split(" ")
        if len(part) != 3:
            continue

        try:
            # @@@
            # 根据package_name和version 找对应的id
            version_to_id_list = get_labels_id(part[0])
            if part[2] in version_to_id_list:
                cmp_label = version_to_id_list[part[2]]
            else:
                # 模糊匹配
                data = [x for x in list(version_to_id_list.keys()) if x.startswith(part[2])]
                if data:
                    cmp_label = version_to_id_list[data[0]]
                else:
                    continue

            x = Int(part[0])
            s.maximize(x)
            if part[1] == '>':
                temp.append(x > cmp_label)
            elif part[1] == '>=' or part[1] == '~=' or part[1] == '^=':
                temp.append(x >= cmp_label)
            elif part[1] == '<':
                temp.append(x < cmp_label)
            elif part[1] == '<=':
                temp.append(x <= cmp_label)
            elif part[1] == '!=':
                temp.append(x != cmp_label)
            elif part[1] == '==':
                temp.append(x == cmp_label)
        except KeyError:
            print("This package name " + part[0] + ' is unknown')
            pass

    if temp:
        s.add(temp)
    # print('-----------')
    # print('true:')
    # print(s.check())
    # print(s)
    # print('-----------')
    if s.check() == sat:
        return True
    else:
        # print('?:')
        # print(s.check())
        s.pop()
        return False


def judge_version_range_local(package_name, opt, version_range, s):
    if version_range != "*":
        try:
            version_list = get_labels_id(package_name)

            if version_range in version_list:
                version_to_id = version_list[version_range]
            else:
                # 模糊匹配
                data = [x for x in list(version_list.keys()) if x.startswith(version_range)]
                if data:
                    version_to_id = version_list[data[0]]
                else:
                    print("error ")
                    return
            temp = list()
            x = Int(package_name)
            s.maximize(x)
            if opt == '>':
                temp.append(x > version_to_id)
            elif opt == '>=' or opt == '~=' or opt == '^=':
                temp.append(x >= version_to_id)
            elif opt == '<':
                temp.append(x < version_to_id)
            elif opt == '<=':
                temp.append(x <= version_to_id)
            elif opt == '!=':
                temp.append(x != version_to_id)
            elif opt == '==':
                temp.append(x == version_to_id)

            if temp:
                s.add(temp)

        except Exception as e:
            print(e)
    else:
        print("*")


# 对namelist中第一个包用transform函数寻找依赖，并将其装入s和dep_tree，新依赖项装入namelist
# 装入s后如果有解则递归调用，若无解则让namelist, s和dep_tree全部退回上一状态
# namelist: 需要寻找依赖的库名单
# s: 求解器断言栈
# dep_tree: 依赖树
# dep_flag: 深度标记，用于生成树时区分该依赖位于哪一层
# flag: 记录当前采用的依赖的标记，比如库a有5个可用的版本依赖，第一个版本的依赖如果无法满足，则在退回时将flag设置为1，直接从第2个版本开始添加
def constraint_solving(namelist, s, dep_tree, dep_flag, flag=0):
    if namelist:
        # print('stack:')
        # print(stack)
        # print('namelist:')
        # print(namelist)
        now = namelist.pop(0)
        stack.append(now)
        now = now.split(' ')
        now_copy = now
        now_name = now[0]
        # print('now:')
        # print(now_name)
        requirements = []

        if len(now) == 1:
            version = transform(now_name)
            requirements = transform(now_name, major_v=version, flag=1, icon=2)

        else:
            m_v = now[-1]
            m_v_split = m_v.split('.')
            if m_v_split[-1] == '*':
                now[1] = '>='
                m_v_split[-1] = '0'
                m_v = '.'.join(m_v_split)
                temp = m_v_split[-2]
                m_v_split[-2] = str(int(temp) + 1)
                m_v1 = '.'.join(m_v_split)
                now_copy[-1] = m_v1
                now_copy[1] = '<'
                new = ' '.join(now_copy)
                namelist.insert(0, new)

            if now[1] == '>=':
                requirements = transform(now_name, major_v=m_v, flag=1, icon=1)
            elif now[1] == '<=':
                requirements = transform(now_name, major_v=m_v, flag=1, icon=2)
            elif now[1] == '>' or now[1] == '!=':
                requirements = transform(now_name, major_v=m_v, flag=1, icon=3)
            elif now[1] == '<':
                requirements = transform(now_name, major_v=m_v, flag=1, icon=4)
            elif now[1] == '~=' or now[1] == '^=' or now[1] == '^' or now[1] == '~':
                requirements = transform(now_name, major_v=m_v, flag=1, icon=5)
            elif now[1] == '==':
                requirements = transform(now_name, major_v=m_v, flag=1, icon=0)
            else:
                cmp = list(now[1])[0]
                if cmp == '>':
                    requirements = transform(now_name, major_v=m_v, flag=1, icon=3)
                elif cmp == '<':
                    requirements = transform(now_name, major_v=m_v, flag=1, icon=4)
        dep_list = []
        if requirements:
            for item in requirements:
                dep_list.append(normalize_req(item))
        # print('dep_list')
        # print(dep_list)
        if len(dep_list) == 0:
            if flag == 0:
                dep_flag -= 1
                if dep_flag == 0:
                    dep_flag = len(namelist)
                    dep_count()
                constraint_solving(namelist, s, dep_tree, dep_flag)
            else:
                dep_flag += 1
                pkg = stack.pop()
                namelist.insert(0, pkg)
                pop_dependency_tree(dep_tree, pkg)
                s.pop()
                if stack:
                    dep_flag += 1
                    namelist.insert(0, stack.pop())
                    constraint_solving(namelist, s, dep_tree, dep_flag, flag=flag)
            # print('now flag:')
            # print(flag)
        else:
            if flag == len(dep_list) and len(dep_list) != 0:
                s.pop()
                namelist.insert(0, stack.pop())
                if len(stack) == 0:
                    print('This package cannot be solved')
                    exit(-1)
                pkg = stack.pop()
                namelist.insert(0, pkg)
                pop_dependency_tree(dep_tree, pkg)
                dep_flag += 1
                constraint_solving(namelist, s, dep_tree, dep_flag, flag=flag_list.pop())
            # print("solver:")
            # print(s)
            for i in range(flag, len(dep_list)):
                s.push()
                if con_add(dep_list[i], s):
                    flag_list.append(i + 1)
                    create_dependency_tree(dep_list[i], dep_tree, now_name)
                    for item in dep_list[i]:
                        eachname = item.split(' ')[0]
                        if eachname not in lib_dict:
                            lib_dict.append(eachname)
                        namelist.append(item)
                    dep_flag -= 1
                    if dep_flag == 0:
                        dep_flag = len(namelist)
                        dep_count()
                    constraint_solving(namelist, s, dep_tree, dep_flag)
                    break
                else:
                    if i == len(dep_list) - 1:
                        pkg = stack.pop()
                        namelist.insert(0, pkg)
                        pop_dependency_tree(dep_tree, pkg)
                        if stack:
                            dep_flag += 1
                            namelist.insert(0, stack.pop())
                            constraint_solving(namelist, s, dep_tree, dep_flag, flag=flag_list.pop())
                        else:
                            final_flag_change()
