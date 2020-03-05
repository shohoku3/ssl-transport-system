# ssl-transform-system
### 概述

一个基于SSL的简单文件安全传输系统


### 功能
- [x] 简单登录注册 基于文本文件
- [x] 单方认证证书
- [x] openssl 自签发证书
- [x] 简单应用层协议设计 基于SSL
- [x] 文件传输下载 基于SSL
- [ ] 多线程 线程管理
- [ ] 用户管理
- [x] 文件浏览
- [x] 下载进度打印
- [ ] 服务器日志记录
- [ ] 读写磁盘文件/磁盘空间检查
- [ ] 封装协议，提供外部接口
- [x] 使用自定义协议接收/发送
- [x] 命令解释/图形化界面

### 文件结构
	├─.idea
	│  └─inspectionProfiles
	├─cert 证书
	├─database  数据库
	├─file_repository  服务端仓库
	├─local_repository 本地仓库
	├─venv  
	└─资料
	└─client_2.py 客户端
	└─server_2.py 服务端


### 参考

- [python实现简单的文件传输程序-TCP](https://blog.csdn.net/Tifinity/article/details/90372654)
- [手把手教你实现自定义的应用层协议](https://segmentfault.com/a/1190000008740863#item-7)
- [证书签发](https://www.jianshu.com/p/6997d5dd8258)
- [Python3+ssl实现加密通信](https://www.cnblogs.com/lsdb/p/9397530.html) 
- [廖雪峰Python](https://www.liaoxuefeng.com/wiki/1016959663602400)
- [进度条打印函数](https://www.cnblogs.com/suguangti/p/10802720.html)
- [python 函数内部修改全局变量](https://blog.csdn.net/zy13270867781/article/details/80662967)
- [Python 线程安全（同步锁Lock）详解](http://c.biancheng.net/view/2617.html)
- [python基于tcp/ip协议的服务端(支持多个客户端同时连接处理)](https://www.cnblogs.com/yuanshuang-club/p/11541622.html)
- [python一句话之利用文件对话框获取文件路径](https://blog.csdn.net/shawpan/article/details/78759199)