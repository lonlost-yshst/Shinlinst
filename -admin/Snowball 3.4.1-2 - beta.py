
# -------- 导入库 --------

import gradio as gr
from openai import OpenAI, APIConnectionError
import pickle
from Crypto.Cipher import AES
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

# ------ 加密模块 ------

MEMORY_KEY = b'Snowballsnowball'

MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memories")
os.makedirs(MEMORY_DIR, exist_ok=True)

def _next_memory_path():
    idx = 1
    while os.path.exists(os.path.join(MEMORY_DIR, f"encrypted_snowball{idx}.mem")):
        idx += 1
    return os.path.join(MEMORY_DIR, f"encrypted_snowball{idx}.mem")

def save_memories(turn):
    path = _next_memory_path()
    cipher = AES.new(MEMORY_KEY, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(pickle.dumps(turn))
    with open(path, "wb") as f:
        f.write(cipher.nonce)
        f.write(tag)
        f.write(ciphertext)

def load_memories():
    mems = []
    files = sorted(
        glob.glob(os.path.join(MEMORY_DIR, "encrypted_snowball*.mem")),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0].replace("encrypted_snowball", ""))
    )
    for path in files:
        try:
            with open(path, "rb") as f:
                nonce, tag, ciphertext = f.read(16), f.read(16), f.read()
                cipher = AES.new(MEMORY_KEY, AES.MODE_EAX, nonce)
                turn = pickle.loads(cipher.decrypt_and_verify(ciphertext, tag))
                mems.append(turn)
        except Exception:
            continue
    return mems

# ------ 对话函数 ------

def chat_with_cat(user_msg, history):
    if not user_msg.strip():
        return "", history

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
            assistant_reply += " 喵"
            
    except Exception as e:
        assistant_reply = f"[错误] {e}"
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": assistant_reply})
    save_memories([user_msg, assistant_reply])
    
    return "", history

# ------ Gradio 界面 ------

# 加载初始历史记录（使用字典格式）
initial_history = []
for h_user, h_assistant in load_memories():
    initial_history.append({"role": "user", "content": h_user})
    initial_history.append({"role": "assistant", "content": h_assistant})

with gr.Blocks(title="Snowball") as demo:
    gr.Markdown("# Snowball")
    chatbot = gr.Chatbot(height=600)
    with gr.Row():
        user_input = gr.Textbox(
            show_label=False,
            placeholder="和Snowball说点什么吧...",
            container=False,
            scale=7,
            max_lines=1                           # 单行输入
        )
        send_btn = gr.Button("发送", scale=1)

    send_btn.click(chat_with_cat, [user_input, chatbot], [user_input, chatbot])
    user_input.submit(chat_with_cat, [user_input, chatbot], [user_input, chatbot])

# ------ 启动 ------

if __name__ == "__main__":
    demo.launch()
