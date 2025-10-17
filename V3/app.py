import os
import json
import time
import uuid
import shutil
import random
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, send_from_directory, redirect
from dotenv import load_dotenv  # ← 新增

# 加载 .env 文件（仅本地开发时生效）
load_dotenv()

app = Flask(__name__, static_folder='static')

# === 邮箱配置（从 .env 读取，无默认值！）===
QQ_EMAIL = os.getenv('QQ_EMAIL')
QQ_MAIL_PASSWORD = os.getenv('QQ_MAIL_PASSWORD')

if not QQ_EMAIL or not QQ_MAIL_PASSWORD:
    raise EnvironmentError("❌ 请在 .env 文件中设置 QQ_EMAIL 和 QQ_MAIL_PASSWORD")

# 临时存储验证码（生产环境建议用 Redis）
VERIFICATION_CODES = {}  # {email: {'code': '123456', 'expires': timestamp, 'username': 'xxx'}}

DATA_DIR = 'data'
os.makedirs(f'{DATA_DIR}/users', exist_ok=True)
os.makedirs(f'{DATA_DIR}/messages', exist_ok=True)
os.makedirs(f'{DATA_DIR}/friends', exist_ok=True)
os.makedirs(f'{DATA_DIR}/requests', exist_ok=True)
os.makedirs(f'{DATA_DIR}/uploads', exist_ok=True)
os.makedirs(f'{DATA_DIR}/last_read', exist_ok=True)

# ----------------- 工具函数 -----------------
def user_exists(username):
    return os.path.exists(f'{DATA_DIR}/users/{username}.json')

def save_user(username, password, email=""):
    with open(f'{DATA_DIR}/users/{username}.json', 'w', encoding='utf-8') as f:
        json.dump({"username": username, "password": password, "email": email}, f, ensure_ascii=False, indent=2)

def get_user(username):
    if user_exists(username):
        with open(f'{DATA_DIR}/users/{username}.json', encoding='utf-8') as f:
            return json.load(f)
    return None

