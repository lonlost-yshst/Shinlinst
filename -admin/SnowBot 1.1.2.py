# -------- 含霜 SnowBot --------
# AI 聊天机器人 - 1.1.2

from openai import OpenAI
import json
import os
import sys
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

# ------ 初始化 ------

if getattr(sys, "frozen", False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))

_BASE_URL = os.environ.get('OPENAI_BASE_URL', 'https://api.deepseek.com')

# 用户注册记录固定保存到当前 Windows 用户的 Roaming AppData\SnowBot
_ROAMING_DIR = os.environ.get(
    "APPDATA",
    os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
)
_DATA_DIR = os.path.join(_ROAMING_DIR, "SnowBot")
os.makedirs(_DATA_DIR, exist_ok=True)

# 兼容旧代码中对 _BASE_DIR 的引用；新版本不再把用户记录写到程序目录
_BASE_DIR = _DATA_DIR

USERS_FILE = os.path.join(_DATA_DIR, "users.json")
LANG_FILE = os.path.join(_DATA_DIR, "language.txt")

# ------ 语言系统 ------

CURRENT_LANG = "1"

LANG_STRINGS = {
    "1": {  # 简体汉语
        "menu": "请选择",
        "login": "登录",
        "register": "注册",
        "status": "状态",
        "language": "语言",
        "quit": "退出",
        "username": "用户名",
        "password": "密码",
        "confirm_password": "确认密码",
        "api_key": "API Key",
        "login_success": "登录成功",
        "register_success": "注册成功",
        "logout": "退出",
        "system_status": "系统状态",
        "network_ok": "网络: 已连接",
        "network_fail": "网络: 未连接",
        "users_count": "注册用户",
        "user_list": "用户列表",
        "choose_language": "选择语言",
        "selected": "已选择",
        "invalid_choice": "无效选择",
        "ai_name": "AI 名称",
        "persona": "人设描述",
        "call_you": "如何称呼你",
        "welcome_back": "欢迎回来",
        "goodbye": "再见",
        "thinking": "思考中...",
        "chat_history": "聊天记录",
        "user": "User",
        "input_content": "请输入内容",
        "exit_chat": "已退出登录",
        "set_your_ai": "设定你的 AI",
        "skip": "直接回车跳过",
        "test_api": "测试 API 连接",
        "api_success": "API 连接成功",
        "api_fail": "API 连接失败",
        "need_api": "需要 API Key 才能使用",
        "not_set_api": "未设置 API Key",
        "not_found_settings": "未找到设定，是否现在设置?",
        "setting": "设置?",
        "password_mismatch": "密码不匹配",
        "user_exists": "用户名已存在",
        "user_not_exist": "用户不存在",
        "wrong_password": "密码错误",
        "username_too_short": "用户名至少3个字符",
        "password_too_short": "密码至少4个字符",
        "empty_username": "用户名不能为空",
    },
    "2": {  # 繁体汉语
        "menu": "請選擇",
        "login": "登入",
        "register": "註冊",
        "status": "狀態",
        "language": "語言",
        "quit": "退出",
        "username": "用戶名",
        "password": "密碼",
        "confirm_password": "確認密碼",
        "api_key": "API Key",
        "login_success": "登入成功",
        "register_success": "註冊成功",
        "logout": "退出",
        "system_status": "系統狀態",
        "network_ok": "網絡: 已連接",
        "network_fail": "網絡: 未連接",
        "users_count": "註冊用戶",
        "user_list": "用戶列表",
        "choose_language": "選擇語言",
        "selected": "已選擇",
        "invalid_choice": "無效選擇",
        "ai_name": "AI 名稱",
        "persona": "人設描述",
        "call_you": "如何稱呼你",
        "welcome_back": "歡迎回來",
        "goodbye": "再見",
        "thinking": "思考中...",
        "chat_history": "聊天記錄",
        "user": "User",
        "input_content": "請輸入內容",
        "exit_chat": "已退出登入",
        "set_your_ai": "設定你的 AI",
        "skip": "直接回車跳過",
        "test_api": "測試 API 連接",
        "api_success": "API 連接成功",
        "api_fail": "API 連接失敗",
        "need_api": "需要 API Key 才能使用",
        "not_set_api": "未設置 API Key",
        "not_found_settings": "未找到設定，是否現在設置?",
        "setting": "設置?",
        "password_mismatch": "密碼不匹配",
        "user_exists": "用戶名已存在",
        "user_not_exist": "用戶不存在",
        "wrong_password": "密碼錯誤",
        "username_too_short": "用戶名至少3個字符",
        "password_too_short": "密碼至少4個字符",
        "empty_username": "用戶名不能為空",
    },
    "3": {  # 文言（简）
        "menu": "请择",
        "login": "登入",
        "register": "注册",
        "status": "状态",
        "language": "语言",
        "quit": "去",
        "username": "用户名",
        "password": "密码",
        "confirm_password": "再输密码",
        "api_key": "API Key",
        "login_success": "登入成",
        "register_success": "注册成",
        "logout": "去",
        "system_status": "系统状态",
        "network_ok": "网络通",
        "network_fail": "网络塞",
        "users_count": "注册者",
        "user_list": "用户列表",
        "choose_language": "择语言",
        "selected": "已择",
        "invalid_choice": "误择",
        "ai_name": "AI名",
        "persona": "人设",
        "call_you": "如何唤",
        "welcome_back": "归矣",
        "goodbye": "去矣",
        "thinking": "思中...",
        "chat_history": "会话",
        "user": "汝",
        "input_content": "输入言",
        "exit_chat": "已退",
        "set_your_ai": "设定AI",
        "skip": "回车跳过",
        "test_api": "试API",
        "api_success": "API通",
        "api_fail": "API塞",
        "need_api": "需API Key",
        "not_set_api": "未设API",
        "not_found_settings": "未设，设为？",
        "setting": "设？",
        "password_mismatch": "密码不合",
        "user_exists": "用户名有",
        "user_not_exist": "用户名无",
        "wrong_password": "密码误",
        "username_too_short": "��至少三字",
        "password_too_short": "密至少四字",
        "empty_username": "名不可空",
    },
    "4": {  # 文言（繁）
        "menu": "請擇",
        "login": "登入",
        "register": "註冊",
        "status": "狀態",
        "language": "語言",
        "quit": "去",
        "username": "用戶名",
        "password": "密碼",
        "confirm_password": "再輸密碼",
        "api_key": "API Key",
        "login_success": "登入成",
        "register_success": "註冊成",
        "logout": "去",
        "system_status": "系統狀態",
        "network_ok": "網絡通",
        "network_fail": "網絡塞",
        "users_count": "註冊者",
        "user_list": "用戶列表",
        "choose_language": "擇語言",
        "selected": "已擇",
        "invalid_choice": "誤擇",
        "ai_name": "AI名",
        "persona": "人設",
        "call_you": "如何喚",
        "welcome_back": "歸矣",
        "goodbye": "去矣",
        "thinking": "思中...",
        "chat_history": "會話",
        "user": "汝",
        "input_content": "輸入言",
        "exit_chat": "已退",
        "set_your_AI": "設定AI",
        "skip": "回車跳過",
        "test_api": "試API",
        "api_success": "API通",
        "api_fail": "API塞",
        "need_api": "需API Key",
        "not_set_api": "未設API",
        "not_found_settings": "未設，設為？",
        "setting": "設？",
        "password_mismatch": "密碼不合",
        "user_exists": "用戶名有",
        "user_not_exist": "用戶名無",
        "wrong_password": "密碼誤",
        "username_too_short": "名至少三字",
        "password_too_short": "密至少四字",
        "empty_username": "名不可空",
    },
    "5": {  # English
        "menu": "Please choose",
        "login": "Login",
        "register": "Register",
        "status": "Status",
        "language": "Language",
        "quit": "Quit",
        "username": "Username",
        "password": "Password",
        "confirm_password": "Confirm password",
        "api_key": "API Key",
        "login_success": "Login successful",
        "register_success": "Registration successful",
        "logout": "Logout",
        "system_status": "System Status",
        "network_ok": "Network: Connected",
        "network_fail": "Network: Disconnected",
        "users_count": "Registered users",
        "user_list": "User list",
        "choose_language": "Choose language",
        "selected": "Selected",
        "invalid_choice": "Invalid choice",
        "ai_name": "AI name",
        "persona": "Persona",
        "call_you": "How to call you",
        "welcome_back": "Welcome back",
        "goodbye": "Goodbye",
        "thinking": "Thinking...",
        "chat_history": "Chat history",
        "user": "User",
        "input_content": "Enter message",
        "exit_chat": "Logged out",
        "set_your_ai": "Set up your AI",
        "skip": "Press Enter to skip",
        "test_api": "Testing API",
        "api_success": "API connected",
        "api_fail": "API failed",
        "need_api": "API Key required",
        "not_set_api": "API Key not set",
        "not_found_settings": "Settings not found. Set now?",
        "setting": "Set?",
        "password_mismatch": "Password mismatch",
        "user_exists": "Username exists",
        "user_not_exist": "User not found",
        "wrong_password": "Wrong password",
        "username_too_short": "Username min 3 chars",
        "password_too_short": "Password min 4 chars",
        "empty_username": "Username required",
    },
    "6": {  # にほんご
        "menu": "えらんでください",
        "login": "ログイン",
        "register": "とうろく",
        "status": "ステータス",
        "language": "げんご",
        "quit": "おわる",
        "username": "ゆーざーめい",
        "password": "ぱすわーど",
        "confirm_password": "ぱすわーどかく���ん",
        "api_key": "API Key",
        "login_success": "ログインせいこう",
        "register_success": "とうろくせいこう",
        "logout": "ログアウト",
        "system_status": "しすてむすてーたす",
        "network_ok": "ねっとう: かつようちゅう",
        "network_fail": "ねっとう: ふかつよう",
        "users_count": "とうろくゆーざー",
        "user_list": "ゆーざーリスト",
        "choose_language": "げんごをえらぶ",
        "selected": "えらびました",
        "invalid_choice": "こうそく",
        "ai_name": "AIなまえ",
        "persona": "じんせつ",
        "call_you": "なづけ",
        "welcome_back": "おかえり",
        "goodbye": "さようなら",
        "thinking": "かんがえちゅう...",
        "chat_history": "かいわきろく",
        "user": "ゆーざー",
        "input_content": "にゅうりょく",
        "exit_chat": "ログアウト濟み",
        "set_your_ai": "AIせってい",
        "skip": "Enterでとばす",
        "test_api": "APIしすてむてすと",
        "api_success": "APIかつようちゅう",
        "api_fail": "APIしっぱい",
        "need_api": "API Keyが必要です",
        "not_set_api": "API Keyみせってい",
        "not_found_settings": "せっていかりません。いませっていしますか？",
        "setting": "せってい？",
        "password_mismatch": "ぱすわーど不一致",
        "user_exists": "ゆーざーすみません",
        "user_not_exist": "ゆーざーみません",
        "wrong_password": "ぱすわーどちがい",
        "username_too_short": "ゆーざー3もじいじょう",
        "password_too_short": "ぱすわーど4もじいじょう",
        "empty_username": "ゆーざーひつよう",
    },
    "7": {  # le français
        "menu": "Veuillez choisir",
        "login": "Connexion",
        "register": "S'inscrire",
        "status": "Statut",
        "language": "Langue",
        "quit": "Quitter",
        "username": "Nom d'utilisateur",
        "password": "Mot de passe",
        "confirm_password": "Confirmer le mot de passe",
        "api_key": "Clé API",
        "login_success": "Connexion réussie",
        "register_success": "Inscription réussie",
        "logout": "Déconnexion",
        "system_status": "État du système",
        "network_ok": "Réseau: Connecté",
        "network_fail": "Réseau: Déconnecté",
        "users_count": "Utilisateurs inscrits",
        "user_list": "Liste des utilisateurs",
        "choose_language": "Choisir la langue",
        "selected": "Sélectionné",
        "invalid_choice": "Choix invalide",
        "ai_name": "Nom de l'IA",
        "persona": "Persona",
        "call_you": "Comment vous appeler",
        "welcome_back": "Bon retour",
        "goodbye": "Au revoir",
        "thinking": "Réflexion...",
        "chat_history": "Historique",
        "user": "Utilisateur",
        "input_content": "Entrez le message",
        "exit_chat": "Déconnecté",
        "set_your_ai": "Configurez votre IA",
        "skip": "Entrée pour passer",
        "test_api": "Test API",
        "api_success": "API connectée",
        "api_fail": "Échec API",
        "need_api": "Clé API requise",
        "not_set_api": "Clé API non définie",
        "not_found_settings": "Paramètres non trouvés. Configurer maintenant?",
        "setting": "Configurer?",
        "password_mismatch": "Mot de passe différent",
        "user_exists": "Nom d'utilisateur existant",
        "user_not_exist": "Utilisateur introuvable",
        "wrong_password": "Mot de passe incorrect",
        "username_too_short": "Nom min 3 caractères",
        "password_too_short": "Mot de passe min 4 caractères",
        "empty_username": "Nom requis",
    },
}

