# Online_Chat

# V1

## 初版网络聊天室

1.登录，注册界面；

2.正常聊天，添加好友界面。



使用范围：

可用于实验室局域网、家庭局域网中，也可用于自己的公网IP服务器中，分享给附件的人尝鲜体验。



项目介绍及开源协议：

1.本项目皆为独立自主完成，后续会不时进行迭代、优化。如有需要或者使用反馈也可以微信联系：automatic_learning

2.本项目开源，免费提供给学生学习使用，禁止商用！！！禁止商用！！！禁止商用！！！

3.本项目旨在为相关专业学生及广大爱好者进行学习交流使用，禁止传播违法信息，违者作者有权追责。



如有需要代做相关项目，诸如：嵌入式、物联网、前后端开发，可联系作者微信：automatic_learning



## 本系统采用Python + Web + NGINX代理架构

### 一、安装NGINX

1. 更新系统包

首先，建议更新系统的包列表，以确保你能够安装最新版本的软件包。运行以下命令：

sudo apt update

 

2. 安装 Nginx

在 Ubuntu/Debian 系统上，Nginx 包已经包含在官方的软件库中。可以通过以下命令安装 

sudo apt install nginx

安装过程会自动下载和安装 Nginx 及其依赖包。

 

3. 启动和启用 Nginx 服务

安装完成后，可以使用 systemctl 命令启动 Nginx 服务，并使其在系统启动时自动启动：

sudo systemctl start nginx  # 启动 Nginx

sudo systemctl enable nginx  # 设置 Nginx 开机自启

 

4. 检查 Nginx 是否安装成功

安装并启动 Nginx 后，你可以通过以下命令来检查 Nginx 服务的状态：

sudo systemctl status nginx

如果 Nginx 启动成功，你应该会看到类似于下面的输出：

 

● nginx.service - A high performance web server and a reverse proxy server

  Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)

  Active: active (running) since Tue 2024-11-05 10:15:00 UTC; 1h 23min ago

   Docs: man:nginx(8)

 Main PID: 1234 (nginx)

  Tasks: 2 (limit: 4915)

  Memory: 6.3M

  CGroup: /system.slice/nginx.service

​      ├─1234 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;

​      └─1235 nginx: worker process

 

5. 配置防火墙

如果你的服务器启用了防火墙，可能需要允许 Nginx 的 HTTP 和 HTTPS 流量通过防火墙。可以通过 ufw (Uncomplicated Firewall) 来允许这些流量：

sudo ufw allow 'Nginx Full'

这条命令将允许 HTTP（80端口）和 HTTPS（443端口）流量。如果你只想允许 HTTP 流量，可以运行：

sudo ufw allow 'Nginx HTTP'

 

6. 测试 Nginx 是否工作

安装并启动 Nginx 后，你可以在浏览器中访问服务器的 IP 地址来确认 Nginx 是否成功运行。默认情况下，Nginx 会显示一个欢迎页面。

例如，如果你的服务器 IP 地址是 192.168.1.100，你可以在浏览器中输入：

http://192.168.1.100

如果一切正常，你应该能看到 Nginx 的默认欢迎页面。

 

7. 配置 Nginx（可选）

安装并启动 Nginx 后，你可以根据需要进一步配置它。Nginx 的配置文件通常位于 /etc/nginx/nginx.conf，虚拟主机配置文件位于 /etc/nginx/sites-available/ 目录下。

编辑 Nginx 配置文件：

sudo nano /etc/nginx/nginx.conf

 

编辑完成后，你可以使用以下命令重新加载 Nginx 配置：

sudo systemctl reload nginx



### 二、安装Python及Flask

第一步：安装必要软件

1. 安装 Python 3 和 pip（Ubuntu 24.04 默认已装，但确认一下）

sudo apt update

sudo apt install -y python3 python3-pip python3-venv

 

2. 创建项目目录

mkdir -p ~/webchat

cd ~/webchat

 

3. 创建虚拟环境（推荐）

python3 -m venv venv

