# author : wangcwangc
# time : 2021/11/24 8:02 PM

myFunction = """
def setup(**atrrs):
    name = ""
    version = ""
    for k, v in atrrs.items():
        if k.__eq__("name"):
            name = v
            break
    for k, v in atrrs.items():
        if k.__eq__("version"):
            version = v
            break
    for k, v in atrrs.items():
        if k.__eq__("install_requires"):
            print(name)
            print(version)
            for req in v:
                print(req)
            break
    """
