# 优化

## 优化时间问题，后台无法正常显示时间：

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

![前端](.\picture\前端.png)

后端：

![后端](.\picture\后端.png)