source venv/bin/activate

 

4. 安装轻量 Web 框架（我们用 Flask，简单高效）

pip install flask

轻量、无数据库依赖；可用 JSON 文件或纯文本模拟用户/消息存储；适合单机部署。

 

​	5.设计本地数据存储结构（不用数据库！）

在 ~/webchat/data/ 下用 JSON 文件 存储所有数据：

mkdir -p data/users data/messages data/friends data/requests

 

data/users/：每个用户一个 JSON 文件，如 alice.json

data/messages/：每个会话一个文件，如 alice_bob.json

data/friends/：每个用户的好友列表，如 alice_friends.json

data/requests/：好友申请，如 from_alice_to_bob.json

所有数据都存在本机，重启不丢（除非你删文件）。



### 三、配置相关信息

完成框架搭建后，写好python后端和html前端。

 启动服务 & 配置 Nginx 代理：

1. 启动 Flask（后台运行）

\# 激活虚拟环境（如果退出了）

source ~/webchat/venv/bin/activate

\# 启动（用 nohup 后台运行）

nohup python3 app.py > webchat.log 2>&1 &

Flask 默认监听 http://0.0.0.0:5000

 

2. 配置 Nginx 代理（假设域名是 example.com，或直接用 IP）

编辑 Nginx 站点配置（例如 /etc/nginx/sites-available/default）：

sudo nano /etc/nginx/sites-available/default

在 server { ... } 块中，替换或添加以下内容：

location / {

​    proxy_pass http://127.0.0.1:5000;  # 注意结尾的斜杠！

​    proxy_set_header Host $host;

​    proxy_set_header X-Real-IP $remote_addr;

​    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

​    proxy_set_header X-Forwarded-Proto $scheme;

}

注意：
我的服务器之前nginx已经配置了一个个人博客，所以需要单独配置两个不同的服务通道，可以参考我的配置文件：[本目录下实例1](实例1.docx)（本地VMware测试机配置），[实例2](实例2.docx)（云服务器公网配置）。



3. 重载 Nginx

sudo nginx -t && sudo systemctl reload nginx

 

4.访问聊天系统！

打开浏览器，访问服务器 IP 或域名：http://你的服务器IP



### 建议

重启服务器后，本服务会自动关闭，推荐可以使用systemd服务，设置开机、崩溃自动重启

#### 步骤 1：创建 systemd 服务文件

sudo nano /etc/systemd/system/webchat.service

 

粘贴以下内容（已根据你的路径和 venv 完全适配）：

[Unit]

Description=WebChat Flask Application

After=network.target

 

[Service]

Type=simple

User=root

WorkingDirectory=/root/webchat

ExecStart=/root/webchat/venv/bin/python3 app.py

Restart=always

RestartSec=10

StandardOutput=journal

StandardError=journal

SyslogIdentifier=webchat

 

[Install]

WantedBy=multi-user.target

 

说明：

直接使用虚拟环境中的 Python：/root/webchat/venv/bin/python3

不需要 source activate，因为 venv/bin/python3 已经绑定了虚拟环境

日志会自动进入 journalctl，也可以保留你原来的 webchat.log（见下方可选）



#### 步骤 2：启用并启动服务

\# 重载 systemd 配置

sudo systemctl daemon-reload

\# 停止你之前用 nohup 启动的进程（避免冲突）

pkill -f "python3 app.py"

\# 启动新服务

sudo systemctl start webchat

\# 设置开机自启

sudo systemctl enable webchat

\# 查看状态

sudo systemctl status webchat

查看日志（推荐方式）

\# 实时查看日志

journalctl -u webchat -f

\# 查看最近 50 行

journalctl -u webchat -n 50

 

原来的 webchat.log 不再需要了（除非特别想保留文件日志）。如果仍想写入文件日志，可以改用下面的 ExecStart（不推荐，优先用 journal）：

ExecStart=/bin/bash -c '/root/webchat/venv/bin/python3 app.py >> /root/webchat/webchat.log 2>&1'

 

