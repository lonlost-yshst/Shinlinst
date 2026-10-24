# -------- 含霜 SnowBot --------
# AI 聊天猫娘 - 1.3.1

from openai import OpenAI
import json
import os
import re
import sys
import hashlib
import concurrent.futures

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

# 用户注册记录目录：
#   1) 优先使用环境变量 SNOWBOT_DATA_DIR（可用于临时切换或迁移）
#   2) 否则使用硬编码默认 C:\Shinlinst\.files\SnowBot
import shutil
_DATA_DIR = os.environ.get("SNOWBOT_DATA_DIR") or r"C:\Shinlinst\.files\SnowBot"
os.makedirs(_DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(_DATA_DIR, "users.json")
LANG_FILE = os.path.join(_DATA_DIR, "language.txt")


def migrate_legacy_data():
    """
    从 1.2.4 及更早版本迁移 users.json / language.txt 到新 _DATA_DIR。

    仅迁移全局文件；用户 records_dir（即 settings/memories 所在目录）保持原样。
    若新位置已存在对应文件，则不覆盖，避免破坏新版本数据。
    """
    roaming = os.environ.get(
        "APPDATA",
        os.path.join(os.path.expanduser("~"), "AppData", "Roaming"),
    )
    legacy_dir = os.path.join(roaming, "SnowBot")
    try:
        if os.path.abspath(legacy_dir) == os.path.abspath(_DATA_DIR):
            return
        if not os.path.isdir(legacy_dir):
            return
    except OSError:
        return

    pairs = [
        ("users.json", USERS_FILE),
        ("language.txt", LANG_FILE),
    ]
    migrated, failed = [], []
    for name, target in pairs:
        src = os.path.join(legacy_dir, name)
        if not (os.path.isfile(src) and not os.path.exists(target)):
            continue
        try:
            shutil.copy2(src, target)
            migrated.append(name)
        except OSError as e:
            failed.append(f"{name}: {e}")

    if migrated:
        print(f"{Colors.GREEN}[{_('migrate_tag')}] {_('migrate_success').format(path=_DATA_DIR, files=', '.join(migrated))}{Colors.RESET}")
        print(f"{Colors.YELLOW}[{_('migrate_tag')}] {_('migrate_hint')}{Colors.RESET}")
    if failed:
        for line in failed:
            print(f"{Colors.RED}[{_('migrate_tag')}] {_('migrate_fail').format(error=line)}{Colors.RESET}")

# ------ 模型配置 ------

MODELS = {
    "1": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "model_name": "deepseek-chat",
        "api_key_hint": "DeepSeek API Key",
    },
    "2": {
        "name": "Doubao",
        "base_url": "https://api.doubao.com/v1",
        "model_name": "doubao-3.5-pro",
        "api_key_hint": "豆包 API Key",
    },
    "3": {
        "name": "Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "model_name": "moonshot-v1-8k",
        "api_key_hint": "Kimi API Key",
    },
    "4": {
        "name": "MiniMax",
        "base_url": "https://api.minimax.chat/v1",
        "model_name": "abab5.5-chat",
        "api_key_hint": "MiniMax API Key",
    },
    "5": {
        "name": "Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model_name": "gemini-pro",
        "api_key_hint": "Gemini API Key",
        "use_gemini": True,
    },
    "6": {
        "name": "ChatGPT",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-3.5-turbo",
        "api_key_hint": "OpenAI API Key",
    },
}

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
        "records_path_title": "文件存放路径",
        "records_path_hint": "请输入用于存放聊天记录和用户设定的文件夹路径。",
        "records_path_auto_create": "程序会直接使用您指定的路径。",
        "records_path_new_hint": "如果输入新路径，程序会直接使用该路径。",
        "records_path_default": "直接回车默认使用:",
        "records_path_last": "直接回车使用上次路径:",
        "records_path_prompt": "文件存放路径:",
        "records_path_saved": "用户记录将保存到:",
        "records_path_create_fail": "无法创建文件夹:",
        "records_path_use_fail": "无法使用该文件夹:",
        "records_path_try_another": "请换一个有写入权限的路径。",
        "records_path_unavailable": "当前文件存放路径不可用:",
        "records_path_respecify": "请重新指定文件存放路径。",
        "migrate_tag": "迁移",
        "migrate_success": "已从旧位置复制到 {path}：{files}",
        "migrate_hint": "用户的 records_dir 未变动；如需调整请在登录时重新指定。",
        "migrate_fail": "失败：{error}",
        "register_success_detail": "注册成功！设定已保存",
        "user_records_path": "用户记录路径:",
        "timeout_msg": "连接超时（超过90秒），请重试。",
        "empty_response": "API返回空响应，请重试。",
        "api_maybe_available": "可能可用（超时）",
        "network_checking": "检测网络连接...",
        "network_ok_msg": "网络连接正常",
        "network_fail_msg": "无法连接到互联网",
        "api_key_saved": "API Key 已保存",
        "chat_label": "聊天",
        "count_unit": "人",
        "count_records_unit": "条",
        "optional": "可选",
        "error": "错误",
        "info": "信息",
        "choose_model": "选择 AI 模型",
        "model": "模型",
        "current_model": "当前模型",
        "model_not_set": "未设置模型",
        "model_changed": "模型已切换",
    },
    "2": {  # 繁体汉语
        "menu": "請選擇",
        "login": "登入",
        "register": "註冊",
        "status": "狀態",
        "language": "Language",
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
        "records_path_title": "文件存放路徑",
        "records_path_hint": "請輸入用於存放聊天記錄和用戶設定的文件夾路徑。",
        "records_path_auto_create": "程序會直接使用您指定的路徑。",
        "records_path_new_hint": "如果輸入新路徑，程序會直接使用該路徑。",
        "records_path_default": "直接回車默認使用:",
        "records_path_last": "直接回車使用上次路徑:",
        "records_path_prompt": "文件存放路徑:",
        "records_path_saved": "用戶記錄將保存到:",
        "records_path_create_fail": "無法創建文件夾:",
        "records_path_use_fail": "無法使用該文件夾:",
        "records_path_try_another": "請換一個有寫入權限的路徑。",
        "records_path_unavailable": "當前文件存放路徑不可用:",
        "records_path_respecify": "請重新指定文件存放路徑。",
        "migrate_tag": "遷移",
        "migrate_success": "已從舊位置複製到 {path}：{files}",
        "migrate_hint": "用戶的 records_dir 未變動；如需調整請在登入時重新指定。",
        "migrate_fail": "失敗：{error}",
        "register_success_detail": "註冊成功！設定已保存",
        "user_records_path": "用戶記錄路徑:",
        "timeout_msg": "連接超時（超過90秒），請重試。",
        "empty_response": "API返回空響應，請重試。",
        "api_maybe_available": "可能可用（超時）",
        "network_checking": "檢測網絡連接...",
        "network_ok_msg": "網絡連接正常",
        "network_fail_msg": "無法連接到互聯網",
        "api_key_saved": "API Key 已保存",
        "chat_label": "聊天",
        "count_unit": "人",
        "count_records_unit": "條",
        "optional": "可選",
        "error": "錯誤",
        "info": "信息",
        "choose_model": "選擇 AI 模型",
        "model": "模型",
        "current_model": "當前模型",
        "model_not_set": "未設置模型",
        "model_changed": "模型已切換",
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
        "username_too_short": "名至少三字",
        "password_too_short": "密至少四字",
        "empty_username": "名不可空",
        "records_path_title": "文件路径",
        "records_path_hint": "请输存录与设定之路径。",
        "records_path_auto_create": "程序将径用君所输之径。",
        "records_path_new_hint": "若输新径，程序将径用之。",
        "records_path_default": "回车即用默认:",
        "records_path_last": "回车即用旧径:",
        "records_path_prompt": "文件路径:",
        "records_path_saved": "记录将存于:",
        "records_path_create_fail": "不可建文件夹:",
        "records_path_use_fail": "不可用此文件夹:",
        "records_path_try_another": "请换可写之径。",
        "records_path_unavailable": "今存录之径不可用:",
        "records_path_respecify": "请重指文件路径。",
        "migrate_tag": "迁",
        "migrate_success": "已自旧位复制至 {path}：{files}",
        "migrate_hint": "用户之 records_dir 未动；若需调，请于登时重指。",
        "migrate_fail": "败：{error}",
        "register_success_detail": "注册成！设定已存",
        "user_records_path": "记录路径:",
        "timeout_msg": "连接逾时（过九十秒），请再试。",
        "empty_response": "API空应，请再试。",
        "api_maybe_available": "或可用（逾时）",
        "network_checking": "探网络...",
        "network_ok_msg": "网络通",
        "network_fail_msg": "网络不通",
        "api_key_saved": "API Key 已存",
        "chat_label": "会话",
        "count_unit": "人",
        "count_records_unit": "则",
        "optional": "可略",
        "error": "误",
        "info": "告",
        "choose_model": "择AI模型",
        "model": "模型",
        "current_model": "今模型",
        "model_not_set": "未设模型",
        "model_changed": "模型已换",
    },
    "4": {  # 文言（繁）
        "menu": "請擇",
        "login": "登入",
        "register": "註冊",
        "status": "狀態",
        "language": "Language",
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
        "set_your_ai": "設定AI",
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
        "records_path_title": "文件路徑",
        "records_path_hint": "請輸存錄與設定之路徑。",
        "records_path_auto_create": "程序將徑用君所輸之路徑。",
        "records_path_new_hint": "若輸新路徑，程序將徑用之。",
        "records_path_default": "回車即用默認:",
        "records_path_last": "回車即用舊徑:",
        "records_path_prompt": "文件路徑:",
        "records_path_saved": "記錄將存於:",
        "records_path_create_fail": "不可建文件夾:",
        "records_path_use_fail": "不可用此文件夾:",
        "records_path_try_another": "請換可寫之徑。",
        "records_path_unavailable": "今存錄之徑不可用:",
        "records_path_respecify": "請重指文件路徑。",
        "migrate_tag": "遷",
        "migrate_success": "已自舊位複製至 {path}：{files}",
        "migrate_hint": "用戶之 records_dir 未動；若需調，請於登入時重指。",
        "migrate_fail": "敗：{error}",
        "register_success_detail": "註冊成！設定已存",
        "user_records_path": "記錄路徑:",
        "timeout_msg": "連接逾時（過九十秒），請再試。",
        "empty_response": "API空應，請再試。",
        "api_maybe_available": "或可用（逾時）",
        "network_checking": "探網絡...",
        "network_ok_msg": "網絡通",
        "network_fail_msg": "網絡不通",
        "api_key_saved": "API Key 已存",
        "chat_label": "會話",
        "count_unit": "人",
        "count_records_unit": "則",
        "optional": "可略",
        "error": "誤",
        "info": "告",
        "choose_model": "擇AI模型",
        "model": "模型",
        "current_model": "今模型",
        "model_not_set": "未設模型",
        "model_changed": "模型已換",
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
        "records_path_title": "File Storage Path",
        "records_path_hint": "Enter the folder path for storing chat records and user settings.",
        "records_path_auto_create": "The program will use the specified path directly.",
        "records_path_new_hint": "If you enter a new path, the program will use it directly.",
        "records_path_default": "Press Enter for default:",
        "records_path_last": "Press Enter to use previous path:",
        "records_path_prompt": "File storage path:",
        "records_path_saved": "User records will be saved to:",
        "records_path_create_fail": "Cannot create folder:",
        "records_path_use_fail": "Cannot use this folder:",
        "records_path_try_another": "Please choose a path with write permission.",
        "records_path_unavailable": "Current file storage path unavailable:",
        "records_path_respecify": "Please specify a new file storage path.",
        "migrate_tag": "Migrate",
        "migrate_success": "Copied from legacy location to {path}: {files}",
        "migrate_hint": "User records_dir is unchanged. You can re-specify it at login if needed.",
        "migrate_fail": "Failed: {error}",
        "register_success_detail": "Registration successful! Settings saved",
        "user_records_path": "User records path:",
        "timeout_msg": "Connection timed out (over 90s), please retry.",
        "empty_response": "API returned empty response, please retry.",
        "api_maybe_available": "Possibly available (timed out)",
        "network_checking": "Checking network connection...",
        "network_ok_msg": "Network connected",
        "network_fail_msg": "Cannot connect to the internet",
        "api_key_saved": "API Key saved",
        "chat_label": "Chat",
        "count_unit": "users",
        "count_records_unit": "records",
        "optional": "Optional",
        "error": "Error",
        "info": "Info",
        "choose_model": "Choose AI Model",
        "model": "Model",
        "current_model": "Current model",
        "model_not_set": "Model not set",
        "model_changed": "Model changed",
    },
    "6": {  # にほんご
        "menu": "えらんでください",
        "login": "ログイン",
        "register": "とうろく",
        "status": "ステータス",
        "language": "Language",
        "quit": "おわる",
        "username": "ゆーざーめい",
        "password": "ぱすわーど",
        "confirm_password": "ぱすわーどかくにん",
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
        "invalid_choice": "むこうなせんたく",
        "ai_name": "AIなまえ",
        "persona": "じんせつ",
        "call_you": "なづけ",
        "welcome_back": "おかえり",
        "goodbye": "さようなら",
        "thinking": "かんがえちゅう...",
        "chat_history": "かいわきろく",
        "user": "ゆーざー",
        "input_content": "にゅうりょく",
        "exit_chat": "ログアウトずみ",
        "set_your_ai": "AIせってい",
        "skip": "Enterでとばす",
        "test_api": "APIしすてむてすと",
        "api_success": "APIかつようちゅう",
        "api_fail": "APIしっぱい",
        "need_api": "API Keyが必要です",
        "not_set_api": "API Keyみせってい",
        "not_found_settings": "せっていかりません。いませっていしますか？",
        "setting": "せってい？",
        "password_mismatch": "ぱすわーどふいっち",
        "user_exists": "ゆーざーめいすでにあり",
        "user_not_exist": "ゆーざーみつかりません",
        "wrong_password": "ぱすわーどちがい",
        "username_too_short": "ゆーざー3もじいじょう",
        "password_too_short": "ぱすわーど4もじいじょう",
        "empty_username": "ゆーざーひつよう",
        "records_path_title": "ふぁいるほぞんぱす",
        "records_path_hint": "かいわきろくとゆーざーせっていをほぞんするふぉるだぱすをにゅうりょくしてください。",
        "records_path_auto_create": "ぷろぐらむはしていされたぱすをちょくせつつかいます。",
        "records_path_new_hint": "あたらしいぱすをにゅうりょくすると、ぷろぐらむはそれをちょくせつつかいます。",
        "records_path_default": "Enterででふぉるとつかう:",
        "records_path_last": "Enterでまえのぱすつかう:",
        "records_path_prompt": "ふぁいるほぞんぱす:",
        "records_path_saved": "ゆーざーきろくほぞんさき:",
        "records_path_create_fail": "ふぉるださくせいふかのう:",
        "records_path_use_fail": "このふぉるだつかえません:",
        "records_path_try_another": "かきこみけんげんのあるぱすをえらんでください。",
        "records_path_unavailable": "げんざいのほぞんぱすつかえません:",
        "records_path_respecify": "あたらしいほぞんぱすをしていしてください。",
        "migrate_tag": "いこう",
        "migrate_success": "きゅうぱすから {path} へコピーしました: {files}",
        "migrate_hint": "ゆーざーの records_dir はへんこうありません。ひつようであれば、ログインときにさいしていしてください。",
        "migrate_fail": "しっぱい: {error}",
        "register_success_detail": "とうろくせいこう！せっていほぞんずみ",
        "user_records_path": "ゆーざーきろくぱす:",
        "timeout_msg": "せつぞくたいむあうと（90びょういか）、やりなおしてください。",
        "empty_response": "APIからくうのへんとう、やりなおしてください。",
        "api_maybe_available": "かのうせいあり（たいむあうと）",
        "network_checking": "ねっとうせつぞくかくにんちゅう...",
        "network_ok_msg": "ねっとうせつぞくせいこう",
        "network_fail_msg": "ねっとうにせつぞくできません",
        "api_key_saved": "API Keyほぞんずみ",
        "chat_label": "ちゃっと",
        "count_unit": "にん",
        "count_records_unit": "けん",
        "optional": "こうひつよう",
        "error": "えらー",
        "info": "じょうほう",
        "choose_model": "AIもでるえらぶ",
        "model": "もでる",
        "current_model": "げんざいのもでる",
        "model_not_set": "もでるみせってい",
        "model_changed": "もでるこうかんずみ",
    },
    "7": {  # le français
        "menu": "Veuillez choisir",
        "login": "Connexion",
        "register": "S'inscrire",
        "status": "Statut",
        "language": "Language",
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
        "records_path_title": "Chemin de stockage",
        "records_path_hint": "Entrez le chemin du dossier pour stocker les historiques et paramètres.",
        "records_path_auto_create": "Le programme utilisera directement le chemin spécifié.",
        "records_path_new_hint": "Si vous entrez un nouveau chemin, le programme l'utilisera directement.",
        "records_path_default": "Entrée pour le chemin par défaut:",
        "records_path_last": "Entrée pour utiliser le chemin précédent:",
        "records_path_prompt": "Chemin de stockage:",
        "records_path_saved": "Les enregistrements seront sauvegardés dans:",
        "records_path_create_fail": "Impossible de créer le dossier:",
        "records_path_use_fail": "Impossible d'utiliser ce dossier:",
        "records_path_try_another": "Veuillez choisir un chemin avec accès en écriture.",
        "records_path_unavailable": "Chemin de stockage actuel indisponible:",
        "records_path_respecify": "Veuillez spécifier un nouveau chemin de stockage.",
        "migrate_tag": "Migration",
        "migrate_success": "Copié depuis l'ancien emplacement vers {path} : {files}",
        "migrate_hint": "Le records_dir de l'utilisateur n'a pas été modifié. Vous pouvez le redéfinir à la connexion si nécessaire.",
        "migrate_fail": "Échec : {error}",
        "register_success_detail": "Inscription réussie ! Paramètres sauvegardés",
        "user_records_path": "Chemin des enregistrements:",
        "timeout_msg": "Délai d'attente dépassé (plus de 90s), veuillez réessayer.",
        "empty_response": "Réponse vide de l'API, veuillez réessayer.",
        "api_maybe_available": "Peut-être disponible (délai dépassé)",
        "network_checking": "Vérification de la connexion réseau...",
        "network_ok_msg": "Réseau connecté",
        "network_fail_msg": "Impossible de se connecter à Internet",
        "api_key_saved": "Clé API sauvegardée",
        "chat_label": "Discussion",
        "count_unit": "utilisateurs",
        "count_records_unit": "enregistrements",
        "optional": "Facultatif",
        "error": "Erreur",
        "info": "Info",
        "choose_model": "Choisir le modèle AI",
        "model": "Modèle",
        "current_model": "Modèle actuel",
        "model_not_set": "Modèle non défini",
        "model_changed": "Modèle changé",
    },
}

