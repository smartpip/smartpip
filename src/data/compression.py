# author : wangcwangc
# time : 2021/12/23 8:33 PM
import gzip
import json
import time


def read_json_file(file):
    f = open(file, 'r')
    data = json.load(f)
    return data


def read_gzip_file_to_json(gzip_file_path):
    with gzip.open(gzip_file_path, 'rt', encoding='UTF-8') as zipfile:
        json_data = json.load(zipfile)
        return json_data


def write_json_to_gzip_file(json_path, gzip_file_path):
    with gzip.open(gzip_file_path, 'wt', encoding='UTF-8') as zipfile:
        json.dump(read_json_file(json_path), zipfile)


if __name__ == '__main__':
    # write_json_to_gzip_file("dependency.json", "dependency.shrink")
    # write_json_to_gzip_file("dep_set.json", "dep_set.shrink")
    # write_json_to_gzip_file("label.json", "label.shrink")
    start = time.time()
    # read_gzip_file_to_json("dependency.shrink")
    # read_gzip_file_to_json("label.shrink")
    read_gzip_file_to_json("dep_set.shrink")
    end = time.time()
    print(end - start)
    # start = end
    # read_json_file("dependency.json")
    # read_json_file("label.json")
    # end = time.time()
    # print(end - start)
    # start = time.time()
    # labels = read_gzip_file_to_json("label.shrink")
    # dependencies = read_gzip_file_to_json("dependency.shrink")
    # end = time.time()
    # print(end - start)
    # start = end
    # for dep in dependencies:
    #     if dep == labels["requests"]["2.22.0"]:
    #         print(dep)
    # end = time.time()
    # print(end - start)
    # start = end
    # print(labels["requests"]["2.22.0"])
    # end = time.time()
    # print(end - start)
    # start = end
    # requests_id = labels["requests"]["2.22.0"]
    # print(dependencies[str(requests_id)])
    # end = time.time()
    # print(end - start)
