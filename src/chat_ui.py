# -*- coding: utf-8 -*-
"""
@Time    : 2025/6/28 16:41
@Author  : ShenXinjie
@Email   : 
@Desc    : Enhanced UI with full conversation history display
"""

import os
import json
import time
import chardet
import gradio as gr

from typing import List, Dict, Optional, Tuple, Any
from chatcot import chatcot

# ===== Load settings =====
my_theme = gr.themes.Glass()

delimiters = [
    {"left": r'\(', "right": r'\)', "display": True},
    {"left": r'\[', "right": r'\]', "display": True},
    {"left": '$$', "right": '$$', "display": True}
]

css = """
#header {
    background: linear-gradient(90deg, #2c3e50, #4a69bd);
    color: white;
    padding: 15px 25px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.gr-row, .gr-column {
    gap: 15px !important;
}

.accordion-section {
    background: #2d3436;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.button-group {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

button {
    transition: all 0.2s ease !important;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

button:active {
    transform: translateY(1px);
}

.file-preview {
    background: #1e272e;
    border-radius: 6px;
    padding: 12px;
}

label, .text-md {
    color: #ecf0f1 !important;
}

.full-history {
    background: #1e2b38;
    padding: 15px;
    border-radius: 8px;
    max-height: 600px;
    overflow-y: auto;
    margin-top: 20px;
}

.message-user { color: #64b5f6; }
.message-assistant { color: #81c784; }
.message-system { color: #ffb74d; }
.message-tool { color: #ff8a65; }
.message-error { color: #e57373; }
"""


def predict(message: str, history: List[Tuple[str, str]]):
    # Initialize response content
    response_content = ""
    step_markers = {}  # Track step markers
    seen_content = set()  # Track processed content to avoid duplicates

    # Create base history
    if history and history[-1][1] is None:
        # If assistant placeholder exists, extract user message as base
        user_msg = history[-1][0]
        base_history = history[:-1]
    else:
        user_msg = message
        base_history = history.copy()

    # Initialize new history
    new_history = base_history + [(user_msg, response_content)]

    # Call chatcot generator
    for chunk in chatcot(message):
        try:
            content = chunk["content"]
            step = chunk.get("step", 0)
            msg_type = chunk["type"]

            # Check for duplicate content - especially for JSON formula blocks
            if content.strip() in seen_content:
                continue  # Skip duplicate content
            seen_content.add(content.strip())

            # Handle different message types
            if msg_type == "reasoning":
                response_content += content
            elif msg_type in ["action", "result", "error", "final"]:
                # Add message type icon
                icon = {
                    "action": "⚡",
                    "result": "📊",
                    "error": "❌",
                    "final": "✅"
                }.get(msg_type, "")

                # Add step marker
                if step != step_markers.get("current_step"):
                    step_markers["current_step"] = step
                    response_content += f"\n{'=' * 20} Step {step} {'=' * 20}\n\n"

                # Add content (auto-format JSON structure)
                formatted_content = content
                if content.strip().startswith("{"):
                    try:
                        json_content = json.loads(content)
                        formatted_content = json.dumps(json_content, indent=2)
                    except:
                        pass

                response_content += f"{icon} {formatted_content}\n"

                # For final messages
                if msg_type == "final":
                    response_content += f"\n{'=' * 20} Final Answer {'=' * 20}\n{formatted_content}"

            # Update assistant message content
            new_history = base_history + [(user_msg, response_content)]
            yield new_history

        except Exception as e:
            print(f"Error processing chunk: {e}")
            continue

def convert_to_chat_history_format(messages: List[Dict[str, str]]) -> List[Tuple[str, str]]:
    """Convert message format back to gradio history format"""
    history = []
    for msg in messages:
        if msg["role"] == "user":
            user_msg = msg["content"]
        elif msg["role"] == "assistant":
            assistant_msg = msg["content"]
            if user_msg:  # Ensure corresponding user message exists
                history.append((user_msg, assistant_msg))
                user_msg = None
    return history


def export_to_md(history: List[Tuple[str, str]]) -> str:
    try:
        md_content = "# Chat History\n\n"
        for user, assistant in history:
            md_content += f"**User**: {user}\n"
            md_content += f"**Assistant**: {assistant}\n\n"

        os.makedirs("../exports", exist_ok=True)
        filename = f"../exports/chat_{int(time.time())}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(md_content)
        return f"✅ Export successful: {filename}"
    except Exception as e:
        return f"❌ Export failed: {str(e)}"