LANGUAGES = {
    "1": "简体汉语",
    "2": "繁體漢語",
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

# ------ API 检测 ------

def check_api_status(api_key, model_code="1"):
    if not api_key:
        return False, _("not_set_api")
    model_config = MODELS.get(model_code, MODELS["1"])
    try:
        client = OpenAI(api_key=api_key, base_url=model_config["base_url"])
        response = client.chat.completions.create(
            model=model_config["model_name"],
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
            timeout=10
        )
        return True, "OK"
    except Exception as e:
        err_msg = str(e)
        if "timeout" in err_msg.lower():
            return True, _("api_maybe_available")
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
    return os.path.join(_DATA_DIR, "records")

def normalize_parent_path(parent_path):
    parent_path = (parent_path or "").strip().strip('"').strip("'")
    if not parent_path:
        parent_path = get_default_records_parent()

    parent_path = os.path.expandvars(os.path.expanduser(parent_path))

    if not os.path.isabs(parent_path):
        first_part = parent_path.split(os.sep)[0].split("/")[0].lower()
        known_user_dirs = {"desktop", "documents", "downloads", "pictures", "videos", "music"}
        if first_part in known_user_dirs:
            parent_path = os.path.join(os.path.expanduser("~"), parent_path)
        else:
            parent_path = os.path.abspath(parent_path)

    return os.path.normpath(parent_path)

def create_records_dir(parent_path):
    parent_path = normalize_parent_path(parent_path)
    # 不再在用户输入的路径下强制创建 SnowBot 子目录，直接使用规范化后的路径
    records_dir = parent_path
    os.makedirs(records_dir, exist_ok=True)
    return records_dir

def collect_records_dir():
    print(f"\n{Colors.CYAN}=== {_('records_path_title')} ==={Colors.RESET}")
    print(f"{Colors.YELLOW}{_('records_path_hint')}{Colors.RESET}")
    print(f"{Colors.YELLOW}{_('records_path_auto_create')}{Colors.RESET}")
    print(f"{Colors.YELLOW}{_('records_path_default')} {get_default_records_parent()}{Colors.RESET}")

    while True:
        parent_path = input(f"{Colors.CYAN}{_('records_path_prompt')} {Colors.RESET}").strip()
        try:
            records_dir = create_records_dir(parent_path)
            print(f"{Colors.GREEN}{_('records_path_saved')} {records_dir}{Colors.RESET}")
            return records_dir
        except OSError as e:
            print(f"{Colors.RED}{_('records_path_create_fail')} {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}{_('records_path_try_another')}{Colors.RESET}")

def collect_login_records_dir(current_records_dir=None):
    print(f"\n{Colors.CYAN}=== {_('records_path_title')} ==={Colors.RESET}")
    print(f"{Colors.YELLOW}{_('records_path_hint')}{Colors.RESET}")
    print(f"{Colors.YELLOW}{_('records_path_new_hint')}{Colors.RESET}")
    if current_records_dir:
        print(f"{Colors.YELLOW}{_('records_path_last')} {current_records_dir}{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}{_('records_path_default')} {get_default_records_parent()}{Colors.RESET}")

    while True:
        parent_path = input(f"{Colors.CYAN}{_('records_path_prompt')} {Colors.RESET}").strip()
        try:
            if parent_path:
                records_dir = create_records_dir(parent_path)
            elif current_records_dir:
                records_dir = validate_records_dir(current_records_dir)
            else:
                records_dir = create_records_dir(parent_path)
            print(f"{Colors.GREEN}{_('records_path_saved')} {records_dir}{Colors.RESET}")
            return records_dir
        except OSError as e:
            print(f"{Colors.RED}{_('records_path_use_fail')} {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}{_('records_path_try_another')}{Colors.RESET}")
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
            print(f"{Colors.RED}{_('records_path_unavailable')} {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}{_('records_path_respecify')}{Colors.RESET}")
            users[username]["records_dir"] = collect_records_dir()
            save_users(users)

def get_user_records_dir(username):
    users = load_users()
    user_data = users.get(username, {})
    records_dir = user_data.get("records_dir")
    if not records_dir:
        records_dir = get_default_records_parent()
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

# ------ 模型选择 ------

def collect_model():
    print(f"\n{Colors.CYAN}=== {_('choose_model')} ==={Colors.RESET}")
    for code, config in MODELS.items():
        print(f"  {code}. {config['name']}")
    print()
    choice = input(f"{Colors.CYAN}>> {Colors.RESET}").strip()
    if choice in MODELS:
        return choice
    print(f"{Colors.YELLOW}{_('selected')} DeepSeek{Colors.RESET}")
    return "1"

# ------ 注册时收集设定 ------

def collect_settings():
    print(f"\n{Colors.CYAN}=== {_('set_your_ai')} ==={Colors.RESET}\n")
    
    name = input(f"{Colors.YELLOW}{_('ai_name')}: {Colors.RESET}").strip()
    if not name:
        name = "含霜"
    
    persona = input(f"{Colors.YELLOW}{_('persona')}: {Colors.RESET}").strip()
    if not persona:
        persona = "AI 助手"
    
    call_name = input(f"{Colors.YELLOW}{_('call_you')}: {Colors.RESET}").strip()
    if not call_name:
        call_name = "你"
    
    model_code = collect_model()
    model_name = MODELS[model_code]["name"]
    
    settings = {
        "name": name,
        "persona": persona,
        "call_name": call_name,
        "model": model_code,
        "model_name": model_name,
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

    records_dir = collect_records_dir()
    
    users[username] = {
        "password": hash_password(password),
        "api_key": "",
        "records_dir": records_dir
    }
    save_users(users)
    
    settings = collect_settings()
    save_settings(username, settings)
    
    return True, f"{Colors.GREEN}{_('register_success_detail')}\n{_('user_records_path')} {records_dir}{Colors.RESET}"

def login(username, password):
    users = load_users()
    if not username:
        return None, f"{Colors.RED}{_('empty_username')}{Colors.RESET}"
    if username not in users:
        return None, f"{Colors.RED}{_('user_not_exist')}{Colors.RESET}"
    if users[username]["password"] != hash_password(password):
        return None, f"{Colors.RED}{_('wrong_password')}{Colors.RESET}"
    ensure_login_records_dir(username, users)
    return users[username], f"{Colors.GREEN}{_('login_success')}{Colors.RESET}"

def init_api(username):
    users = load_users()
    user_data = users.get(username)
    if not user_data:
        return None, None
    api_key = user_data.get("api_key")
    if not api_key:
        return None, None
    settings = load_settings(username)
    model_code = settings.get("model", "1") if settings else "1"
    model_config = MODELS.get(model_code, MODELS["1"])
    client = OpenAI(api_key=api_key, base_url=model_config["base_url"])
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

def _call_api(messages, api_client, model_name):
    response = api_client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=False
    )
    return response.choices[0].message.content

def _submit_with_timeout(messages, api_client, model_name):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_call_api, messages, api_client, model_name)
    try:
        reply = future.result(timeout=API_TIMEOUT)
        executor.shutdown(wait=False)
        return reply, False
    except concurrent.futures.TimeoutError:
        executor.shutdown(wait=False)
        return None, True
    except Exception as e:
        executor.shutdown(wait=False)
        return f"[{_('error')}] {e}", False