LANGUAGES = {
    "1": "简体汉语",
    "2": "繁体汉语",
    "3": "文言（简）",
    "4": "文言（繁）",
    "5": "English",
    "6": "にほんご",
    "7": "le français",
}

def load_language():
    global CURRENT_LANG
    if os.path.exists(LANG_FILE):
        try:
            with open(LANG_FILE, "r", encoding="utf-8") as f:
                CURRENT_LANG = f.read().strip()
        except:
            pass

def save_language(lang_code):
    global CURRENT_LANG
    CURRENT_LANG = lang_code
    with open(LANG_FILE, "w", encoding="utf-8") as f:
        f.write(lang_code)

def _(key):
    return LANG_STRINGS.get(CURRENT_LANG, LANG_STRINGS["1"]).get(key, key)

# ------ 网络检测 ------

def check_internet():
    test_urls = [
        "https://api.deepseek.com",
        "https://www.baidu.com",
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
    if not api_key:
        return False, "未设置 API Key"
    try:
        client = OpenAI(api_key=api_key, base_url=_BASE_URL)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
            timeout=10
        )
        return True, "OK"
    except Exception as e:
        err_msg = str(e)
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

def safe_filename(value):
    invalid_chars = '<>:"/\\|?*'
    safe = "".join("_" if ch in invalid_chars else ch for ch in str(value)).strip()
    return safe or "user"

