import streamlit as st
from utils.speech_to_text import audio_to_text
from database.db_connector import save_chat_record
from models.get_llm import get_llm
import time


def run():
    st.title("与客户互动 & 记录")

    # 初始化session_state，用于在页面刷新时保存状态
    if 'customer_message' not in st.session_state:
        st.session_state['customer_message'] = ""
    if 'advisor_message' not in st.session_state:
        st.session_state['advisor_message'] = ""

    # 上传语音文件
    audio_file = st.file_uploader("上传语音文件", type=["mp3", "wav", "flac"])

    if audio_file is not None:
        # 语音转换为文本
        try:
            customer_message = audio_to_text(audio_file)
            st.session_state['customer_message'] = customer_message
            st.write(f"客户消息: {customer_message}")
            
            # 语音转换成功后，自动填充对应的顾问消息
            # 这里使用一个基于客户消息的简单示例回复
            st.session_state['advisor_message'] = "感谢您的咨询。基于您提供的信息，我建议..."
            st.write("已自动填充顾问消息模板，请根据实际情况修改")
        except Exception as e:
            st.error(f"语音转换失败: {e}")
            # 语音转换失败时，从session_state中获取或使用默认值
            st.session_state['customer_message'] = st.text_area("手动输入客户消息",
                                                                st.session_state['customer_message'])
    else:
        # 从session_state中获取当前值并显示在文本框中
        st.session_state['customer_message'] = st.text_area("客户消息", st.session_state['customer_message'])

    # 从session_state中获取当前值并显示在文本框中
    st.session_state['advisor_message'] = st.text_area("顾问消息", st.session_state['advisor_message'])

    # 添加一个示例按钮，帮助用户理解正确的格式
    if st.button("填充示例数据"):
        # 填充示例客户消息和顾问消息到session_state
        st.session_state['customer_message'] = "我有50万的积蓄，想进行投资，但不知道该如何分配。我希望在保证本金安全的前提下，获得一定的收益。"
        st.session_state[
            'advisor_message'] = "根据您的情况，我建议采用稳健型投资策略。我们可以将资金分为三部分：60%配置在低风险产品如债券基金和定期存款，30%配置在中等风险产品如混合型基金，10%配置在高风险产品如股票型基金，这样既保证了本金安全，又能获得一定的收益。"
        st.success("示例数据已填充到输入框中！")
        # 使用rerun强制刷新页面，使数据立即显示在输入框中
        st.rerun()

    if st.button("保存聊天记录"):
        # 从session_state中获取当前的消息内容
        customer_message = st.session_state['customer_message']
        advisor_message = st.session_state['advisor_message']

        if not customer_message.strip() or not advisor_message.strip():
            st.warning("请确保填写了客户消息和顾问消息！")
        else:
            try:
                # 显示加载状态
                with st.spinner('正在生成对话摘要并保存记录...'):
                    # 模拟生成摘要（避免每次都调用OpenAI API）
                    # 在实际使用时，取消下面的注释并使用真实的LLM调用

                    # llm = get_llm()
                    # conversation = [{"role": "user", "content": customer_message}, {"role": "assistant", "content": advisor_message}]
                    # summary = llm(conversation)

                    # 模拟摘要，实际使用时请删除这部分
                    # 根据实际内容生成更贴合的摘要
                    summary = f"客户咨询投资配置问题，希望在保证本金安全的前提下获得收益。顾问提供了详细的投资策略建议。"
                    time.sleep(1)  # 模拟处理时间

                    # 保存聊天记录和摘要到数据库
                    save_chat_record(customer_message, advisor_message, summary)

                    st.success("聊天记录已保存，摘要已生成并存储。")
                    st.write(f"对话摘要: {summary}")

                    # 显示保存的记录示例格式
                    st.subheader("保存的记录格式：")
                    st.json({
                        "customer_message": customer_message,
                        "advisor_message": advisor_message,
                        "summary": summary
                    })
            except Exception as e:
                st.error(f"保存过程中发生错误: {e}")

    # 显示使用说明
    with st.expander("使用指南"):
        st.markdown("""
        ### 如何正确保存聊天记录

        1. **填写客户消息**：
           - 可以通过上传语音文件自动转换
           - 也可以直接在文本框中手动输入

        2. **填写顾问消息**：
           - 在顾问消息文本框中输入您的回复

        3. **保存记录**：
           - 点击"保存聊天记录"按钮
           - 系统会生成对话摘要并保存所有信息到数据库

        ### 正确的记录样例
        - **客户消息**：包含客户的问题、需求或情况描述
        - **顾问消息**：包含您作为顾问的专业建议或回复
        - **摘要**：系统自动生成的对话核心内容总结

        点击"填充示例数据"按钮可以查看一个完整的示例。
        """)