但一般 journalctl 更规范、支持日志轮转、不会占满磁盘。

验证是否成功

重启服务器：

sudo reboot

重新 SSH 登录后，运行：

systemctl status webchat

应该看到 active (running)

访问 https://www.stuvip.top/chat/login 确认聊天室正常

 

（可选）清理旧的 nohup 进程和日志

\# 删除旧日志（如果不再需要）

rm /root/webchat/webchat.log

\# 确保没有残留进程

ps aux | grep "app.py"

 

##### 总结

用户 root

项目路径 /root/webchat/

虚拟环境 /root/webchat/venv/

启动命令 /root/webchat/venv/bin/python3 app.py

服务名 webchat.service

开机自启 ✅ 已启用

崩溃重启 ✅ 自动恢复





## 效果如下



### 移动端

<img src=".\V1\picture\移动端-联系人.jpg" alt="移动端-联系人" style="zoom: 25%;" /><img src=".\V1\picture\移动端-发现.jpg" alt="移动端-发现" style="zoom:25%;" />



### PC端

这个发现界面是V2版本的，当前版本没有“退出登录”和“注销账号”功能

<img src=".\V1\picture\PC端-发现V2版本.png" alt="PC端-发现V2版本" style="zoom:25%;" />





<img src=".\V1\picture\PC端-联系人.png" alt="PC端-联系人" style="zoom:25%;" />



# V2

## 优化

1.注册界面优化，注册成功后300ms自动跳转到登陆界面登录；



## 修复

1.修复移动端添加好友不稳定，无法添加情况。



## 新增

1.注册时新增校验，相同用户名不可重复注册；

2.发现界面新增“退出登录”、“注销账户”功能，修复诸如微信、QQ的bug：

A、B用户互为好友，A用户注销账户时，B用户联系人列表直接消失A用户信息。





# V2.1

## 新增

新增聊天记录中，时间戳，记录每条信息发送时间。





# V2.2

## 优化

### 优化时间问题，后台无法正常显示时间：

确保前后端都是字符串，而非时间戳。



只修改 save_message 函数中的时间生成方式：

current_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
同时，为了保持分钟级精度，用 %H:%M，不带秒。



找到 `save_message` 函数，替换为以下内容：

```
def save_message(sender, receiver, content):
    key = '_'.join(sorted([sender, receiver]))
    path = f'{DATA_DIR}/messages/{key}.json'
    
    # ✅ 使用人类可读的时间字符串，格式： "2025-10-17 12:11"
    current_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    
    msg = {
        "sender": sender,
        "text": content,
        "time": current_time  # 字符串格式，人类可读
    }
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            msgs = json.load(f)
    else:
        msgs = []
    msgs.append(msg)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)
```





因为现在 `msg['time']` 是字符串（如 `"2025-10-17 12:11"`），而 `last_read_time` 在 `mark_chat_as_read` 中仍然保存的是 **时间戳**（float），这会导致类型不匹配，无法比较！

所以我们必须**统一格式**。既然你坚持用字符串，那我们也把 `last_read` 存成**相同格式的字符串**。

#### 步骤 1：修改 `mark_chat_as_read` 函数

```
def mark_chat_as_read(user1, user2):
    key = '_'.join(sorted([user1, user2]))
    path = f'{DATA_DIR}/last_read/{key}.json'
    current_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"last_read_time": current_time}, f, ensure_ascii=False, indent=2)
```

#### 步骤 2：修改 `get_last_read_time` 函数

让它返回字符串（或空字符串），而不是 0：

```
def get_last_read_time(user1, user2):
    key = '_'.join(sorted([user1, user2]))
    path = f'{DATA_DIR}/last_read/{key}.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
            return data.get("last_read_time", "")
    return ""
```

#### 步骤 3：修改 `unread_counts` 中的比较逻辑

字符串时间不能直接比较大小！但幸运的是，`"2025-10-17 12:11"` 这种格式是 **字典序可比的**（ISO 格式），所以可以直接用 `>` 比较！