def get_default_records_parent():
    return os.path.join(os.path.expanduser("~"), "Documents")

def create_records_dir(parent_path):
    parent_path = (parent_path or "").strip().strip('"').strip("'")
    if not parent_path:
        parent_path = get_default_records_parent()
    parent_path = os.path.expandvars(os.path.expanduser(parent_path))
    records_dir = os.path.join(parent_path, "SnowBot")
    os.makedirs(records_dir, exist_ok=True)
    return records_dir

def collect_records_dir():
    print(f"\n{Colors.CYAN}=== 文件存放路径 ==={Colors.RESET}")
    print(f"{Colors.YELLOW}请输入用于存放聊天记录和用户设定的文件夹路径。{Colors.RESET}")
    print(f"{Colors.YELLOW}程序会在该路径下自动创建 SnowBot 文件夹。{Colors.RESET}")
    print(f"{Colors.YELLOW}直接回车默认使用: {get_default_records_parent()}{Colors.RESET}")

    while True:
        parent_path = input(f"{Colors.CYAN}文件存放路径: {Colors.RESET}").strip()
        try:
            records_dir = create_records_dir(parent_path)
            print(f"{Colors.GREEN}用户记录将保存到: {records_dir}{Colors.RESET}")
            return records_dir
        except OSError as e:
            print(f"{Colors.RED}无法创建文件夹: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}请换一个有写入权限的路径。{Colors.RESET}")