# ------ 对话函数 ------

def chat(user_msg, memories, client, system_prompt, model_name):
    messages = [{"role": "system", "content": system_prompt}]
    for h_user, h_assistant in memories:
        messages.append({"role": "user", "content": h_user})
        messages.append({"role": "assistant", "content": h_assistant})
    messages.append({"role": "user", "content": user_msg})
    
    print(f"{Colors.CYAN}{_('thinking')}{Colors.RESET}")
    assistant_reply, timed_out = _submit_with_timeout(messages, client, model_name)
    
    if timed_out:
        print(f"{Colors.RED}{_('timeout_msg')}{Colors.RESET}")
        return None
    if assistant_reply is None:
        print(f"{Colors.RED}{_('empty_response')}{Colors.RESET}")
        return None
    
    return assistant_reply

# ------ 界面函数 ------

def print_header(title):
    width = 50
    # 剥离 ANSI 转义码后计算可见长度，避免颜色码导致居中偏移
    visible_len = len(re.sub(r"\033\[[0-9;]*m", "", str(title)))
    pad = max(0, (width - visible_len) // 2)
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * width}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{' ' * pad}{title}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * width}{Colors.RESET}")
    print()

def print_menu(options, title="菜单"):
    print(f"{Colors.YELLOW}{Colors.BOLD}{title}{Colors.RESET}")
    for opt in options:
        print(f"  {Colors.CYAN}*{Colors.RESET} {opt}")
    print()

