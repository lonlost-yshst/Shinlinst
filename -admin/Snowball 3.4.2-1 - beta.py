
# -------- 导入库 --------

import gradio as gr
from openai import OpenAI
import json
import os
import glob

# ------ 初始化客户端 ------

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    with open(os.path.join(_BASE_DIR, "api_key.txt"), "r") as f:
        api_key = f.read().strip()
except FileNotFoundError:
    raise SystemExit("❌ 找不到 api_key.txt，请在脚本同目录下创建该文件并填入 API 密钥。")

client = OpenAI(
    api_key=api_key,
    base_url=os.environ.get('OPENAI_BASE_URL', 'https://api.deepseek.com')
)

# ------ 系统人设 ------

system_prompt = (
    "你是一只高傲冷艳的猫，是猫中最高贵的品种，"
    "你不太想搭理人类，回答问题很敷衍，并且总在句尾加上'喵'。"
    "你的名字叫Snowball。"
)

# ------ 记忆模块------

MEMORY_DIR = os.path.join(_BASE_DIR, "memories")
os.makedirs(MEMORY_DIR, exist_ok=True)

def _next_memory_path():
    idx = 1
    while os.path.exists(os.path.join(MEMORY_DIR, f"Snowballmem{idx}.json")):
        idx += 1
    return os.path.join(MEMORY_DIR, f"Snowballmem{idx}.json")

def save_memories(turn):
    path = _next_memory_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"user": turn[0], "assistant": turn[1]}, f, ensure_ascii=False, indent=2)

def load_memories():
    mems = []
    files = sorted(
        glob.glob(os.path.join(MEMORY_DIR, "Snowballmem*.json")),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0].replace("Snowballmem", ""))
    )
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                mems.append([data["user"], data["assistant"]])
        except Exception:
            continue
    return mems

# ------ 对话函数 ------

def chat_with_cat(user_msg, history):
    if not user_msg.strip():
        return "", history, gr.update(visible=True)

    memories = load_memories()
    messages = [{"role": "system", "content": system_prompt}]

    for h_user, h_assistant in memories:
        messages.append({"role": "user", "content": h_user})
        messages.append({"role": "assistant", "content": h_assistant})

    messages.append({"role": "user", "content": user_msg})

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        assistant_reply = response.choices[0].message.content

        # 强制添加猫语后缀（如果还没有）
        if not assistant_reply.endswith("喵"):
            assistant_reply += "喵"

    except Exception as e:
        assistant_reply = f"[错误] {e}"

    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": assistant_reply})
    save_memories([user_msg, assistant_reply])

    return "", history, gr.update(visible=False)

# ------ 特殊动作按钮 ------

def feed_fish(history):
    _, new_history, _ = chat_with_cat("（你给Snowball喂了一条鱼）", history)
    return new_history

def pat_head(history):
    _, new_history, _ = chat_with_cat("（你轻轻摸了摸Snowball的头）", history)
    return new_history

# ------ Gradio 界面 ------

# 加载初始历史记录
initial_history = []
for h_user, h_assistant in load_memories():
    initial_history.append({"role": "user", "content": h_user})
    initial_history.append({"role": "assistant", "content": h_assistant})

# ------ 空消息提示框 ------
with gr.Column(visible=False) as empty_warning:
    gr.Markdown("### ⚠️ 无法发送空消息")
    confirm_btn = gr.Button("确定")

with gr.Blocks(title="Snowball") as demo:
    gr.Markdown("# 🐱 Snowball")
    chatbot = gr.Chatbot(height=600, value=initial_history)
    with gr.Row():
        user_input = gr.Textbox(
            show_label=False,
            placeholder="和Snowball说点什么吧...",
            container=False,
            scale=7,
            max_lines=1
        )
        send_btn = gr.Button("发送", scale=1)
    with gr.Row():
        fish_btn = gr.Button("🐟 喂鱼")
        pat_btn  = gr.Button("🤚 摸头")

    send_btn.click(chat_with_cat, [user_input, chatbot], [user_input, chatbot, empty_warning])
    user_input.submit(chat_with_cat, [user_input, chatbot], [user_input, chatbot, empty_warning])
    fish_btn.click(feed_fish, [chatbot], [chatbot])
    pat_btn.click(pat_head, [chatbot], [chatbot])
    confirm_btn.click(lambda: gr.update(visible=False), outputs=[empty_warning])

# ------ 启动 ------

if __name__ == "__main__":
    demo.launch()