def collect_login_records_dir(current_records_dir=None):
    print(f"\n{Colors.CYAN}=== 文件存放路径 ==={Colors.RESET}")
    print(f"{Colors.YELLOW}登录顺序: 用户名 -> 密码 -> 路径 -> 其他{Colors.RESET}")
    print(f"{Colors.YELLOW}请输入用于存放聊天记录和用户设定的文件夹路径。{Colors.RESET}")
    print(f"{Colors.YELLOW}如果输入新路径，程序会在该路径下自动创建 SnowBot 文件夹。{Colors.RESET}")
    if current_records_dir:
        print(f"{Colors.YELLOW}直接回车使用上次路径: {current_records_dir}{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}直接回车默认使用: {get_default_records_parent()}{Colors.RESET}")

    while True:
        parent_path = input(f"{Colors.CYAN}文件存放路径: {Colors.RESET}").strip()
        try:
            if parent_path:
                records_dir = create_records_dir(parent_path)
            elif current_records_dir:
                records_dir = validate_records_dir(current_records_dir)
            else:
                records_dir = create_records_dir(parent_path)
            print(f"{Colors.GREEN}用户记录将保存到: {records_dir}{Colors.RESET}")
            return records_dir
        except OSError as e:
            print(f"{Colors.RED}无法使用该文件夹: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}请换一个有写入权限的路径。{Colors.RESET}")
            current_records_dir = None