def print_error(msg):
    print(f"{Colors.RED}{_('error')}: {msg}{Colors.RESET}\n")

def print_success(msg):
    print(f"{Colors.GREEN}{msg}{Colors.RESET}\n")

def print_info(msg):
    print(f"{Colors.BLUE}{_('info')}: {msg}{Colors.RESET}\n")

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
            # 单个 word 超过宽度（常见于无空格的中文段落），按字符强制换行
            if len(word) > width:
                for ch in word:
                    if len(line) + 1 > width:
                        if line:
                            print(f"  {line}")
                        line = ""
                    line += ch
                continue
            if len(line) + len(word) + 1 > width:
                if line:
                    print(f"  {line}")
                line = word
            else:
                line = (line + " " + word) if line else word
        if line:
            print(f"  {line}")


def read_chat_message():
    if os.name != "nt":
        return input(f"{Colors.YELLOW}{_('user')}>{Colors.RESET} ").strip()

    import ctypes

    STD_INPUT_HANDLE = -10
    KEY_EVENT = 0x0001
    VK_RETURN = 0x0D
    VK_BACK = 0x08
    LEFT_CTRL_PRESSED = 0x0008
    RIGHT_CTRL_PRESSED = 0x0004

    class KEY_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("bKeyDown", ctypes.c_int),
            ("wRepeatCount", ctypes.c_ushort),
            ("wVirtualKeyCode", ctypes.c_ushort),
            ("wVirtualScanCode", ctypes.c_ushort),
            ("uChar", ctypes.c_wchar),
            ("dwControlKeyState", ctypes.c_uint),
        ]

    class INPUT_EVENT(ctypes.Union):
        _fields_ = [("KeyEvent", KEY_EVENT_RECORD)]

    class INPUT_RECORD(ctypes.Structure):
        _fields_ = [
            ("EventType", ctypes.c_ushort),
            ("Event", INPUT_EVENT),
        ]

    kernel32 = ctypes.windll.kernel32
    # 64 位 Windows 上 HANDLE 是 8 字节，必须声明返回类型，否则按 c_int 截断
    kernel32.GetStdHandle.restype = ctypes.c_void_p
    kernel32.GetStdHandle.argtypes = [ctypes.c_uint]
    kernel32.ReadConsoleInputW.restype = ctypes.c_int
    kernel32.ReadConsoleInputW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(INPUT_RECORD),
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_uint),
    ]
    input_handle = kernel32.GetStdHandle(STD_INPUT_HANDLE)
    record = INPUT_RECORD()
    read_count = ctypes.c_uint(0)
    message = []

    print(f"{Colors.YELLOW}{_('user')}>{Colors.RESET} ", end="", flush=True)

    while True:
        ok = kernel32.ReadConsoleInputW(input_handle, ctypes.byref(record), 1, ctypes.byref(read_count))
        if not ok or record.EventType != KEY_EVENT:
            continue

        key = record.Event.KeyEvent
        if not key.bKeyDown:
            continue

        ctrl_pressed = key.dwControlKeyState & (LEFT_CTRL_PRESSED | RIGHT_CTRL_PRESSED)

        for repeat_index in range(max(1, key.wRepeatCount)):
            if key.wVirtualKeyCode == VK_RETURN:
                if ctrl_pressed:
                    print()
                    return "".join(message).strip()
                message.append("\n")
                print()
                continue

            if key.wVirtualKeyCode == VK_BACK:
                if message:
                    last = message.pop()
                    if last != "\n":
                        print("\b \b", end="", flush=True)
                continue

            char = key.uChar
            if char and ord(char) >= 32:
                message.append(char)
                print(char, end="", flush=True)

