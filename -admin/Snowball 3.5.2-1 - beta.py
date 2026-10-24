# -------- 导入库 --------

from openai import OpenAI
import json
import os
import concurrent.futures

# ------ 初始化客户端 ------

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_URL  = os.environ.get('OPENAI_BASE_URL', 'https://api.deepseek.com')

# 主 API
try:
    with open(os.path.join(_BASE_DIR, "api_key.txt"), "r") as f:
        api_key = f.read().strip()
except FileNotFoundError:
    raise SystemExit("❌ 找不到 api_key.txt，请在脚本同目录下创建该文件并填入主 API 密钥。")

# 备用 API（找不到文件则禁用备用功能）
try:
    with open(os.path.join(_BASE_DIR, "api_key_backup.txt"), "r") as f:
        api_key_backup = f.read().strip()
except FileNotFoundError:
    api_key_backup = None

client        = OpenAI(api_key=api_key,        base_url=_BASE_URL)
client_backup = OpenAI(api_key=api_key_backup, base_url=_BASE_URL) if api_key_backup else None

# ------ 系统人设 ------

system_prompt = (
    "你是一个高效直接的猫娘机器人，"
    "你说话总在句尾加上'喵'，"
    "你的名字叫Snowball，"
    "你会叫我Master。"
)

# ------ 记忆模块------
MEMORY_FILE = os.path.join(_BASE_DIR, "Snowballmemories.json")

def save_memories(turn):
    """追加单轮对话到文件"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memories = json.load(f)
        except json.JSONDecodeError:
            memories = []
    else:
        memories = []
    
    # 追加新对话
    memories.append({"user": turn[0], "assistant": turn[1]})
    
    # 保存
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)


def load_memories(limit=None):
    if not os.path.exists(MEMORY_FILE):
        return []
    
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_memories = [[item["user"], item["assistant"]] for item in data]
            
            # 限制返回条数
            if limit and isinstance(limit, int) and limit > 0:
                return all_memories[-limit:]  # 取最后N条
            return all_memories
    except (json.JSONDecodeError, KeyError):
        return []


# ------ API 调用 ------

API_TIMEOUT = 90  # 超时秒数

def _call_api(messages, api_client):
    response = api_client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
    return response.choices[0].message.content

def _submit_with_timeout(messages, api_client):
    """提交 API 调用，返回 (reply, timed_out)"""
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

def chat(user_msg, memories):
    messages = [{"role": "system", "content": system_prompt}]

    for h_user, h_assistant in memories:
        messages.append({"role": "user", "content": h_user})
        messages.append({"role": "assistant", "content": h_assistant})

    messages.append({"role": "user", "content": user_msg})

    # 尝试主 API
    assistant_reply, timed_out = _submit_with_timeout(messages, client)

    if timed_out:
        if client_backup:
            print("主API超时，正在切换备用API重试...")
            assistant_reply, timed_out = _submit_with_timeout(messages, client_backup)
            if timed_out:
                print("备用API也超时（超过90秒），本次对话未保存，请重试。")
                return None
        else:
            print("连接超时（超过90秒），本次对话未保存，请重试。")
            return None

    # 处理空回复
    if assistant_reply is None:
        print("API返回空响应，请重试。")
        return None

    return assistant_reply


# ------ 主循环 ------

def main():
    print("=" * 50)
    print("Snowball 3.5.2-1 - beta")
    print("输入 'exit' 或 'quit' 退出")
    print("=" * 50)
    print()

    # 加载记忆
    memories = load_memories(limit=5)
    print(f"已加载 {len(memories)} 条记忆:")
    for i, (u, a) in enumerate(memories):
        print(f"  [{i+1}] User: {u}")
        # 分段显示回复
        lines = a.split("\n")
        for line in lines:
            if line.strip():
                print(f"       {line}")
    print()

    while True:
        try:
            user_msg = input("User: ").strip()
        except EOFError:
            break

        if not user_msg:
            print("请输入内容\n")
            continue

        if user_msg.lower() in ["exit", "quit", "退出"]:
            print("再见喵~")
            break

        # 对话
        assistant_reply = chat(user_msg, memories)

        if assistant_reply:
            # 分段落输出
            print("Snowball:")
            # 按换行分段
            paragraphs = assistant_reply.split("\n")
            for para in paragraphs:
                if para.strip():
                    # 长行自动换行
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
            # 保存记忆
            save_memories([user_msg, assistant_reply])
            memories.append([user_msg, assistant_reply])
            # 只保留最近5条
            if len(memories) > 5:
                memories = memories[-5:]


if __name__ == "__main__":
    main()