def validate_records_dir(records_dir):
    records_dir = os.path.expandvars(os.path.expanduser(records_dir))
    os.makedirs(records_dir, exist_ok=True)

    test_file = os.path.join(records_dir, ".snowbot_write_test")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("ok")
    try:
        os.remove(test_file)
    except OSError:
        pass

    return records_dir

def ensure_login_records_dir(username, users):
    while True:
        records_dir = users[username].get("records_dir")
        try:
            records_dir = collect_login_records_dir(records_dir)
            users[username]["records_dir"] = records_dir
            save_users(users)
            return records_dir
        except OSError as e:
            print(f"{Colors.RED}当前文件存放路径不可用: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}请重新指定文件存放路径。{Colors.RESET}")
            users[username]["records_dir"] = collect_records_dir()
            save_users(users)

def get_user_records_dir(username):
    users = load_users()
    user_data = users.get(username, {})
    records_dir = user_data.get("records_dir")
    if not records_dir:
        records_dir = _DATA_DIR
    os.makedirs(records_dir, exist_ok=True)
    return records_dir

def get_settings_file(username):
    return os.path.join(get_user_records_dir(username), f"settings_{safe_filename(username)}.json")

def load_settings(username):
    settings_file = get_settings_file(username)
    if not os.path.exists(settings_file):
        return None
    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None

def save_settings(username, settings):
    settings_file = get_settings_file(username)
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

# ------ 注册时收集设定 ------

def collect_settings():
    print(f"\n{Colors.CYAN}=== 设定你的 AI ==={Colors.RESET}\n")
    
    name = input(f"{Colors.YELLOW}AI 名称: {Colors.RESET}").strip()
    if not name:
        name = "含霜"
    
    persona = input(f"{Colors.YELLOW}人设描述: {Colors.RESET}").strip()
    if not persona:
        persona = "AI 助手"
    
    call_name = input(f"{Colors.YELLOW}如何称呼你: {Colors.RESET}").strip()
    if not call_name:
        call_name = "你"
    
    settings = {
        "name": name,
        "persona": persona,
        "call_name": call_name,
    }
    
    return settings

def register(username, password):
    users = load_users()
    if not username:
        return False, _("empty_username")
    if len(username) < 3:
        return False, _("username_too_short")
    if username in users:
        return False, f"{Colors.RED}{_('user_exists')}{Colors.RESET}"
    if len(password) < 4:
        return False, _("password_too_short")

    # 注册时指定文件存放路径，并在该路径下创建 SnowBot 文件夹
    records_dir = collect_records_dir()
    
    users[username] = {
        "password": hash_password(password),
        "api_key": "",
        "records_dir": records_dir
    }
    save_users(users)
    
    # 收集设定
    settings = collect_settings()
    save_settings(username, settings)
    
    return True, f"{Colors.GREEN}注册成功！设定已保存\n用户记录路径: {records_dir}{Colors.RESET}"

