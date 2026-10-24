import os
import sys
import hashlib
import json

# 颜色定义
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @staticmethod
    def init():
        """初始化 Windows 终端颜色支持"""
        if sys.platform == "win32":
            os.system('color')

def get_password_file_path(target_file):
    """获取密码文件路径，文件名基于目标文件的绝对路径"""
    abs_path = os.path.abspath(target_file)
    safe_name = abs_path.replace(':', '').replace('\\', '_').replace('/', '_')
    username = os.environ.get('USERNAME', os.environ.get('USER', 'default'))
    if sys.platform == "win32":
        base_dir = f"C:\\Users\\{username}\\AppData\\Roaming\\Shinlinst\\EternalLock"
    else:
        base_dir = os.path.expanduser("~/.config/Shinlinst/EternalLock")
    return os.path.join(base_dir, f"Lock{safe_name}.json")

def get_valid_file_path(prompt):
    """获取有效的文件路径，路径错误时重新输入"""
    while True:
        target_file = input(prompt).strip()
        if os.path.exists(target_file):
            return target_file
        print(f"{Colors.RED}❌ 找不到文件: {target_file}，请重新输入{Colors.END}")

def lock_file(target_file):
    """封印文件"""
    # 要求输入密码，直接回车则跳过
    password = input(f"{Colors.WHITE}请输入封印密码（直接回车则不需要密码）: {Colors.END}")

    if password:
        sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        password_file = get_password_file_path(target_file)
        os.makedirs(os.path.dirname(password_file), exist_ok=True)
        with open(password_file, 'w', encoding='utf-8') as f:
            json.dump({"sha256": sha256_hash}, f)
        print(f"{Colors.CYAN}🔒 密码已设置并储存到 {password_file}{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️ 未设置密码，文件将直接封印{Colors.END}")

    # 设置文件系统只读属性
    if sys.platform == "win32":
        os.system(f'attrib +R +S "{target_file}"')
        os.system(f'icacls "{target_file}" /deny Everyone:(W)')
    else:
        os.chmod(target_file, 0o444)
        os.system(f'chattr +i "{target_file}" 2>/dev/null')

    print(f"{Colors.GREEN}✅ 文件 {target_file} 已成功封印{Colors.END}")

def unlock_file(target_file):
    """解封文件"""
    password_file = get_password_file_path(target_file)

    if os.path.exists(password_file):
        with open(password_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        stored_hash = data.get("sha256", "")

        max_attempts = 3
        for attempt in range(max_attempts):
            password = input(f"{Colors.WHITE}请输入解封密码: {Colors.END}")
            input_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if input_hash == stored_hash:
                print(f"{Colors.GREEN}✅ 密码正确{Colors.END}")
                break
            else:
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    print(f"{Colors.RED}❌ 密码错误，还剩 {remaining} 次尝试{Colors.END}")
                else:
                    print(f"{Colors.RED}❌ 密码错误次数过多，解封失败{Colors.END}")
                    return
    else:
        print(f"{Colors.YELLOW}⚠️ 未检测到密码文件，无需密码直接解封{Colors.END}")

    # 移除文件系统只读属性
    if sys.platform == "win32":
        os.system(f'attrib -R -S "{target_file}"')
        os.system(f'icacls "{target_file}" /grant Everyone:(W)')
    else:
        os.chmod(target_file, 0o755)
        os.system(f'chattr -i "{target_file}" 2>/dev/null')

    print(f"{Colors.GREEN}✅ 文件 {target_file} 已成功解封{Colors.END}")

def main():
    Colors.init()

    while True:
        print(f"\n{Colors.CYAN}{'=' * 50}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}         文件保护工具{Colors.END}")
        print(f"{Colors.CYAN}{'=' * 50}{Colors.END}")
        print(f"{Colors.YELLOW}l{Colors.END} - {Colors.BLUE}封印文件{Colors.END}{Colors.WHITE}（设置为只读）{Colors.END}")
        print(f"{Colors.YELLOW}u{Colors.END} - {Colors.BLUE}解封文件{Colors.END}{Colors.WHITE}（恢复可读写）{Colors.END}")
        print(f"{Colors.YELLOW}q{Colors.END} - {Colors.BLUE}退出程序{Colors.END}")
        print(f"{Colors.CYAN}{'=' * 50}{Colors.END}")

        choice = input(f"{Colors.BOLD}请选择操作 (l/u/q): {Colors.END}").strip().lower()

        if choice == 'l':
            target_file = get_valid_file_path(f"{Colors.WHITE}请输入要封印的文件路径: {Colors.END}")
            lock_file(target_file)
        elif choice == 'u':
            target_file = get_valid_file_path(f"{Colors.WHITE}请输入要解封的文件路径: {Colors.END}")
            unlock_file(target_file)
        elif choice == 'q':
            print(f"{Colors.BLUE}👋 程序已退出{Colors.END}")
            break
        else:
            print(f"{Colors.RED}❌ 无效的选择，请输入 l、u 或 q{Colors.END}")

if __name__ == "__main__":
    main()