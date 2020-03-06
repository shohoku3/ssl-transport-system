import socket
import ssl
import threading
import json
import struct
import os
import pickle
import time

lock = threading.Lock()


class Server(object):

    def __init__(self):
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain('cert/server.crt', 'cert/server.key')
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.Address = ('127.0.0.1', 9443)
        self.server_sock.bind(self.Address)
        self.server_sock.listen(5)
        self.server_sscok = self.context.wrap_socket(self.server_sock, server_side=True)

    def WaitClient(self):
        print('监听等待客户端连接......')
        while True:
            self.clientsocket, self.clientAddresss = self.server_sscok.accept()
            print("%s已经连接成功！" % str(self.clientAddresss))
            t1 = threading.Thread(target=self.RecvMsg)
            t1.start()

    def RecvMsg(self):
        while True:
            try:
                recvmsg = self.clientsocket.recv(1024)
                recvmsg = recvmsg.decode('utf-8')
                recvmsg = json.loads(recvmsg)
                # print(recvmsg['api'])
                if recvmsg['api'] == 'api/get/login':
                    self.check_login(recvmsg['name'], recvmsg['password'])
                elif recvmsg['api'] == 'api/get/register':
                    self.check_register(recvmsg['name'], recvmsg['password'])
                elif recvmsg['api'] == 'api/post/file':
                    # print('检测到文件传输请求')
                    self.RecvFile()
                elif recvmsg['api'] == 'api/get/file':
                    # print('检测到文件下载请求)
                    file_name = recvmsg['data']
                    self.SendFile(file_name)
                elif recvmsg['api'] == 'api/get/filelist':
                    self.file_list()
                elif recvmsg['api'] == 'api/get/downfilelist':
                    self.downfile_list()
                elif recvmsg['api'] == 'api/get/userlist':
                    self.users_list()
                elif recvmsg['api']=='api/del/username':
                    self.del_user(recvmsg['data'])
                elif recvmsg['api']=='api/get/dataspace':
                    self.checkdataspace()
            except Exception as ret:
                self.clientsocket.close()
                print(ret)
                break

    def RecvFile(self):
        header_struct = struct.Struct('i1024s')
        # 接收序列化的header数据包
        starttime = time.time()
        packed_haeder = self.clientsocket.recv(1024 + 4)
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
                with open('./file_repository/%s' % (file_name), 'wb') as f:
                    recv_size = 0
                    while recv_size < file_size:
                        res = self.clientsocket.recv(1024)
                        f.write(res)
                        recv_size += len(res)
                        recv_per = int(recv_size / file_size * 100)
                        print_progress(recv_per)
                endtime = time.time()
                resp = {'msg': 'Transport success', 'code': 200, 'data': '传输完成'}
                resp = json.dumps(resp)
                self.SendMsg(resp)
                time_consuming = endtime - starttime
                print('上传耗时：' + str(int(time_consuming % 60)) + 's')

            except Exception as exp:
                msg = 'Transport default'
                data = '警告：传输失败'
                code = 300
                resp = {'msg': msg, 'code': code, 'data': data}
                resp = json.dumps(resp)
                self.SendMsg(resp)
                print(exp)

    def SendMsg(self, msg):
        self.clientsocket.send(msg.encode('utf-8'))

    def SendFile(self, file_name):
        try:
            # 发送信号告诉客户端接收文件
            info = {'msg': 'begin file transport', 'code': 200, 'data': '准备开始文件传输'}
            info = json.dumps(info)
            self.SendMsg(info)
            header_struct = struct.Struct('i1024s')
            # data_struct = struct.Struct('1024s')
            file_path = './file_repository' + '/' + file_name
            header = {
                'file_name': file_name,
                'file_size': os.path.getsize(file_path),
                'file_ctime': os.path.getctime(file_path),
                'file_atime': os.path.getatime(file_path),
                'file_mtime': os.path.getmtime(file_path)
            }
            # 序列化
            header_str = pickle.dumps(header)
            # 把序列化的header长度和header正文打包发送
            self.clientsocket.send(header_struct.pack(*(len(header_str), header_str)))
            with open(file_path, 'rb') as f:
                for line in f:
                    self.clientsocket.send(line)
        except Exception as exp:
            print(exp)

    def check_login(self, username, password):
        with open("./database/users.txt", 'r+') as f:
            user_info = f.readlines()
        for i in range(len(user_info)):
            user_info[i]=user_info[i].rstrip('\n')
        user={'name':username,'password':password}
        if str(user) in user_info:
            code = 200
            data = '成功：登录成功可以开始进一步操作'
            msg = 'login success'
            resp = {'msg': msg, 'code': code, 'data': data}
            resp = json.dumps(resp, ensure_ascii=False)
            self.SendMsg(resp)
        else:
            msg = 'login default'
            data = '警告：登录失败用户名或密码错误'
            code = 300
            resp = {'msg': msg, 'code': code, 'data': data}
            resp = json.dumps(resp)
            self.SendMsg(resp)

    def check_register(self, username, password):
        with open("./database/users.txt", 'r+') as f:
            user_info = f.readlines()
        user_name=[]
        for i in range(len(user_info)):
            user_name.append(eval(user_info[i].rstrip('\n'))['name'])
        if username not in user_name:
            user = {'name': username, 'password': password}
            user = json.dumps(user)
            f=open("./database/users.txt", 'a+')
            f.write(user+'\n')
            f.close()
            resp = {'msg': 'register success', 'code': 200, 'data': '成功：注册成功'}
            resp = json.dumps(resp)
            print('fasong')
            self.SendMsg(resp)
        else:
            resp = {'msg': 'register default', 'code': 300, 'data': '警告：注册失败，用户名重复'}
            resp = json.dumps(resp)
            self.SendMsg(resp)

    def file_list(self):
        filelist = os.listdir('./file_repository')
        data=[]
        for i in filelist:
            file_path = './file_repository/' + i
            file_info = {'file_name': i,
                         'file_size': self.filesize_format(os.path.getsize(file_path))
                         }
            data.append(file_info)
        resp = {'msg': 'ListFile success', 'code': 200, 'data': data}
        resp = json.dumps(resp)
        self.SendMsg(resp)

    def filesize_format(self,file_size):
        if file_size<1024*1024:
            file_size=str(int(file_size / float(1024)))+'KB'
            return file_size
        elif 1024*1024<file_size<1024*1024*1024:
            file_size=str(int(file_size /float(1024*1024)))+'MB'
            return file_size

    def downfile_list(self):
        filelist = os.listdir('./file_repository')
        resp = {'msg': 'DownFileList success', 'code': 200, 'data': filelist}
        resp = json.dumps(resp)
        self.SendMsg(resp)

    def users_list(self):
        with open("./database/users.txt", 'r+') as f:
            user_info = f.readlines()
        for i in range(len(user_info)):
            user_info[i] = eval(user_info[i].rstrip('\n'))
        resp = {'msg': 'ListUsers success', 'code': 200, 'data': user_info}
        resp = json.dumps(resp)
        self.SendMsg(resp)

    def del_user(self,username):
        pass

    def checkdataspace(self):
        filelist=os.listdir('./file_repository')
        allfilesize=0
        dataspace=1*1024
        for i in filelist:
            allfilesize+=os.path.getsize('./file_repository/'+i)
        allfilesize=self.filesize_format(allfilesize)
        if allfilesize[-2:]=='KB':
            Percentage_used='0%'
            resp = {'msg': 'checkdataspace success', 'code': 200, 'data': {'Percentage_used':Percentage_used,'allfilesize':allfilesize,'dataspace':str(dataspace)+'MB'}}
            resp = json.dumps(resp)
            self.SendMsg(resp)
        else:
            Percentage_used=str(round(int(allfilesize[:-2])/dataspace,2))+'%'
            resp = {'msg': 'checkdataspace success', 'code': 200, 'data': {'Percentage_used':Percentage_used,'allfilesize':allfilesize,'dataspace':str(dataspace)+'MB'}}
            resp = json.dumps(resp)
            self.SendMsg(resp)

def print_progress(percent, width=50):
    # 字符串拼接的嵌套使用
    show_str = ('上传中！[%%-%ds]' % width) % (int(width * percent / 100) * '>')
    print('\r%s %d%%' % (show_str, percent), end='')


def main():
    S = Server()
    S.WaitClient()


if __name__ == '__main__':
    main()