def login(username, password):
    users = load_users()
    if not username:
        return None, "用户名不能为空"
    if username not in users:
        return None, f"{Colors.RED}用户不存在{Colors.RESET}"
    if users[username]["password"] != hash_password(password):
        return None, f"{Colors.RED}密码错误{Colors.RESET}"
    ensure_login_records_dir(username, users)
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

# ------ 构建系统人设 ------

def build_system_prompt(settings):
    name = settings.get("name", "含霜")
    persona = settings.get("persona", "AI 助手")
    call_name = settings.get("call_name", "你")
    
    return f"你的名字叫{name}，{persona}。你会称呼对方为{call_name}。"

# ------ 记忆模块 ------

def get_memory_file(username):
    return os.path.join(get_user_records_dir(username), f"memories_{safe_filename(username)}.json")

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

def chat(user_msg, memories, client, system_prompt):
    messages = [{"role": "system", "content": system_prompt}]
    for h_user, h_assistant in memories:
        messages.append({"role": "user", "content": h_user})
        messages.append({"role": "assistant", "content": h_assistant})
    messages.append({"role": "user", "content": user_msg})
    
    print(f"{Colors.CYAN}含霜思考中...{Colors.RESET}")
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
    for opt in options:
        print(f"  {Colors.CYAN}*{Colors.RESET} {opt}")
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
    load_language()
    print_header(f"{Colors.MAGENTA}含霜 SnowBot{Colors.RESET}")
    
    print(f"{Colors.CYAN}检测网络连接...{Colors.RESET}")
    if check_internet():
        print_success("网络连接正常")
    else:
        print_error("无法连接到互联网")
    
    print_divider()
    
    while True:
        print_menu([_("login") + " (l)", _("register") + " (r)", _("status") + " (s)", "Language (lg)", _("quit") + " (q)"], _("menu"))
        choice = input(f"{Colors.CYAN}>> {Colors.RESET}").strip().lower()
        
        if choice in ["login", "l", "1"]:
            do_login()
        elif choice in ["register", "r", "2"]:
            do_register()
        elif choice in ["status", "s", "3"]:
            do_status()
        elif choice in ["language", "lg", "4"]:
            do_language()
        elif choice in ["quit", "q", "5", "exit"]:
            print(f"{Colors.GREEN}{_('goodbye')}{Colors.RESET}")
            break
        else:
            print_error(_("invalid_choice"))

def do_status():
    print_header(_("system_status"))
    
    if check_internet():
        print_success(_("network_ok"))
    else:
        print_error(_("network_fail"))
    
    users = load_users()
    print_info(f"{_('users_count')}: {len(users)} 人")
    
    if users:
        print(f"{Colors.CYAN}{_('user_list')}:{Colors.RESET}")
        for username in users:
            api_key = users[username].get("api_key", "")

# ------ 语言模块 ------

LANGUAGES = {
    "1": "简体汉语",
    "2": "繁体汉语",
    "3": "文言（简）",
    "4": "文言（繁）",
    "5": "English",
    "6": "にほんご",
    "7": "le français",
}

def do_language():
    # Always use English for language selection
    print_header("Choose Language")
    print(f"{Colors.CYAN}Choose Language:{Colors.RESET}\n")
    for code, name in LANGUAGES.items():
        print(f"  {code}. {name}")
    print()
    choice = input(f"{Colors.CYAN}>> {Colors.RESET}").strip()
    if choice in LANGUAGES:
        save_language(choice)
        print_success(f"Selected: {LANGUAGES[choice]}")
    else:
        print_error("Invalid choice")