# ------ 主循环 ------

def main():
    migrate_legacy_data()
    load_language()
    print_header(f"{Colors.MAGENTA}含霜 SnowBot{Colors.RESET}")
    
    print_divider()
    
    while True:
        print_menu([_("login") + " (l)", _("register") + " (r)", _("language") + " (lg)", _("quit") + " (q)"], _("menu"))
        choice = input(f"{Colors.CYAN}>> {Colors.RESET}").strip().lower()

        if choice in ["login", "l", "1", _("login").lower()]:
            do_login()
        elif choice in ["register", "r", "2", _("register").lower()]:
            do_register()
        elif choice in ["language", "lg", "3", _("language").lower()]:
            do_language()
        elif choice in ["quit", "q", "4", "exit", _("quit").lower()]:
            print(f"{Colors.GREEN}{_('goodbye')}{Colors.RESET}")
            break
        else:
            print_error(_("invalid_choice"))

# ------ 语言模块 ------

def do_language():
    print_header(_("choose_language"))
    print(f"{Colors.CYAN}{_('choose_language')}:{Colors.RESET}\n")
    for code, name in LANGUAGES.items():
        print(f"  {code}. {name}")
    print()
    choice = input(f"{Colors.CYAN}>> {Colors.RESET}").strip()
    if choice in LANGUAGES:
        save_language(choice)
        print_success(f"{_('selected')}: {LANGUAGES[choice]}")
    else:
        print_error(_("invalid_choice"))