def send_verification_email(email, code):
    """发送验证码邮件"""
    try:
        msg = MIMEText(f'您的验证码是：{code}\n有效期5分钟。', 'plain', 'utf-8')
        msg['From'] = QQ_EMAIL
        msg['To'] = email
        msg['Subject'] = "【WebChat】注册/找回密码验证码"

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(QQ_EMAIL, QQ_MAIL_PASSWORD)
        server.sendmail(QQ_EMAIL, [email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("邮件发送失败:", str(e))
        return False

# ----------------- 新增 API：发送验证码 -----------------
@app.route('/chat/api/send_verification_code', methods=['POST'])
def send_verification_code():
    data = request.json
    email = data.get('email')
    username = data.get('username')

    if not email or '@' not in email:
        return jsonify({"error": "请输入有效邮箱"}), 400

    if username:
        if user_exists(username):
            return jsonify({"error": "用户名已存在"}), 409
        for file in os.listdir(f'{DATA_DIR}/users'):
            if file.endswith('.json'):
                with open(f'{DATA_DIR}/users/{file}', encoding='utf-8') as f:
                    user_data = json.load(f)
                    if user_data.get('email') == email:
                        return jsonify({"error": "该邮箱已被注册"}), 409

    code = str(random.randint(100000, 999999))
    expires = time.time() + 300

    VERIFICATION_CODES[email] = {
        'code': code,
        'expires': expires,
        'username': username
    }

    if send_verification_email(email, code):
        return jsonify({"ok": True})
    else:
        return jsonify({"error": "邮件发送失败，请检查邮箱或稍后重试"}), 500

# ----------------- 新增 API：验证验证码并注册 -----------------
@app.route('/chat/api/verify_and_register', methods=['POST'])
def verify_and_register():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    username = data.get('username')
    password = data.get('password')

    if not all([email, code, username, password]):
        return jsonify({"error": "参数缺失"}), 400

    record = VERIFICATION_CODES.get(email)
    if not record:
        return jsonify({"error": "验证码已过期或未发送"}), 400
    if time.time() > record['expires']:
        VERIFICATION_CODES.pop(email, None)
        return jsonify({"error": "验证码已过期"}), 400
    if record['code'] != code:
        return jsonify({"error": "验证码错误"}), 400
    if record.get('username') != username:
        return jsonify({"error": "用户名不匹配"}), 400

    save_user(username, password, email)
    VERIFICATION_CODES.pop(email, None)
    return jsonify({"ok": True})

# ----------------- 找回密码：发验证码 -----------------
@app.route('/chat/api/request_password_reset', methods=['POST'])
def request_password_reset():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({"error": "请输入用户名"}), 400

    user = get_user(username)
    if not user or not user.get('email'):
        return jsonify({"error": "该用户不存在或未绑定邮箱"}), 404

    email = user['email']
    code = str(random.randint(100000, 999999))
    expires = time.time() + 300

    VERIFICATION_CODES[email] = {
        'code': code,
        'expires': expires,
        'username': username
    }

    if send_verification_email(email, code):
        return jsonify({"ok": True})
    else:
        return jsonify({"error": "邮件发送失败"}), 500

# ----------------- 重置密码 -----------------
@app.route('/chat/api/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    new_password = data.get('new_password')

    if not all([email, code, new_password]):
        return jsonify({"error": "参数缺失"}), 400

    record = VERIFICATION_CODES.get(email)
    if not record:
        return jsonify({"error": "验证码无效"}), 400
    if time.time() > record['expires']:
        VERIFICATION_CODES.pop(email, None)
        return jsonify({"error": "验证码已过期"}), 400
    if record['code'] != code:
        return jsonify({"error": "验证码错误"}), 400

    username = record['username']
    user = get_user(username)
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    user['password'] = new_password
    with open(f'{DATA_DIR}/users/{username}.json', 'w', encoding='utf-8') as f:
        json.dump(user, f, ensure_ascii=False, indent=2)

    VERIFICATION_CODES.pop(email, None)
    return jsonify({"ok": True})

# ----------------- 其他 API（保持不变）-----------------
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

@app.route('/chat/api/mark_read', methods=['POST'])
def mark_read():
    data = request.json
    user = data.get('user')
    friend = data.get('friend')
    if not user or not friend:
        return jsonify({"ok": False}), 400
    mark_chat_as_read(user, friend)
    return jsonify({"ok": True})

@app.route('/chat/api/unread_friend_requests/<username>')
def unread_friend_requests(username):
    reqs = get_friend_requests(username)
    return jsonify({"count": len(reqs)})

@app.route('/chat/api/messages/<user1>/<user2>')
def get_chat(user1, user2):
    mark_chat_as_read(user1, user2)
    return jsonify(get_messages(user1, user2))

@app.route('/chat/api/check_user_email', methods=['POST'])
def check_user_email():
    data = request.json
    username = data.get('username')
    user = get_user(username)
    if user and user.get('email'):
        return jsonify({"email": user['email']})
    return jsonify({"error": "用户不存在或未绑定邮箱"}), 404

@app.route('/chat/api/login', methods=['POST'])
def login():
    data = request.json
    user = get_user(data.get('username'))
    if user and user['password'] == data.get('password'):
        return jsonify({"ok": True, "username": user['username']})
    return jsonify({"error": "用户名或密码错误"}), 401

@app.route('/chat/api/friends/<username>')
def friends_list(username):
    return jsonify(get_friends(username))

@app.route('/chat/api/add_friend_request', methods=['POST'])
def add_friend_request():
    data = request.json
    sender = data['sender']
    target = data['target']
    if not user_exists(target):
        return jsonify({"error": "用户不存在"}), 404
    save_friend_request(sender, target)
    return jsonify({"ok": True})

@app.route('/chat/api/friend_requests/<username>')
def friend_requests(username):
    return jsonify(get_friend_requests(username))

@app.route('/chat/api/accept_friend', methods=['POST'])
def accept_friend():
    data = request.json
    user = data['user']
    friend = data['friend']
    add_friend(user, friend)
    add_friend(friend, user)
    remove_friend_request(friend, user)
    return jsonify({"ok": True})

@app.route('/chat/api/reject_friend', methods=['POST'])
def reject_friend():
    data = request.json
    user = data['user']
    friend = data['friend']
    remove_friend_request(friend, user)
    return jsonify({"ok": True})

@app.route('/chat/api/send_file', methods=['POST'])
def send_file():
    if 'file' not in request.files:
        return jsonify({"error": "未选择文件"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "文件名为空"}), 400

    allowed_ext = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi', '.webm'}
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_ext:
        return jsonify({"error": "不支持的文件类型"}), 400

    filename = str(uuid.uuid4()) + ext.lower()
    filepath = os.path.join(DATA_DIR, 'uploads', filename)
    file.save(filepath)

    return jsonify({
        "ok": True,
        "url": f"/chat/uploads/{filename}"
    })

@app.route('/chat/uploads/<filename>')
def uploaded_file(filename):
    if '..' in filename or filename.startswith('/'):
        return "非法文件名", 400
    return send_from_directory(os.path.join(DATA_DIR, 'uploads'), filename)

@app.route('/chat/api/send_message', methods=['POST'])
def send_message():
    data = request.json
    sender = data.get('from')
    receiver = data.get('to')
    content = data.get('text')
    if not sender or not receiver or content is None:
        return jsonify({"error": "缺少必要字段"}), 400
    save_message(sender, receiver, content)
    return jsonify({"ok": True})

@app.route('/chat/api/check_username_exists/<username>')
def check_username_exists(username):
    exists = user_exists(username)
    return jsonify({"exists": exists})

@app.route('/chat/api/change_password', methods=['POST'])
def change_password():
    data = request.json
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not username or not old_password or not new_password:
        return jsonify({"ok": False, "error": "参数缺失"}), 400
    success, msg = change_user_password(username, old_password, new_password)
    if success:
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False, "error": msg})

@app.route('/chat/api/change_username', methods=['POST'])
def change_username():
    data = request.json
    old_username = data.get('old_username')
    new_username = data.get('new_username')
    if not old_username or not new_username:
        return jsonify({"ok": False, "error": "参数缺失"}), 400
    success, msg = change_user_username(old_username, new_username)
    if success:
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False, "error": msg})