但要注意：如果 `last_read` 是空字符串（从未读过），则所有消息都算未读。

```
@app.route('/chat/api/unread_counts/<username>')
def unread_counts(username):
    if not user_exists(username):
        return jsonify({}), 404
    friends = get_friends(username)
    unread = {}
    for friend in friends:
        last_read = get_last_read_time(username, friend)  # 字符串 or ""
        messages = get_messages(username, friend)
        count = 0
        for msg in messages:
            msg_time = msg.get('time', "")
            # 如果从未读过（last_read 为空），或者消息时间晚于最后阅读时间
            if not last_read or (isinstance(msg_time, str) and msg_time > last_read):
                count += 1
        if count > 0:
            unread[friend] = count
    return jsonify(unread)
```



### 最终修改汇总

替换以下函数：

```
def save_message(sender, receiver, content):
    key = '_'.join(sorted([sender, receiver]))
    path = f'{DATA_DIR}/messages/{key}.json'
    current_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    msg = {
        "sender": sender,
        "text": content,
        "time": current_time
    }
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            msgs = json.load(f)
    else:
        msgs = []
    msgs.append(msg)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)


def mark_chat_as_read(user1, user2):
    key = '_'.join(sorted([user1, user2]))
    path = f'{DATA_DIR}/last_read/{key}.json'
    current_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"last_read_time": current_time}, f, ensure_ascii=False, indent=2)


def get_last_read_time(user1, user2):
    key = '_'.join(sorted([user1, user2]))
    path = f'{DATA_DIR}/last_read/{key}.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
            return data.get("last_read_time", "")
    return ""


@app.route('/chat/api/unread_counts/<username>')
def unread_counts(username):
    if not user_exists(username):
        return jsonify({}), 404
    friends = get_friends(username)
    unread = {}
    for friend in friends:
        last_read = get_last_read_time(username, friend)
        messages = get_messages(username, friend)
        count = 0
        for msg in messages:
            msg_time = msg.get('time', "")
            if not last_read or (isinstance(msg_time, str) and msg_time > last_read):
                count += 1
        if count > 0:
            unread[friend] = count
    return jsonify(unread)
```

------

### 📌 注意事项

- 所有新消息的时间格式为：`"2025-10-17 12:11"`（无秒）
- 旧数据如果是时间戳格式，**不会自动转换**。如果已有数据，建议清空 `data/messages` 和 `data/last_read` 测试，或写个迁移脚本。
- 前端如果之前用 `msg.time > lastRead` 做比较，现在依然可以（因为字符串是 ISO 格式，字典序 = 时间序）。
- 如果前端需要显示“刚刚”、“5分钟前”等，可以用 JS 把字符串转成 Date 对象处理。





## 效果如下

前端：

<img src=".\V2.2\picture\前端.png" alt="前端" style="zoom:25%;" />

后端：

<img src=".\V2.2\picture\后端.png" alt="后端" style="zoom:25%;" />







# V3

## 新增

1.邮箱注册验证；

2.邮箱找回密码机制。



### 打开QQ邮箱API方法

1.打开QQ邮箱➡登录➡设置➡账号与安全➡安全设置➡POP3/IMAP/SMTP/Exchange/CardDAV 服务➡生成授权码。



本次新增功能注意点：（在app.py）

\# === 邮箱配置（从 .env 读取，无默认值！）===

QQ_EMAIL = os.getenv('QQ_EMAIL')

QQ_MAIL_PASSWORD = os.getenv('QQ_MAIL_PASSWORD')



### 使用前，需要先下载python-dotenv：

进入当前环境：

cd ~/webchat

source venv/bin/activate

pip install python-dotenv



配置时，为了保障邮箱信息和授权码安全，特意配置了.env保存机制，在本app.py同级目录下，有一个.env文件，里面已经设置好
QQ_EMAIL=真实邮箱号@qq.com
QQ_MAIL_PASSWORD=真实授权码


将这个信息填好后，即可正常使用。
