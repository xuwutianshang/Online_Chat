# 新增

1.邮箱注册验证；

2.邮箱找回密码机制。



### 打开QQ邮箱API方法

1.打开QQ邮箱➡登录➡设置➡账号与安全➡安全设置➡POP3/IMAP/SMTP/Exchange/CardDAV 服务➡生成授权码。



本次新增功能注意点：

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
