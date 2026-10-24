# -------- 导入库 --------

from openai import OpenAI
import json
import os
import hashlib
import concurrent.futures
import urllib.request
import urllib.error

# ------ 颜色定义 ------
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"

# Windows 支持
if os.name == "nt":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

# ------ 初始化客户端 ------

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_URL  = os.environ.get('OPENAI_BASE_URL', 'https://api.deepseek.com')

USERS_FILE = os.path.join(_BASE_DIR, "users.json")

# ------ 网络检测 ------

def check_internet():
    """检测网络连接"""
    test_urls = [
        "https://api.deepseek.com",
        "https://www.baidu.com",
        "https://www.google.com",
        "https://cloudflare.com",
    ]
    for url in test_urls:
        try:
            req = urllib.request.Request(url, method='HEAD')
            urllib.request.urlopen(req, timeout=3)
            return True
        except:
            continue
    return False

def check_api_status(api_key):
    """检测 API 是否可用"""
    if not api_key:
        return False, "未设置 API Key"
    try:
        client = OpenAI(api_key=api_key, base_url=_BASE_URL)
        # 简单测试调用，带超时
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
            timeout=10
        )
        return True, "OK"
    except Exception as e:
        err_msg = str(e)
        # 忽略超时错误
        if "timeout" in err_msg.lower():
            return True, "可能可用（超时）"
        return False, err_msg

# ------ 用户系统 ------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def register(username, password):
    users = load_users()
    if not username:
        return False, "用户名不能为空"
    if len(username) < 3:
        return False, "用户名至少3个字符"
    if username in users:
        return False, f"{Colors.RED}用户名已存在{Colors.RESET}"
    if len(password) < 4:
        return False, "密码至少4个字符"
    users[username] = {
        "password": hash_password(password),
        "api_key": "",
        "memories": []
    }
    save_users(users)
    return True, f"{Colors.GREEN}注册成功{Colors.RESET}"

def login(username, password):
    users = load_users()
    if not username:
        return None, "用户名不能为空"
    if username not in users:
        return None, f"{Colors.RED}用户不存在{Colors.RESET}"
    if users[username]["password"] != hash_password(password):
        return None, f"{Colors.RED}密码错误{Colors.RESET}"
    return users[username], f"{Colors.GREEN}登录成功{Colors.RESET}"

def init_api(username):
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

def get_memory_file(username):
    return os.path.join(_BASE_DIR, f"memories_{username}.json")

def save_memories(username, turn):
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
    
    print(f"{Colors.CYAN}Snowball 正在思考...{Colors.RESET}")
    assistant_reply, timed_out = _submit_with_timeout(messages, client)
    
    if timed_out:
        print(f"{Colors.RED}连接超时（超过90秒），请重试。{Colors.RESET}")
        return None
    if assistant_reply is None:
        print(f"{Colors.RED}API返回空响应，请重试。{Colors.RESET}")
        return None
    
    return assistant_reply

# ------ 界面函数 ------

def print_header(title):
    width = 50
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * width}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title:^{width}}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * width}{Colors.RESET}")
    print()

def print_menu(options, title="菜单"):
    print(f"{Colors.YELLOW}{Colors.BOLD}{title}{Colors.RESET}")
    for i, opt in enumerate(options, 1):
        print(f"  {Colors.CYAN}{i}.{Colors.RESET} {opt}")
    print()

def print_error(msg):
    print(f"{Colors.RED}错误: {msg}{Colors.RESET}\n")

def print_success(msg):
    print(f"{Colors.GREEN}{msg}{Colors.RESET}\n")

def print_info(msg):
    print(f"{Colors.BLUE}信息: {msg}{Colors.RESET}\n")

def print_divider():
    print(f"{Colors.BLUE}{'-' * 40}{Colors.RESET}")

def format_output(text, width=60):
    """格式化输出，自动换行"""
    if not text:
        return
    paragraphs = text.split("\n")
    for para in paragraphs:
        if not para.strip():
            continue
        words = para.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 > width:
                if line:
                    print(f"  {line}")
                line = word
            else:
                line = (line + " " + word) if line else word
        if line:
            print(f"  {line}")

# ------ 主循环 ------

def main():
    print_header(f"{Colors.MAGENTA}霜匠 SnowBot{Colors.RESET}")
    
    # 检测网络
    print(f"{Colors.CYAN}检测网络连接...{Colors.RESET}")
    if check_internet():
        print_success("网络连接正常")
    else:
        print_error("无法连接到互联网")
    
    print_divider()
    
    while True:
        print_menu(["|登录|Login|", "|注册|Register|", "|状态|Status|", "|退出|Quit|"], "请选择/Please choose")
        choice = input(f"{Colors.CYAN}>> {Colors.RESET}").strip()
        
        if choice == "1":
            do_login()
        elif choice == "2":
            do_register()
        elif choice == "3":
            do_status()
        elif choice == "4":
            print(f"{Colors.GREEN}再见喵~{Colors.RESET}")
            break
        else:
            print_error("无效选择")

