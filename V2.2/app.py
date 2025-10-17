import os
import json
import time
import uuid
import shutil
from flask import Flask, request, jsonify, send_from_directory, redirect

app = Flask(__name__, static_folder='static')

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

def save_user(username, password, phone=""):
    with open(f'{DATA_DIR}/users/{username}.json', 'w', encoding='utf-8') as f:
        json.dump({"username": username, "password": password, "phone": phone}, f, ensure_ascii=False, indent=2)

def get_user(username):
    if user_exists(username):
        with open(f'{DATA_DIR}/users/{username}.json', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_friends(username):
    path = f'{DATA_DIR}/friends/{username}_friends.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return []

def add_friend(username, friend):
    friends = get_friends(username)
    if friend not in friends:
        friends.append(friend)
        with open(f'{DATA_DIR}/friends/{username}_friends.json', 'w', encoding='utf-8') as f:
            json.dump(friends, f, ensure_ascii=False, indent=2)

def rename_friends_file(old_name, new_name):
    old_path = f'{DATA_DIR}/friends/{old_name}_friends.json'
    new_path = f'{DATA_DIR}/friends/{new_name}_friends.json'
    if os.path.exists(old_path):
        shutil.move(old_path, new_path)

def update_messages_for_username(old_name, new_name):
    messages_dir = f'{DATA_DIR}/messages'
    for filename in os.listdir(messages_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(messages_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    msgs = json.load(f)
                except:
                    continue
            changed = False
            for msg in msgs:
                if msg.get('sender') == old_name:
                    msg['sender'] = new_name
                    changed = True
            if changed:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(msgs, f, ensure_ascii=False, indent=2)

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

def get_messages(user1, user2):
    key = '_'.join(sorted([user1, user2]))
    path = f'{DATA_DIR}/messages/{key}.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return []

def get_last_read_time(user1, user2):
    key = '_'.join(sorted([user1, user2]))
    path = f'{DATA_DIR}/last_read/{key}.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
            return data.get("last_read_time", "")
    return ""

def mark_chat_as_read(user1, user2):
    key = '_'.join(sorted([user1, user2]))
    path = f'{DATA_DIR}/last_read/{key}.json'
    current_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"last_read_time": current_time}, f, ensure_ascii=False, indent=2)

def get_friend_requests(username):
    path = f'{DATA_DIR}/requests/to_{username}.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return []

def save_friend_request(sender, receiver):
    req = {"from": sender, "status": "pending"}
    path = f'{DATA_DIR}/requests/to_{receiver}.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            requests = json.load(f)
    else:
        requests = []
    requests.append(req)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)

def remove_friend_request(sender, receiver):
    path = f'{DATA_DIR}/requests/to_{receiver}.json'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            requests = json.load(f)
        requests = [r for r in requests if r["from"] != sender]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)

def delete_user_completely(username):
    user_file = f'{DATA_DIR}/users/{username}.json'
    if os.path.exists(user_file):
        os.remove(user_file)

    friends_file = f'{DATA_DIR}/friends/{username}_friends.json'
    if os.path.exists(friends_file):
        os.remove(friends_file)

    requests_file = f'{DATA_DIR}/requests/to_{username}.json'
    if os.path.exists(requests_file):
        os.remove(requests_file)

    messages_dir = f'{DATA_DIR}/messages'
    for filename in os.listdir(messages_dir):
        if filename.endswith('.json'):
            parts = filename[:-5].split('_')
            if username in parts:
                os.remove(os.path.join(messages_dir, filename))

    last_read_dir = f'{DATA_DIR}/last_read'
    for fname in os.listdir(last_read_dir):
        if fname.endswith('.json'):
            parts = fname[:-5].split('_')
            if username in parts:
                os.remove(os.path.join(last_read_dir, fname))

    friends_dir = f'{DATA_DIR}/friends'
    for fname in os.listdir(friends_dir):
        if fname.endswith('_friends.json'):
            friend_user = fname[:-13]
            if friend_user == username:
                continue
            friend_file = os.path.join(friends_dir, fname)
            try:
                with open(friend_file, 'r', encoding='utf-8') as f:
                    friends_list = json.load(f)
                if username in friends_list:
                    friends_list = [f for f in friends_list if f != username]
                    if friends_list:
                        with open(friend_file, 'w', encoding='utf-8') as f:
                            json.dump(friends_list, f, ensure_ascii=False, indent=2)
                    else:
                        os.remove(friend_file)
            except (json.JSONDecodeError, FileNotFoundError, OSError):
                continue

def change_user_password(username, old_password, new_password):
    user = get_user(username)
    if not user:
        return False, "用户不存在"
    if user['password'] != old_password:
        return False, "旧密码错误"
    user['password'] = new_password
    with open(f'{DATA_DIR}/users/{username}.json', 'w', encoding='utf-8') as f:
        json.dump(user, f, ensure_ascii=False, indent=2)
    return True, "密码修改成功"

def change_user_username(old_username, new_username):
    if not user_exists(old_username):
        return False, "原用户不存在"
    if user_exists(new_username):
        return False, "用户名已被占用"
    
    old_user_file = f'{DATA_DIR}/users/{old_username}.json'
    new_user_file = f'{DATA_DIR}/users/{new_username}.json'
    shutil.move(old_user_file, new_user_file)

    rename_friends_file(old_username, new_username)

    update_messages_for_username(old_username, new_username)

    last_read_dir = f'{DATA_DIR}/last_read'
    for fname in os.listdir(last_read_dir):
        if fname.endswith('.json'):
            parts = fname[:-5].split('_')
            if old_username in parts:
                new_parts = [new_username if p == old_username else p for p in parts]
                new_fname = '_'.join(new_parts) + '.json'
                os.rename(os.path.join(last_read_dir, fname), os.path.join(last_read_dir, new_fname))

    return True, "用户名修改成功"

# ----------------- 新增 API：未读消息 -----------------
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

# ----------------- 原有 API 路由（部分增强） -----------------
@app.route('/chat/api/messages/<user1>/<user2>')
def get_chat(user1, user2):
    mark_chat_as_read(user1, user2)
    return jsonify(get_messages(user1, user2))

# ----------------- API 路由 -----------------
@app.route('/chat/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone', '')
    if not username or not password:
        return jsonify({"error": "用户名和密码必填"}), 400
    if user_exists(username):
        return jsonify({"error": "用户已存在"}), 409
    save_user(username, password, phone)
    return jsonify({"ok": True})

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)