def get_full_history(history: List[Tuple[str, str]]) -> List[Dict[str, str]]:
    """Load complete conversation history"""
    try:
        with open("chat_history.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        # If full history not available, reconstruct from chat history
        messages = []
        for user, assistant in history:
            messages.append({"role": "user", "content": user})
            messages.append({"role": "assistant", "content": assistant})
        return messages


def export_full_history(history: List[Tuple[str, str]]) -> str:
    """Export the full conversation history"""
    try:
        full_history = get_full_history(history)
        os.makedirs("../exports", exist_ok=True)
        filename = f"../exports/full_history_{int(time.time())}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(full_history, f, indent=2, ensure_ascii=False)

        return f"✅ Full history exported: {filename}"
    except Exception as e:
        return f"❌ Export failed: {str(e)}"


def preview_file(files: Optional[List[str]]) -> str:
    """
    Preview the contents of selected files (text files and certain binary files)
    :param files: List of selected files
    """
    if not files:
        return "Please select the file you want to preview."

    try:
        file_path = files[0]
        file_size = os.path.getsize(file_path)

        # File size limit
        if file_size > 1024 * 1024:  # 1MB
            return "⚠️ File size is too large, preview not supported."

        # Detect file types
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf')):
            return "🖼️ Binary file detected, please download and view externally."

        # Automatic encoding detection
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB for encoding detection
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'

        # Read full content
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read(2000)

            # Add file metadata
            file_info = f"📄 File Path: {file_path}\n"
            file_info += f"📏 File Size: {file_size / 1024:.1f}KB\n"
            file_info += f"🔠 Detected Encoding: {encoding}\n\n"

            return file_info + content

    except Exception as e:
        return f"❌ Preview failed: {str(e)}"


def format_full_history(history: List[Tuple[str, str]]) -> str:
    """Format full history for display with color coding"""
    full_history = get_full_history(history)
    formatted = []
    for entry in full_history:
        role = entry.get('role', 'assistant')
        content = entry.get('content', '')

        # Apply color classes based on role
        if role == 'user':
            formatted.append(f'<div class="message-user"><strong>User:</strong> {content}</div>')
        elif role == 'assistant':
            formatted.append(f'<div class="message-assistant"><strong>Assistant:</strong> {content}</div>')
        elif role == 'system':
            formatted.append(f'<div class="message-system"><strong>System:</strong> {content}</div>')
        elif role == 'tool':
            formatted.append(f'<div class="message-tool"><strong>Tool:</strong> {content}</div>')
        else:
            formatted.append(f'<div><strong>{role.capitalize()}:</strong> {content}</div>')

    return "\n\n".join(formatted)


def user_message(message: str, history: List[Tuple[str, str]]) -> tuple:
    # Add user message and create assistant placeholder
    return "", history + [(message, None)], message


# Gradio Interface
with gr.Blocks(title="Chatbot", theme=my_theme, css=css) as iface:
    # Initialize state with chat history in tuples format for Chatbot
    initial_history = []
    chat_history_state = gr.State(value=convert_to_chat_history_format(initial_history))
    current_user_message = gr.State("")

    gr.Markdown(
        "# 🚀 Enhanced LLM Reasoning: ChatCoT: a new chain-of-thought (CoT) prompting framework based on multi-turn conversations",
        elem_id="header")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                value=convert_to_chat_history_format(initial_history),
                elem_id="chatbot",
                show_label=False,
                resizable=True,
                height=600,
                show_copy_button=True,
                container=False,
            )

            with gr.Row():
                msg = gr.Textbox(
                    label="Input",
                    placeholder="Enter your message here...",
                    show_label=False,
                    container=False,
                    scale=7,
                )
                submit_btn = gr.Button("🚀 Submit", variant="primary", scale=1)

            gr.Examples(
                examples=[
                    ["What is one plus one?"],
                    ["List all products with their prices"]
                ],
                inputs=[msg],
                label="Example inputs"
            )

            # Full history section
            gr.Markdown("## 📜 Full Conversation History")
            full_history_display = gr.HTML(
                "<div style='color:#aaa;padding:20px;text-align:center;'>Click 🔃 Refresh History to view full conversation</div>",
                elem_classes="full-history",
                label="Complete conversation flow"
            )
            refresh_history_btn = gr.Button("🔄 Refresh History", variant="secondary")

        # Control panel
        with gr.Column(scale=1):
            with gr.Accordion("📁 Documents & Tools", open=True):
                with gr.Tab("Session Management"):
                    gr.Markdown("### 💾 Session Operations")
                    with gr.Row():
                        export_btn = gr.Button("💾 Export as Markdown", variant="primary")
                        export_full_btn = gr.Button("📂 Export Full History", variant="primary")
                        export_result = gr.Text(show_label=False)

                    gr.Markdown("### 📂 File Browser")
                    file_explorer = gr.FileExplorer(
                        glob="*.md",
                        root_dir="../exports",
                        file_count="multiple",
                        elem_classes="file-explorer",
                        height=200
                    )

                    gr.Markdown("### 👀 File Preview")
                    file_preview = gr.Code(
                        label="Preview content",
                        elem_classes="file-preview",
                        lines=25,
                        language="markdown"
                    )

    # Bottom status bar
    status_bar = gr.HTML()

    # Event bindings
    submit_event = submit_btn.click(
        fn=user_message,
        inputs=[msg, chat_history_state],
        outputs=[msg, chatbot, current_user_message],  # Add output to message state
        queue=False
    ).then(
        fn=predict,
        inputs=[current_user_message, chatbot],  # Use saved message
        outputs=[chatbot]
    ).then(
        lambda x: x,
        inputs=[chatbot],
        outputs=[chat_history_state],
        queue=False
    )

    # Export buttons
    export_btn.click(export_to_md, inputs=[chatbot], outputs=[export_result])
    export_full_btn.click(export_full_history, inputs=[chatbot], outputs=[export_result])
    file_explorer.change(preview_file, inputs=[file_explorer], outputs=[file_preview])
    refresh_history_btn.click(fn=format_full_history, inputs=[chat_history_state], outputs=[full_history_display])


    def update_status():
        try:
            history_length = len(chat_history_state.value)
        except:
            history_length = 0

        return f"""
        <div class='status-bar'>
            🕒 Current Time: {time.strftime('%Y-%m-%d %H:%M:%S')} | 
            💾 Session Saved: {history_length} conversations | 
            📂 Export Directory: {os.path.abspath('../exports') if os.path.exists('../exports') else 'Not Found'}
        </div>
        """


    iface.load(update_status, outputs=[status_bar])  # Initialize the interface
    chatbot.change(update_status, outputs=[status_bar])  # Update status bar after conversation

iface.launch()