@app.route('/chat/api/delete_account', methods=['POST'])
def delete_account():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = get_user(username)
    if not user:
        return jsonify({"ok": False, "error": "用户不存在"}), 404
    if user['password'] != password:
        return jsonify({"ok": False, "error": "密码错误"}), 401

    delete_user_completely(username)
    return jsonify({"ok": True})

# ----------------- 前端页面路由 -----------------
@app.route('/chat/')
def index():
    return redirect('/chat/login', code=302)

@app.route('/chat/login')
def login_page():
    return send_from_directory('static', 'login.html')

@app.route('/chat/register')
def register_page():
    return send_from_directory('static', 'register.html')

@app.route('/chat/contacts')
def contacts_page():
    return send_from_directory('static', 'contacts.html')

@app.route('/chat/discover')
def discover_page():
    return send_from_directory('static', 'discover.html')

@app.route('/chat/chat')
def chat_page():
    friend = request.args.get('with')
    if not friend:
        return redirect('/chat/contacts', code=302)
    return send_from_directory('static', 'chat.html')

@app.route('/chat/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/')
def root_redirect():
    return redirect('/chat/login', code=302)

# ----------------- 辅助函数 -----------------
def get_friends(username):
    path = f'{DATA_DIR}/friends/{username}.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return []

def get_last_read_time(user, friend):
    path = f'{DATA_DIR}/last_read/{user}_{friend}.txt'
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read().strip()
    return None

def mark_chat_as_read(user, friend):
    from datetime import datetime
    now = datetime.utcnow().isoformat() + 'Z'
    with open(f'{DATA_DIR}/last_read/{user}_{friend}.txt', 'w') as f:
        f.write(now)
    with open(f'{DATA_DIR}/last_read/{friend}_{user}.txt', 'w') as f:
        f.write(now)

def get_messages(user1, user2):
    path = f'{DATA_DIR}/messages/{user1}_{user2}.json'
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def save_message(sender, receiver, content):
    from datetime import datetime
    msg = {
        "from": sender,
        "text": content,
        "time": datetime.utcnow().isoformat() + 'Z'
    }
    for pair in [(sender, receiver), (receiver, sender)]:
        path = f'{DATA_DIR}/messages/{pair[0]}_{pair[1]}.json'
        msgs = []
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                msgs = json.load(f)
        msgs.append(msg)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(msgs, f, ensure_ascii=False, indent=2)

def save_friend_request(sender, target):
    path = f'{DATA_DIR}/requests/{target}.json'
    reqs = []
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            reqs = json.load(f)
    if sender not in reqs:
        reqs.append(sender)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(reqs, f, ensure_ascii=False, indent=2)

def get_friend_requests(username):
    path = f'{DATA_DIR}/requests/{username}.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return []

def add_friend(user, friend):
    friends = get_friends(user)
    if friend not in friends:
        friends.append(friend)
        with open(f'{DATA_DIR}/friends/{user}.json', 'w', encoding='utf-8') as f:
            json.dump(friends, f, ensure_ascii=False, indent=2)

def remove_friend_request(sender, target):
    path = f'{DATA_DIR}/requests/{target}.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            reqs = json.load(f)
        if sender in reqs:
            reqs.remove(sender)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(reqs, f, ensure_ascii=False, indent=2)

def change_user_password(username, old_password, new_password):
    user = get_user(username)
    if not user:
        return False, "用户不存在"
    if user['password'] != old_password:
        return False, "原密码错误"
    user['password'] = new_password
    save_user(username, new_password, user.get('email', ''))
    return True, "修改成功"

def change_user_username(old_username, new_username):
    if user_exists(new_username):
        return False, "新用户名已存在"
    user = get_user(old_username)
    if not user:
        return False, "原用户不存在"
    os.remove(f'{DATA_DIR}/users/{old_username}.json')
    save_user(new_username, user['password'], user.get('email', ''))
    return True, "修改成功"

def delete_user_completely(username):
    if os.path.exists(f'{DATA_DIR}/users/{username}.json'):
        os.remove(f'{DATA_DIR}/users/{username}.json')
    if os.path.exists(f'{DATA_DIR}/friends/{username}.json'):
        os.remove(f'{DATA_DIR}/friends/{username}.json')
    if os.path.exists(f'{DATA_DIR}/requests/{username}.json'):
        os.remove(f'{DATA_DIR}/requests/{username}.json')
    for f in os.listdir(f'{DATA_DIR}/last_read'):
        if f.startswith(username + '_') or f.endswith('_' + username + '.txt'):
            os.remove(os.path.join(f'{DATA_DIR}/last_read', f))
    for f in os.listdir(f'{DATA_DIR}/messages'):
        if f.startswith(username + '_') or f.endswith('_' + username + '.json'):
            os.remove(os.path.join(f'{DATA_DIR}/messages', f))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)