def do_status():
    """显示状态信息"""
    print_header("系统状态")
    
    # 网络状态
    if check_internet():
        print_success("网络: 已连接")
    else:
        print_error("网络: 未连接")
    
    # 用户数量
    users = load_users()
    print_info(f"注册用户: {len(users)} 人")
    
    # 显示所有用户
    if users:
        print(f"{Colors.CYAN}用户列表:{Colors.RESET}")
        for username in users:
            api_key = users[username].get("api_key", "")
            api_status = "✓" if api_key else "✗"
            print(f"  - {username} [API: {api_status}]")
    print()

def do_login():
    print_header("登录")
    username = input(f"{Colors.CYAN}用户名: {Colors.RESET}").strip()
    password = input(f"{Colors.CYAN}密码: {Colors.RESET}").strip()
    
    user_data, msg = login(username, password)
    if user_data is None:
        print_error(msg)
        return
    
    # 检查 API Key
    client, user_info = init_api(username)
    if client is None:
        print(f"{Colors.YELLOW}未设置 API Key{Colors.RESET}")
        api_key = input(f"{Colors.CYAN}请输入 API Key: {Colors.RESET}").strip()
        if api_key:
            # 测试 API
            print(f"{Colors.CYAN}测试 API 连接...{Colors.RESET}")
            ok, result = check_api_status(api_key)
            if ok:
                users = load_users()
                users[username]["api_key"] = api_key
                save_users(users)
                client = OpenAI(api_key=api_key, base_url=_BASE_URL)
                print_success("API 连接成功")
            else:
                print_error(f"API 连接失败: {result}")
                return
        else:
            print_error("需要 API Key 才能使用")
            return
    
    print_success(f"欢迎回来，{username}！")
    chat_loop(username, client)

def do_register():
    print_header("注册")
    username = input(f"{Colors.CYAN}用户名: {Colors.RESET}").strip()
    password = input(f"{Colors.CYAN}密码: {Colors.RESET}").strip()
    confirm = input(f"{Colors.CYAN}确认密码: {Colors.RESET}").strip()
    
    if password != confirm:
        print_error("密码不匹配")
        return
    
    success, msg = register(username, password)
    if not success:
        print_error(msg)
        return
    
    print_success(msg)
    api_key = input(f"{Colors.CYAN}API Key: {Colors.RESET}").strip()
    if api_key:
        # 测试 API
        print(f"{Colors.CYAN}测试 API 连接...{Colors.RESET}")
        ok, result = check_api_status(api_key)
        if ok:
            users = load_users()
            users[username]["api_key"] = api_key
            save_users(users)
            print_success("API Key 已保存")
        else:
            print_error(f"API 连接失败: {result}")

def chat_loop(username, client):
    memories = load_memories(username, limit=None)  # 加载全部历史
    print_header(f"聊天 - {username}")
    print(f"--- 聊天记录 ({len(memories)} 条) ---")
    # 显示全部历史记录
    for i, (u, a) in enumerate(memories):
        print(f"{Colors.CYAN}[{i+1}] User:{Colors.RESET}")
        for line in u.split("\n"):
            print(f"  {line}")
        print(f"{Colors.MAGENTA}Snowball:{Colors.RESET}")
        for line in a.split("\n"):
            print(f"  {line}")
    print_divider()
    print(f"输入 {Colors.YELLOW}logout{Colors.RESET} 退出登录")
    print_divider()
    
    while True:
        user_msg = input(f"{Colors.GREEN}User>{Colors.RESET} ").strip()
        
        if not user_msg:
            print(f"{Colors.YELLOW}请输入内容{Colors.RESET}")
            continue
        
        if user_msg.lower() in ["logout", "exit", "quit"]:
            print(f"{Colors.CYAN}已退出登录{Colors.RESET}")
            print_divider()
            return
        
        assistant_reply = chat(user_msg, memories, client)
        
        if assistant_reply:
            print(f"{Colors.MAGENTA}Snowball:{Colors.RESET}")
            format_output(assistant_reply)
            print()
            
            save_memories(username, [user_msg, assistant_reply])
            memories.append([user_msg, assistant_reply])
            if len(memories) > 5:
                memories = memories[-5:]


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}再见喵~{Colors.RESET}")
    except EOFError:
        print(f"\n{Colors.CYAN}再见喵~{Colors.RESET}")