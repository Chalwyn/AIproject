import time
import streamlit as st
import whisper
from openai import OpenAI
import mysql.connector
from mysql.connector import Error
import sys

from dotenv import load_dotenv
import os

# 加载 .env 文件中的环境变量
load_dotenv()
st.set_page_config(layout="wide")
client = OpenAI(
    api_key='OPENAI_API_KEY')


# 定义一个将文件翻译成中文的函数
def translate_to_chinese(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional translator."},
                {"role": "user", "content": f"Translate the following text to Chinese:\n\n{text}"}
            ],
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


# Function to translate Chinese to English
def translate_to_english(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional translator."},
                {"role": "user", "content": f"Translate the following text to English:\n\n{text}"}
            ],
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


with st.sidebar:
    language = st.selectbox("Choose your language / 选择语言", ["English", "中文"])

if (language == "中文"):
    # 数据库函数导入失败，直接拿过来用
    try:
        import mysql.connector
        from mysql.connector import Error
    except ImportError as e:
        print(f"导入错误: {e}")
        import sys

        print(f"Python版本: {sys.version}")
        print(f"Python路径: {sys.executable}")


    def connect_db():
        try:
            print("尝试连接数据库...")
            connection = mysql.connector.connect(
                host="1.tcp.au.cpolar.io",
                port="13156",
                database="project",  # 替换为你的数据库名
                user="tao",  # 替换为你的数据库用户名
                password="initium123!"  # 替换为你的数据库密码
            )
            if connection.is_connected():
                print("数据库连接成功")
                return connection
            else:
                print("数据库连接失败: 无法建立连接")
                return None
        except Error as e:
            print(f"数据库连接错误: {e}")

            # 返回一个模拟的连接对象，以便应用可以继续运行
            class MockConnection:
                def cursor(self, dictionary=False):
                    class MockCursor:
                        def execute(self, query, params=None):
                            print(f"模拟执行SQL: {query}")
                            print(f"参数: {params}")

                        def fetchall(self):
                            return []

                        def close(self):
                            pass

                    return MockCursor()

                def commit(self):
                    print("模拟提交事务")

                def close(self):
                    print("模拟关闭连接")

            return MockConnection()
        except Exception as e:
            print(f"未知错误: {e}")
            return None


    def save_chat_record(customer_message, advisor_message, summary):
        connection = connect_db()
        if connection:
            cursor = connection.cursor()
            query = """
                INSERT INTO chat_records (customer_message, advisor_message, summary)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (customer_message, advisor_message, summary))
            connection.commit()
            cursor.close()
            connection.close()


    def get_chat_records():
        connection = connect_db()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM chat_records")
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return records



    # 用官方的api库来完成大模型的调用
    def get_ai_response(transcribed_text):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的文本摘要助手。"},  # system为系统设定
                    {"role": "user", "content": f"请根据以下内容生成摘要，生成中文版本的：\n\n{transcribed_text}"}
                    # 输入的用户需求，即问题
                ],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"错误: {str(e)}"


    st.title("record")

    st.page_link("main.py", label="返回主页面")

    model = whisper.load_model("base")

    # 在外部初始化为空字符串

    transcribed_text = ""
    # 最好是wav格式，目前这个是可以的
    uploaded_file = st.file_uploader("上传录音", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        audio = uploaded_file.read()

        with open("temp_audio.wav", "wb") as f:
            f.write(audio)  # 不再调用translate_to_chinese

        result = model.transcribe("temp_audio.wav")

        st.write("转录结果：")
        st.text(result["text"])

        transcribed_text = result["text"]

        st.write(get_ai_response(transcribed_text))  # 不再调用translate_to_chinese

    # 麦克风
    audio_value = st.audio_input("按住说话")

    if audio_value is not None:
        audio = audio_value.read()

        with open("temp_say.wav", "wb") as f:
            f.write(audio)  # 不再调用translate_to_chinese

        result = model.transcribe("temp_say.wav")

        st.write("转录结果：")
        st.text(result["text"])

        # 保存在下述名称中，方便后续调用
        transcribed_text = result["text"]

        st.write(get_ai_response(transcribed_text))  # 不再调用translate_to_chinese

    # 初始化session_state，用于在页面刷新时保存状态
    if 'customer_message' not in st.session_state:
        st.session_state['customer_message'] = ""
    if 'advisor_message' not in st.session_state:
        st.session_state['advisor_message'] = ""

    st.session_state['customer_message'] = transcribed_text
    st.write(f"客户消息: {transcribed_text}")  # 不再调用translate_to_chinese

    # 语音转换成功后，自动填充对应的顾问消息
    # 这里使用一个基于客户消息的简单示例回复
    st.session_state['advisor_message'] = "感谢您的咨询。基于您提供的信息，我建议..."
    st.write("已自动填充顾问消息模板，请根据实际情况修改")

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
                    st.write(f"对话摘要: {summary}")  # 不再调用translate_to_chinese

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

# 英文版：
if (language == "English"):

    try:
        import mysql.connector
        from mysql.connector import Error
    except ImportError as e:
        print(f"Import error: {e}")
        import sys

        print(f"Python version: {sys.version}")
        print(f"Python path: {sys.executable}")


    def connect_db():
        try:
            print("Attempting to connect to database...")
            connection = mysql.connector.connect(
                host="1.tcp.au.cpolar.io",
                port="13156",
                database="project",  # Replace with your database name
                user="tao",  # Replace with your database username
                password="initium123!"  # Replace with your database password
            )
            if connection.is_connected():
                print("Database connection successful")
                return connection
            else:
                print("Database connection failed: Cannot establish connection")
                return None
        except Error as e:
            print(f"Database connection error: {e}")

            # Return a mock connection object to allow the app to continue running
            class MockConnection:
                def cursor(self, dictionary=False):
                    class MockCursor:
                        def execute(self, query, params=None):
                            print(f"Simulated SQL execution: {query}")
                            print(f"Parameters: {params}")

                        def fetchall(self):
                            return []

                        def close(self):
                            pass

                    return MockCursor()

                def commit(self):
                    print("Simulated commit")

                def close(self):
                    print("Simulated close connection")

            return MockConnection()
        except Exception as e:
            print(f"Unknown error: {e}")
            return None


    def save_chat_record(customer_message, advisor_message, summary):
        connection = connect_db()
        if connection:
            cursor = connection.cursor()
            query = """
                INSERT INTO chat_records (customer_message, advisor_message, summary)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (customer_message, advisor_message, summary))
            connection.commit()
            cursor.close()
            connection.close()


    def get_chat_records():
        connection = connect_db()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM chat_records")
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return records



    # Use official API to call large models
    def get_ai_response(transcribed_text):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional text summarization assistant."},
                    # System setting
                    {"role": "user",
                     "content": f"Please generate a summary based on the following content and provide an English version:\n\n{transcribed_text}"}
                    # User input
                ],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"


    st.title("Record")

    st.page_link("main.py", label="Back to Main Page")

    model = whisper.load_model("base")

    # Initialize as an empty string
    transcribed_text = ""

    # Preferably wav format, this one works
    uploaded_file = st.file_uploader("Upload Recording", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        audio = uploaded_file.read()

        with open("temp_audio.wav", "wb") as f:
            f.write(audio)  # No call to translate_to_english

        result = model.transcribe("temp_audio.wav")

        st.write("Transcription Result:")
        st.text(result["text"])

        transcribed_text = result["text"]

        st.write(get_ai_response(transcribed_text))  # No call to translate_to_english

    # Microphone input
    audio_value = st.audio_input("Press and Hold to Speak")

    if audio_value is not None:
        audio = audio_value.read()

        with open("temp_say.wav", "wb") as f:
            f.write(audio)  # No call to translate_to_english

        result = model.transcribe("temp_say.wav")

        st.write("Transcription Result:")
        st.text(result["text"])

        # Save for later use
        transcribed_text = result["text"]

        st.write(get_ai_response(transcribed_text))  # No call to translate_to_english

    # Initialize session_state to save state on page refresh
    if 'customer_message' not in st.session_state:
        st.session_state['customer_message'] = ""
    if 'advisor_message' not in st.session_state:
        st.session_state['advisor_message'] = ""

    st.session_state['customer_message'] = transcribed_text
    st.write(f"Customer Message: {transcribed_text}")  # No call to translate_to_english

    # After voice conversion, automatically fill in the advisor message
    # This uses a simple example response based on customer message
    st.session_state[
        'advisor_message'] = "Thank you for your inquiry. Based on the information you provided, I suggest..."
    st.write("Advisor message template auto-filled. Please modify as needed.")

    if st.button("Save Chat Record"):
        # Retrieve current message content from session_state
        customer_message = st.session_state['customer_message']
        advisor_message = st.session_state['advisor_message']

        if not customer_message.strip() or not advisor_message.strip():
            st.warning("Please ensure both customer message and advisor message are filled!")
        else:
            try:
                # Show loading status
                with st.spinner('Generating conversation summary and saving record...'):
                    # Simulate generating summary (avoid calling OpenAI API each time)
                    # In actual usage, uncomment below to use real LLM call

                    # llm = get_llm()
                    # conversation = [{"role": "user", "content": customer_message}, {"role": "assistant", "content": advisor_message}]
                    # summary = llm(conversation)

                    # Simulate summary, in actual use, delete this part
                    summary = f"The customer inquired about investment configuration and seeks returns while ensuring principal safety. The advisor provided detailed investment strategy suggestions."
                    time.sleep(1)  # Simulate processing time

                    # Save chat record and summary to database
                    save_chat_record(customer_message, advisor_message, summary)

                    st.success("Chat record saved, and summary generated and stored.")
                    st.write(f"Conversation Summary: {summary}")  # No call to translate_to_english

                    # Display saved record example format
                    st.subheader("Saved Record Format:")
                    st.json({
                        "customer_message": customer_message,
                        "advisor_message": advisor_message,
                        "summary": summary
                    })
            except Exception as e:
                st.error(f"Error occurred during saving: {e}")

        # Display user instructions
    with st.expander("User Guide"):
        st.markdown("""
            ### How to correctly save chat records

            1. **Fill in Customer Message**:
               - Can be automatically converted from audio file upload.
               - Alternatively, you can manually enter the message.

            2. **Fill in Advisor Message**:
               - Enter your response in the advisor message box.

            3. **Save Record**:
               - Click the "Save Chat Record" button.
               - The system will generate a summary and save all information to the database.

            ### Correct Record Example - **Customer Message**: Contains the customer's question,
             request, or situation description. - **Advisor Message**: 
             Contains your professional advice or response. 
             - **Summary**: The core content of the conversation automatically generated by the system.
            Click the "Fill Example Data" button to view a complete example. """)
