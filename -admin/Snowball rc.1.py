# -------- 导入库 --------

from openai import OpenAI
import json
import os
import hashlib
import concurrent.futures

# ------ 初始化客户端 ------

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_URL  = os.environ.get('OPENAI_BASE_URL', 'https://api.deepseek.com')

# 用户数据文件
USERS_FILE = os.path.join(_BASE_DIR, "users.json")

# ------ 用户系统 ------

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """加载用户数据"""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_users(users):
    """保存用户数据"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def register(username, password):
    """注册用户"""
    users = load_users()
    if username in users:
        return False, "用户名已存在"
    users[username] = {
        "password": hash_password(password),
        "memories": []
    }
    save_users(users)
    return True, "注册成功"

def login(username, password):
    """登录验证"""
    users = load_users()
    if username not in users:
        return None, "用户不存在"
    if users[username]["password"] != hash_password(password):
        return None, "密码错误"
    return users[username], "登录成功"

# ------ 初始化 API ------

def init_api(username):
    """为用户初始化 API 客户端"""
    users = load_users()
    user_data = users.get(username)
    if not user_data:
        return None, None
    
    api_key = user_data.get("api_key")
    if not api_key:
        return None, None
    
    client = OpenAI(api_key=api_key, base_url=_BASE_URL)
    return client, user_data

# ------ 系统人设 ------

system_prompt = (
    "你是一个高效直接的猫娘机器人，"
    "你说话总在句尾加上'喵'，"
    "你的名字叫Snowball，"
    "你会叫我Master。"
)

# ------ 记忆模块------
# 每个用户独立的记忆文件
def get_memory_file(username):
    return os.path.join(_BASE_DIR, f"memories_{username}.json")

def save_memories(username, turn):
    """追加单轮对话到文件"""
    memory_file = get_memory_file(username)
    if os.path.exists(memory_file):
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                memories = json.load(f)
        except json.JSONDecodeError:
            memories = []
    else:
        memories = []
    
    memories.append({"user": turn[0], "assistant": turn[1]})
    
    with open(memory_file, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

def load_memories(username, limit=None):
    memory_file = get_memory_file(username)
    if not os.path.exists(memory_file):
        return []
    
    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_memories = [[item["user"], item["assistant"]] for item in data]
            
            if limit and isinstance(limit, int) and limit > 0:
                return all_memories[-limit:]
            return all_memories
    except (json.JSONDecodeError, KeyError):
        return []

# ------ API 调用 ------

API_TIMEOUT = 90

def _call_api(messages, api_client):
    response = api_client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
    return response.choices[0].message.content

def _submit_with_timeout(messages, api_client):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_call_api, messages, api_client)
    try:
        reply = future.result(timeout=API_TIMEOUT)
        executor.shutdown(wait=False)
        return reply, False
    except concurrent.futures.TimeoutError:
        executor.shutdown(wait=False)
        return None, True
    except Exception as e:
        executor.shutdown(wait=False)
        return f"[连接超时] {e}", False

# ------ 对话函数 ------

def chat(user_msg, memories, client):
    messages = [{"role": "system", "content": system_prompt}]

    for h_user, h_assistant in memories:
        messages.append({"role": "user", "content": h_user})
        messages.append({"role": "assistant", "content": h_assistant})

    messages.append({"role": "user", "content": user_msg})

    assistant_reply, timed_out = _submit_with_timeout(messages, client)

    if timed_out:
        print("连接超时（超过90秒），请重试。")
        return None

    if assistant_reply is None:
        print("API返回空响应，请重试。")
        return None

    return assistant_reply

# ------ 主循环 ------

def main():
    print("=" * 50)
    print("霜匠 SnowBot")
    print("=" * 50)
    print()
    
    while True:
        print("1. 登录/login")
        print("2. 注册/register")
        print("3. 退出/quit")
        choice = input("请选择: ").strip()
        print()
        
        if choice == "1":
            # 登录
            username = input("用户名: ").strip()
            password = input("密码: ").strip()
            user_data, msg = login(username, password)
            if user_data is None:
                print(f"登录失败: {msg}\n")
                continue
            
            # 检查 API Key
            client, user_info = init_api(username)
            if client is None:
                print("错误: 未设置 API Key")
                # 让用户输入 API Key
                api_key = input("请输入 API Key: ").strip()
                if api_key:
                    users = load_users()
                    users[username]["api_key"] = api_key
                    save_users(users)
                    client = OpenAI(api_key=api_key, base_url=_BASE_URL)
                else:
                    print("需要 API Key 才能使用")
                    continue
            
            print(f"欢迎回来，{username}！\n")
            chat_loop(username, client)
            
        elif choice == "2":
            # 注册
            username = input("用户名: ").strip()
            password = input("密码: ").strip()
            confirm = input("确认密码: ").strip()
            
            if password != confirm:
                print("密码不匹配\n")
                continue
            
            success, msg = register(username, password)
            if success:
                print(f"注册成功！请设置 API Key（可选）")
                api_key = input("API Key (直接回车跳过): ").strip()
                if api_key:
                    users = load_users()
                    users[username]["api_key"] = api_key
                    save_users(users)
                print()
            else:
                print(f"注册失败: {msg}\n")
                
        elif choice == "3":
            print("再见喵~")
            break
        else:
            print("无效选择\n")

def chat_loop(username, client):
    memories = load_memories(username, limit=5)
    print(f"已加载 {len(memories)} 条记忆")
    print("输入 'logout' 退出登录")
    print()
    
    while True:
        try:
            user_msg = input("User: ").strip()
        except EOFError:
            break
        
        if not user_msg:
            print("请输入内容\n")
            continue
        
        if user_msg.lower() in ["logout", "exit", "quit"]:
            print("已退出登录\n")
            break
        
        assistant_reply = chat(user_msg, memories, client)
        
        if assistant_reply:
            print("Snowball:")
            paragraphs = assistant_reply.split("\n")
            for para in paragraphs:
                if para.strip():
                    words = para.split()
                    line = ""
                    for word in words:
                        if len(line) + len(word) + 1 > 60:
                            if line:
                                print(f"  {line}")
                            line = word
                        else:
                            if line:
                                line += " " + word
                            else:
                                line = word
                    if line:
                        print(f"  {line}")
            print()
            
            save_memories(username, [user_msg, assistant_reply])
            memories.append([user_msg, assistant_reply])
            if len(memories) > 5:
                memories = memories[-5:]


if __name__ == "__main__":
    main()