def do_login():
    print_header(_("login"))
    username = input(f"{Colors.CYAN}{_('username')}: {Colors.RESET}").strip()
    password = input(f"{Colors.CYAN}{_('password')}: {Colors.RESET}").strip()
    
    user_data, msg = login(username, password)
    if user_data is None:
        print_error(msg)
        return
    
    settings = load_settings(username)
    if not settings:
        print(f"{Colors.YELLOW}{_('not_found_settings')}{Colors.RESET}")
        if input(f"{Colors.YELLOW}{_('setting')} (y/n): {Colors.RESET}").strip().lower() == "y":
            settings = collect_settings()
            save_settings(username, settings)
        else:
            settings = {"name": "含霜", "persona": "AI 助手", "call_name": "你", "model": "1", "model_name": "DeepSeek"}
    
    model_code = settings.get("model", "1")
    model_config = MODELS.get(model_code, MODELS["1"])
    
    client, user_info = init_api(username)
    if client is None:
        print(f"{Colors.YELLOW}{_('not_set_api')}{Colors.RESET}")
        api_key = input(f"{Colors.CYAN}{_('api_key')} ({model_config['api_key_hint']}): {Colors.RESET}").strip()
        if api_key:
            print(f"{Colors.CYAN}{_('test_api')}...{Colors.RESET}")
            ok, result = check_api_status(api_key, model_code)
            if ok:
                users = load_users()
                users[username]["api_key"] = api_key
                save_users(users)
                client = OpenAI(api_key=api_key, base_url=model_config["base_url"])
                print_success(_("api_success"))
            else:
                print_error(f"{_('api_fail')}: {result}")
                return
        else:
            print_error(_("need_api"))
            return
    
    print_success(f"{_('welcome_back')}，{username}！")
    print_info(f"{_('current_model')}: {model_config['name']}")
    chat_loop(username, client, settings, model_config)

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
    
    settings = load_settings(username)
    model_code = settings.get("model", "1") if settings else "1"
    model_config = MODELS.get(model_code, MODELS["1"])
    
    print(f"\n{Colors.CYAN}{_('optional')}: {_('api_key')} ({model_config['api_key_hint']}){Colors.RESET}")
    api_key = input(f"{Colors.CYAN}{_('api_key')} ({_('skip')}): {Colors.RESET}").strip()
    if api_key:
        print(f"{Colors.CYAN}{_('test_api')}...{Colors.RESET}")
        ok, result = check_api_status(api_key, model_code)
        if ok:
            users = load_users()
            users[username]["api_key"] = api_key
            save_users(users)
            print_success(_("api_key_saved"))
        else:
            print_error(f"{_('api_fail')}: {result}")