# import streamlit as st
# from utils.speech_to_text import audio_to_text
# from database.db_connector import save_chat_record
# from models.get_llm import get_llm
# import time
#
# def run():
#     st.title("与客户互动 & 记录")
#
#     # 初始化session_state，用于在页面刷新时保存状态
#     if 'customer_message' not in st.session_state:
#         st.session_state['customer_message'] = ""
#     if 'advisor_message' not in st.session_state:
#         st.session_state['advisor_message'] = ""
#
#     # 上传语音文件
#     audio_file = st.file_uploader("上传语音文件", type=["mp3", "wav", "flac"])
#
#     if audio_file is not None:
#         # 语音转换为文本
#         try:
#             customer_message = audio_to_text(audio_file)
#             st.session_state['customer_message'] = customer_message
#             st.write(f"客户消息: {customer_message}")
#         except Exception as e:
#             st.error(f"语音转换失败: {e}")
#             # 语音转换失败时，从session_state中获取或使用默认值
#             st.session_state['customer_message'] = st.text_area("手动输入客户消息", st.session_state['customer_message'])
#     else:
#         # 从session_state中获取当前值并显示在文本框中
#         st.session_state['customer_message'] = st.text_area("客户消息", st.session_state['customer_message'])
#
#     # 从session_state中获取当前值并显示在文本框中
#     st.session_state['advisor_message'] = st.text_area("顾问消息", st.session_state['advisor_message'])
#
#     # 添加一个示例按钮，帮助用户理解正确的格式
#     if st.button("填充示例数据"):
#         # 填充示例客户消息和顾问消息到session_state
#         st.session_state['customer_message'] = "我有50万的积蓄，想进行投资，但不知道该如何分配。我希望在保证本金安全的前提下，获得一定的收益。"
#         st.session_state['advisor_message'] = "根据您的情况，我建议采用稳健型投资策略。我们可以将资金分为三部分：60%配置在低风险产品如债券基金和定期存款，30%配置在中等风险产品如混合型基金，10%配置在高风险产品如股票型基金，这样既保证了本金安全，又能获得一定的收益。"
#         st.success("示例数据已填充到输入框中！")
#         # 使用rerun强制刷新页面，使数据立即显示在输入框中
#         st.rerun()
#
#     if st.button("保存聊天记录"):
#         # 从session_state中获取当前的消息内容
#         customer_message = st.session_state['customer_message']
#         advisor_message = st.session_state['advisor_message']
#
#         if not customer_message.strip() or not advisor_message.strip():
#             st.warning("请确保填写了客户消息和顾问消息！")
#         else:
#             try:
#                 # 显示加载状态
#                 with st.spinner('正在生成对话摘要并保存记录...'):
#                     # 模拟生成摘要（避免每次都调用OpenAI API）
#                     # 在实际使用时，取消下面的注释并使用真实的LLM调用
#
#                     # llm = get_llm()
#                     # conversation = [{"role": "user", "content": customer_message}, {"role": "assistant", "content": advisor_message}]
#                     # summary = llm(conversation)
#
#                     # 模拟摘要，实际使用时请删除这部分
#                     # 根据实际内容生成更贴合的摘要
#                     summary = f"客户咨询投资配置问题，希望在保证本金安全的前提下获得收益。顾问提供了详细的投资策略建议。"
#                     time.sleep(1)  # 模拟处理时间
#
#                     # 保存聊天记录和摘要到数据库
#                     save_chat_record(customer_message, advisor_message, summary)
#
#                     st.success("聊天记录已保存，摘要已生成并存储。")
#                     st.write(f"对话摘要: {summary}")
#
#                     # 显示保存的记录示例格式
#                     st.subheader("保存的记录格式：")
#                     st.json({
#                         "customer_message": customer_message,
#                         "advisor_message": advisor_message,
#                         "summary": summary
#                     })
#             except Exception as e:
#                 st.error(f"保存过程中发生错误: {e}")
#
#     # 显示使用说明
#     with st.expander("使用指南"):
#         st.markdown("""
#         ### 如何正确保存聊天记录
#
#         1. **填写客户消息**：
#            - 可以通过上传语音文件自动转换
#            - 也可以直接在文本框中手动输入
#
#         2. **填写顾问消息**：
#            - 在顾问消息文本框中输入您的回复
#
#         3. **保存记录**：
#            - 点击"保存聊天记录"按钮
#            - 系统会生成对话摘要并保存所有信息到数据库
#
#         ### 正确的记录样例
#         - **客户消息**：包含客户的问题、需求或情况描述
#         - **顾问消息**：包含您作为顾问的专业建议或回复
#         - **摘要**：系统自动生成的对话核心内容总结
#
#         点击"填充示例数据"按钮可以查看一个完整的示例。
#         """)
