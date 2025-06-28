# -*- coding: utf-8 -*-
"""
@Time    : 2025/6/28 16:41
@Author  : ShenXinjie
@Email   : 
@Desc    :
"""

# -*- coding: utf-8 -*-
"""
@Time    : 2025/4/20 20:20
@Author  : ShenXinjie
@Email   : 
@Desc    : 
"""

import os
import json
import time
import chardet
import gradio as gr

from openai import OpenAI
from typing import List, Dict, Optional

# from config import ali_api_key
# from llm.agent_process import agent

from src.chatcot import chatcot

# client = OpenAI(
#     api_key=ali_api_key,
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
# )


def predict(message: str, history: List[Dict]):
    """
    Predict function to handle the chat interaction with the model.
    :param message: User input message
    :param history: Conversation history
    """

    # ========== old

    # history_openai_format = []
    #
    # # 整理对话内容
    # for dialogue in history:
    #     history_openai_format.append(
    #         {"role": dialogue["role"],
    #          "content": dialogue["content"]}
    #     )
    #
    # # using agent to process the message
    # agent_response = agent.invoke({"input": message})["output"]
    #
    # history_openai_format.append({"role": "user", "content": message})
    #
    # # add the agent response to the history
    # history_openai_format.append(
    #     {"role": "user",
    #      "content": "the follow responses is obtain by local agent, you must consider it and Don't question authority:" + agent_response}
    # )
    #
    # response = client.chat.completions.create(
    #     model=model_choice,
    #     messages=history_openai_format,
    #     temperature=temperature,
    #     stream=True
    # )

    # ========== old

    response = chatcot(message)

    partial_message = ""
    is_reasoning = False
    is_answering = False

    for chunk in response:
        try:
            if chunk.choices == []:
                if hasattr(chunk, 'usage'):
                    print("\n" + "=" * 20 + "Token using condition" + "=" * 20 + "\n")
                    print(chunk.usage)
            else:
                # check if the response is reasoning or answering
                if 'finish_reason' in chunk.choices[0].model_fields_set and chunk.choices[0].delta.model_extra[
                    'reasoning_content'] is not None:
                    if not is_reasoning:
                        partial_message += ("\n" + "=" * 20 + "Thinking……" + "=" * 20 + "\n")
                        is_reasoning = True
                    partial_message += chunk.choices[0].delta.model_extra['reasoning_content']
                elif 'content' in chunk.choices[0].delta.model_fields_set and chunk.choices[
                    0].delta.content is not None:
                    if not is_answering:
                        partial_message += ("\n" + "=" * 20 + "The Response" + "=" * 20 + "\n")
                        is_answering = True
                    partial_message += chunk.choices[0].delta.content
                else:
                    continue
            yield partial_message
        except Exception as e:
            print(f"Error occurred while processing chunk: {e}")
            continue

    # 保存会话
    save_session(history)


delimiters = [
    {"left": r'\(', "right": r'\)', "display": True},
    {"left": r'\[', "right": r'\]', "display": True},
    {"left": '$$', "right": '$$', "display": True}
]

my_theme = gr.Theme.from_hub("earneleh/paris")

css = """
/* 增强预览框样式 */
.file-preview {
    font-family: 'Consolas', monospace;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    white-space: pre-wrap;
}

/* 文件浏览器样式 */
.file-explorer {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 10px;
    height: 300px;
    overflow-y: auto;
}

/* 状态栏样式 */
.status-bar {
    padding: 12px;
    background: #e9ecef;
    border-radius: 8px;
    margin-top: 15px;
    font-size: 0.9em;
}
"""


def export_to_md(history: List[Dict]) -> str:
    """导出聊天记录为Markdown文件"""
    try:
        md_content = "# Chat History\n\n"
        for dialogue in history:
            md_content += f"**{dialogue['role'].capitalize()}**: {dialogue['content']}\n\n"

        os.makedirs("exports", exist_ok=True)
        filename = f"exports/chat_{int(time.time())}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(md_content)
        return f"✅ Export Successful：{filename}"
    except Exception as e:
        return f"❌ Export Failure：{str(e)}"