def chat_loop(username, client, settings, model_config):
    memories = load_memories(username, limit=None)
    system_prompt = build_system_prompt(settings)
    
    ai_name = settings.get("name", "含霜")
    model_name = model_config["model_name"]
    
    print_header(f"{_('chat_label')} - {username}")
    print(f"--- {_('chat_history')} ({len(memories)} {_('count_records_unit')}) ---")
    print(f"--- {_('current_model')}: {model_config['name']} ---")
    
    for i, (u, a) in enumerate(memories):
        print(f"{Colors.CYAN}[{i+1}] {_('user')}:{Colors.RESET}")
        for line in u.split("\n"):
            print(f"  {line}")
        print(f"{Colors.MAGENTA}{ai_name}:{Colors.RESET}")
        for line in a.split("\n"):
            print(f"  {line}")
    print_divider()
    
    while True:
        user_msg = read_chat_message()
        
        if not user_msg:
            print(f"{Colors.YELLOW}{_('input_content')}{Colors.RESET}")
            continue
        
        if user_msg.lower() in ["logout", "exit", "quit"]:
            print(f"{Colors.CYAN}{_('exit_chat')}{Colors.RESET}")
            print_divider()
            return
        
        assistant_reply = chat(user_msg, memories, client, system_prompt, model_name)
        
        if assistant_reply:
            print(f"{Colors.MAGENTA}{ai_name}:{Colors.RESET}")
            format_output(assistant_reply)
            print()
            
            save_memories(username, [user_msg, assistant_reply])
            memories.append([user_msg, assistant_reply])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}{_('goodbye')}{Colors.RESET}")
    except EOFError:
        print(f"\n{Colors.CYAN}{_('goodbye')}{Colors.RESET}")
