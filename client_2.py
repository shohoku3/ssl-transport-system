import socket
import ssl
import threading
import hashlib
import json
import os
import pickle
import time
import struct
import tkinter as tk
from tkinter import filedialog
import re
import prettytable as pt


class Client(object):
    down_filelist = list()

    def __init__(self):
        self.Address = ('127.0.0.1', 9443)
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.context.load_verify_locations('cert/ca.crt')
        self.sock = socket.create_connection(self.Address)
        self.ssock = self.context.wrap_socket(self.sock, server_hostname='localhost')

    def Connection(self):
        # t1 = threading.Thread(target=self.SendMsg)
        t2 = threading.Thread(target=self.RecvMsg)
        # t1.start()
        t2.start()

    def SendMsg(self, msg):
        self.ssock.send(msg.encode('Utf-8'))

    def RecvMsg(self):
        while True:
            try:
                resp = self.ssock.recv(1024).decode("utf-8")
                resp = json.loads(resp)
                if resp['msg'] == 'login success':
                    print(resp['data'])
                    self.ActionSelectLogined()
                elif resp['msg'] == 'login default':
                    print(resp['data'])
                    self.Login()
                elif resp['msg'] == 'register success':
                    print(resp['data'])
                    self.Login()
                elif resp['msg'] == 'register default':
                    print(resp['data'])
                    self.Register()
                elif resp['msg'] == 'Transport success':
                    print(resp['data'])
                    self.ActionSelectLogined()
                elif resp['msg'] == 'Transport default':
                    print(resp['data'])
                    self.SelectFile()
                elif resp['msg'] == 'ListFile success':
                    tb = pt.PrettyTable()
                    tb.field_names = ["filename"]
                    print(len(resp['data']))
                    for i in range(len(resp['data'])):
                        print(resp['data'][i])
                        tb.add_row(resp['data'][i])
                    print(tb)
                    self.ActionSelectLogined()
                elif resp['msg'] == 'DownFileList success':

                    tb = pt.PrettyTable()
                    tb.field_names = ["filename"]
                    for i in resp['data']:
                        tb.add_row(list(i))
                    print(tb)
                    file_list = resp['data']
                    self.DownLoadFile(file_list)
                elif resp['msg'] == 'begin file transport':
                    # print('开始文件接收')
                    self.RecvFile()
                elif resp['msg'] == 'ListUsers success':
                    tb = pt.PrettyTable()
                    tb.field_names = ["username", "password", 'action']
                    tb.add_row([resp['data']['name'], resp['data']['password'], resp['data']['action']])
                    print(tb)


            except Exception as ret:
                self.ssock.close()
                print(ret)
                break

    def ActionSelect(self):
        print('请选择您要进行的操作\n登录 1\n注册 2')
        action = input('请输入要选择的操作')
        if action == '1':
            self.Login()
        elif action == '2':
            self.Register()
        elif len(action) == 0:
            print('警告：选项不能为空')
            self.ActionSelect()

    def ActionSelectLogined(self):
        print('请选择您要使用的操作\n上传文件 1 \n查看文件列表 2\n下载文件 3\n用户管理 4\n空间查询 5')
        action = input('请输入要选择的操作')
        if action == '1':
            self.SelectFile()
        elif len(action.strip()) == 0:
            print('警告：选项不能为空')
            self.ActionSelectLogined()
        elif action == '2':
            self.ListFile()
        elif action == '3':
            self.DownloadFileList()
        elif action == '4':
            self.UserList()

    def Login(self):
        name = input('请输入用户名:')
        password = input('请输入密码:')
        if len(name.strip()) == 0:
            print('警告：用户名不能为空，请重新输入')
            self.Login()
        elif len(password.strip()) == 0:
            print('警告：密码不能为空，请重新输入.')
            self.Login()
        else:
            api = 'api/get/login'
            md5 = hashlib.md5()
            md5.update(str(password).encode('utf-8'))
            userinfo = {'name': name, 'password': md5.hexdigest(), 'api': api}
            userinfo = json.dumps(userinfo)
            self.SendMsg(userinfo)

    def Register(self):
        name = input('请输入用户名:')
        password = input('请输入密码:')
        c_password = input('请再次输入密码')
        if len(name.strip()) == 0:
            print('警告：用户名不能为空，请重新输入')
            self.Register()
        elif len(password.strip()) == 0:
            print('警告：密码不能为空，请重新输入.')
            self.Register()

        elif c_password != password:
            print('警告：两次输入的密码不一致，请重新输入。')
            self.Register()
        else:
            api = 'api/get/register'
            md5 = hashlib.md5()
            md5.update(str(password).encode('utf-8'))
            userinfo = {'name': name, 'password': md5.hexdigest(), 'api': api}
            userinfo = json.dumps(userinfo)
            self.SendMsg(userinfo)

    def SelectFile(self):
        print('请选择需要上传的文件/文件夹')
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename()
        if len(file_path) != 0:
            print('Filepath:', file_path)
            self.SendFile(file_path)
        else:
            print('警告：没有选择文件')
            self.ActionSelectLogined()

    def ListFile(self):
        api = 'api/get/filelist'
        userinfo = {'api': api}
        userinfo = json.dumps(userinfo)
        self.SendMsg(userinfo)

    def SendFile(self, file_path):
        try:
            # 发送信号 告诉服务器 开始文件接收,调用新线程
            api = 'api/post/file'
            info = {'api': api}
            info = json.dumps(info)
            self.SendMsg(info)
            header_struct = struct.Struct('i1024s')
            # data_struct = struct.Struct('1024s')
            file_name = re.findall(r'[^\\/:*?"<>|\r\n]+$', file_path)
            header = {
                'file_name': file_name[0],
                'file_size': os.path.getsize(file_path),
                'file_ctime': os.path.getctime(file_path),
                'file_atime': os.path.getatime(file_path),
                'file_mtime': os.path.getmtime(file_path)
            }
            # 序列化
            header_str = pickle.dumps(header)
            # 把序列化的header长度和header正文打包发送
            self.ssock.send(header_struct.pack(*(len(header_str), header_str)))
            with open(file_path, 'rb') as f:
                line = f.read()
                self.ssock.sendall(line)
        except Exception as exp:
            print(exp)

    def DownLoadFile(self, file_list):
        while True:
            file_name = input('输入需要下载的文件')
            # 发送信号 告诉服务器 开始文件下载
            if file_name not in file_list:
                print('警告：请从文件列表中选择您输入的文件不存在')
                continue
            else:
                info = {'api': 'api/get/file', 'data': file_name}
                info = json.dumps(info)
                self.SendMsg(info)
                break

    def DownloadFileList(self):
        print('获取到的可下载目录')
        api = 'api/get/downfilelist'
        userinfo = {'api': api}
        userinfo = json.dumps(userinfo)
        self.SendMsg(userinfo)

    def RecvFile(self):
        starttime = time.time()
        header_struct = struct.Struct('i1024s')
        # 接收序列化的header数据包
        packed_haeder = self.ssock.recv(1024 + 4)
        # 解包得到序列化的header的长度和header正文
        header_size, header_s = header_struct.unpack(packed_haeder)
        if header_size == 0:
            return False
        else:
            try:
                # 反序列化得到正文
                header = pickle.loads(header_s)
                file_name = header['file_name']
                file_size = header['file_size']
                with open('./local_repository/%s' % (file_name), 'wb') as f:
                    recv_size = 0
                    while recv_size < file_size:
                        res = self.ssock.recv(1024)
                        f.write(res)
                        recv_size += len(res)
                        recv_per = int(recv_size / file_size * 100)
                        print_progress(recv_per)
                endtime = time.time()
                time_consuming = endtime - starttime
                print('下载耗时：' + str(int(time_consuming % 60)) + 's')
                self.ActionSelectLogined()
            except Exception as exp:
                print(exp)

    def UserList(self):
        api = 'api/get/userlist'
        userinfo = {'api': api}
        userinfo = json.dumps(userinfo)
        self.SendMsg(userinfo)


def print_progress(percent, width=50):
    # 字符串拼接的嵌套使用
    show_str = ('下载中！[%%-%ds]' % width) % (int(width * percent / 100) * '>')
    print('\r%s %d%%' % (show_str, percent), end='')


def main():
    C = Client()
    C.Connection()
    C.ActionSelect()


if __name__ == '__main__':
    main()