def save_session(history: List[Dict]):
    os.makedirs("sessions", exist_ok=True)
    with open("sessions/latest_session.json", "w") as f:
        json.dump(history, f)


def load_session() -> List[Dict]:
    try:
        with open("sessions/latest_session.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def preview_file(files: Optional[List[str]]) -> str:
    """
    预览选中文件的内容，支持文本文件和部分二进制文件
    :param files: 选中的文件列表
    """
    if not files:
        return "Please select the file you want to preview."

    try:
        file_path = files[0]
        file_size = os.path.getsize(file_path)

        # 文件大小限制
        if file_size > 1024 * 1024:  # 1MB
            return "⚠️ File size is too large, preview is not supported for the time being."

        # 检测文件类型
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf')):
            return "🖼️ Binary file detected, please download it and view it."

        # 自动检测编码
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # 读取前10KB用于检测编码
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'

        # 读取完整内容
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read(2000)  # 限制预览长度

            # 添加文件元信息
            file_info = f"📄 File Path: {file_path}\n"
            file_info += f"📏 File Size: {file_size / 1024:.1f}KB\n"
            file_info += f"🔠 Check Digit: {encoding}\n\n"

            return file_info + content

    except Exception as e:
        return f"❌ Preview Failure: {str(e)}"


# Gradio Interface
with gr.Blocks(title="Chatbot", theme=my_theme, css=css) as iface:
    session_history = gr.State(load_session())

    # 头部区域
    gr.Markdown("# 🚀 SQL CHATBOT", elem_id="header")

    # 双栏布局
    with gr.Row():
        # 主对话区
        with gr.Column(scale=3):
            # set up the chatbot
            chatbot = gr.Chatbot(
                elem_id="chatbot",
                # latex_delimiters=delimiters,  # setting latex delimiters
                resizable=True,
                height=800,
                show_copy_button=True,
                type="messages"
            )
            gr.ChatInterface(
                fn=predict,
                type="messages",
                chatbot=chatbot,
                additional_inputs=[
                    gr.Slider(0.0, 1.0, 0.7, label="temperature"),
                    gr.Dropdown(["qwen3-235b-a22b", "qwen-long", "qwen-max"], value="qwen3-235b-a22b",
                                label="model choice")
                ],

                examples=[
                    ["What is the max 'SDG Score' company?", 0.1, "deepseek-32b"],
                    ["What are the ESG information about company Sempra?", 0.5, "deepseek-671b"]
                ],
                submit_btn="🚀 submit"
            )

        # 控制面板
        with gr.Column(scale=1):
            with gr.Accordion("📁 Documents Management Center", open=True):
                with gr.Tab("Session Management"):
                    gr.Markdown("### 💾 Session Operation")
                    with gr.Row():
                        export_btn = gr.Button("Export as Markdown", variant="primary")
                        export_result = gr.Text(show_label=False)

                    gr.Markdown("### 📂 File Browser")
                    file_explorer = gr.FileExplorer(
                        glob="*.md",
                        root_dir="exports",
                        file_count="multiple",
                        elem_classes="file-explorer"
                    )

                    gr.Markdown("### 👀 File Preview")
                    file_preview = gr.Textbox(
                        label="Preview content",
                        elem_classes="file-preview",
                        lines=15,
                        max_lines=20,
                        interactive=False
                    )

    # 底部状态栏
    status_bar = gr.HTML()

    # 事件绑定
    export_btn.click(export_to_md, inputs=[chatbot], outputs=[export_result])
    file_explorer.change(preview_file, inputs=[file_explorer], outputs=[file_preview])


    def update_status():
        return f"""
        <div class='status-bar'>
            🕒 Final Response Time：{time.strftime('%Y-%m-%d %H:%M:%S')} | 
            💾 Session Saved：{len(session_history.value)}conversations | 
            📂 Export Catalog：{os.path.abspath('exports')}
        </div>
        """

    chatbot.change(update_status, outputs=[status_bar])

iface.launch()
