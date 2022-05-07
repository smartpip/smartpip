# author : wangcwangc
# time : 2022/1/5 6:47 PM
import gzip
import os
import socket
import json

TCP_PORT = 8888
LOCAL_HOST = "127.0.0.1"

current_folder = os.path.dirname(os.path.abspath(__file__)) + "/"


def transform_labels(labels):
    data = dict()
    for label in labels:
        versions = labels[label]
        for version in versions:
            if str(version) == "*":
                name = str(label)
            else:
                name = str(label) + "-" + str(version)
            data[str(versions[version])] = name
    return data


def start_server():
    labels = read_gzip_file_to_json(current_folder + "label.shrink")
    dependencies = read_gzip_file_to_json(current_folder + "dependency.shrink")
    dependency_set = read_gzip_file_to_json(current_folder + "dep_set.shrink")
    labels_name = transform_labels(labels)
    # create socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # listen port
    server.bind((LOCAL_HOST, TCP_PORT))
    server.listen(1000)
    print('Server is started.')
    print('Waiting for connection...')
    while True:
        connecting, address = server.accept()
        receive = connecting.recv(10240).decode()
        if receive:
            if receive.split("@@")[0] == 'i':
                package_name = receive.split("@@")[1]
                try:
                    package_data = labels[package_name]
                except KeyError:
                    package_data = {'error': 400}

                send_data = json.dumps(package_data)
                connecting.send(send_data.encode())

            if receive.split("@@")[0] == 'n':
                package_id = receive.split("@@")[1]
                send_data = labels_name[package_id]

                connecting.send(send_data.encode())

            if receive.split("@@")[0] == 'd':
                package_id = receive.split("@@")[1]
                try:
                    dependency_data = dependencies[str(package_id)]
                except KeyError:
                    dependency_data = {"error": 404}

                # send data
                str_json = json.dumps(dependency_data)
                connecting.send(str_json.encode())

            if receive.split("@@")[0] == 'ds':
                package_id = receive.split("@@")[1]
                try:
                    package_dependency_set = dependency_set[str(package_id)]
                except KeyError:
                    package_dependency_set = {"error": 404}
                str_json = json.dumps(package_dependency_set)
                connecting.send(str_json.encode())


def read_gzip_file_to_json(gzip_file_path):
    with gzip.open(gzip_file_path, 'rt', encoding='UTF-8') as zipfile:
        json_data = json.load(zipfile)
        return json_data


if __name__ == "__main__":
    start_server()