def do_login():
    print_header(_("login"))
    username = input(f"{Colors.CYAN}{_('username')}: {Colors.RESET}").strip()
    password = input(f"{Colors.CYAN}{_('password')}: {Colors.RESET}").strip()
    
    user_data, msg = login(username, password)
    if user_data is None:
        print_error(msg)
        return
    
    # 检查设定
    settings = load_settings(username)
    if not settings:
        print(f"{Colors.YELLOW}{_('not_found_settings')}{Colors.RESET}")
        if input(f"{Colors.YELLOW}{_('setting')} (y/n): {Colors.RESET}").strip().lower() == "y":
            settings = collect_settings()
            save_settings(username, settings)
        else:
            settings = {"name": "含霜", "persona": "AI 助手", "call_name": "你"}
    
    # 检查 API
    client, user_info = init_api(username)
    if client is None:
        print(f"{Colors.YELLOW}{_('not_set_api')}{Colors.RESET}")
        api_key = input(f"{Colors.CYAN}{_('api_key')}: {Colors.RESET}").strip()
        if api_key:
            print(f"{Colors.CYAN}{_('test_api')}...{Colors.RESET}")
            ok, result = check_api_status(api_key)
            if ok:
                users = load_users()
                users[username]["api_key"] = api_key
                save_users(users)
                client = OpenAI(api_key=api_key, base_url=_BASE_URL)
                print_success(_("api_success"))
            else:
                print_error(f"{_('api_fail')}: {result}")
                return
        else:
            print_error(_("need_api"))
            return
    
    print_success(f"{_('welcome_back')}，{username}！")
    chat_loop(username, client, settings)

def do_register():
    print_header(_("register"))
    username = input(f"{Colors.CYAN}{_('username')}: {Colors.RESET}").strip()
    password = input(f"{Colors.CYAN}{_('password')}: {Colors.RESET}").strip()
    confirm = input(f"{Colors.CYAN}{_('confirm_password')}: {Colors.RESET}").strip()
    
    if password != confirm:
        print_error(_("password_mismatch"))
        return
    
    success, msg = register(username, password)
    if not success:
        print_error(msg)
        return
    
    print_success(msg)
    
    # 设置 API Key
    print(f"\n{Colors.CYAN}Optional: {_('api_key')}{Colors.RESET}")
    api_key = input(f"{Colors.CYAN}{_('api_key')} ({_('skip')}): {Colors.RESET}").strip()
    if api_key:
        print(f"{Colors.CYAN}{_('test_api')}...{Colors.RESET}")
        ok, result = check_api_status(api_key)
        if ok:
            users = load_users()
            users[username]["api_key"] = api_key
            save_users(users)
            print_success(_("api_key") + " saved")
        else:
            print_error(f"{_('api_fail')}: {result}")

def chat_loop(username, client, settings):
    memories = load_memories(username, limit=None)
    system_prompt = build_system_prompt(settings)
    
    ai_name = settings.get("name", "含霜")
    print_header(f"Chat - {username}")
    print(f"--- {_('chat_history')} ({len(memories)} 条) ---")
    
    for i, (u, a) in enumerate(memories):
        print(f"{Colors.CYAN}[{i+1}] {_('user')}:{Colors.RESET}")
        for line in u.split("\n"):
            print(f"  {line}")
        print(f"{Colors.MAGENTA}{ai_name}:{Colors.RESET}")
        for line in a.split("\n"):
            print(f"  {line}")
    print_divider()
    print(f"Input {Colors.YELLOW}logout{Colors.RESET} {_('logout')}")
    print_divider()
    
    while True:
        user_msg = input(f"{Colors.YELLOW}{_('user')}>{Colors.RESET} ").strip()
        
        if not user_msg:
            print(f"{Colors.YELLOW}{_('input_content')}{Colors.RESET}")
            continue
        
        if user_msg.lower() in ["logout", "exit", "quit"]:
            print(f"{Colors.CYAN}{_('exit_chat')}{Colors.RESET}")
            print_divider()
            return
        
        assistant_reply = chat(user_msg, memories, client, system_prompt)
        
        if assistant_reply:
            print(f"{Colors.MAGENTA}{ai_name}:{Colors.RESET}")
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
        print(f"\n{Colors.CYAN}再见{Colors.RESET}")
    except EOFError:
        print(f"\n{Colors.CYAN}再见{Colors.RESET}")
