import streamlit as st
from frontend.utils.speech_to_text import audio_to_text
from frontend.database.db_connector import save_chat_record
from frontend.models.get_llm import get_llm

def run():
    st.title("与客户互动 & 记录")

    # 上传语音文件
    audio_file = st.file_uploader("上传语音文件", type=["mp3", "wav", "flac"])

    if audio_file is not None:
        # 语音转换为文本
        customer_message = audio_to_text(audio_file)
        st.write(f"客户消息: {customer_message}")

    # 输入顾问消息
    advisor_message = st.text_area("顾问消息", "")

    if st.button("保存聊天记录"):
        # 生成对话摘要
        llm = get_llm()
        conversation = [{"role": "user", "content": customer_message}, {"role": "assistant", "content": advisor_message}]
        summary = llm(conversation)

        # 保存聊天记录和摘要到数据库
        save_chat_record(customer_message, advisor_message, summary)
        st.write("聊天记录已保存，摘要已生成并存储。")
        st.write(f"对话摘要: {summary}")
