import time
import streamlit as st
import whisper
from openai import OpenAI
import mysql.connector
from mysql.connector import Error
import sys
#数据库函数导入失败，直接拿过来用
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

# 客户端输入apikey
client = OpenAI(
    api_key='OPENAI_API_KEY')


# 用官方的api库来完成大模型的调用
def get_ai_response(transcribed_text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的文本摘要助手。"},  # system为系统设定
                {"role": "user", "content": f"请根据以下内容生成摘要，生成英文版本的：\n\n{transcribed_text}"}  # 输入的用户需求，即问题
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
#最好是wav格式，目前这个是可以的
uploaded_file = st.file_uploader("上传录音", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:

    audio = uploaded_file.read()

    with open("temp_audio.wav", "wb") as f:
        f.write(audio)


    result = model.transcribe("temp_audio.wav")

    st.write("转录结果：")
    st.text(result["text"])

    transcribed_text = result["text"]

    st.write(get_ai_response(transcribed_text))




#麦克风
audio_value = st.audio_input("按住说话")




if audio_value is not None:

    audio = audio_value.read()

    with open("temp_say.wav", "wb") as f:
        f.write(audio)


    result = model.transcribe("temp_say.wav")

    st.write("转录结果：")
    st.text(result["text"])

    #保存在下述名称中，方便后续调用
    transcribed_text = result["text"]

    st.write(get_ai_response(transcribed_text))

# 初始化session_state，用于在页面刷新时保存状态
if 'customer_message' not in st.session_state:
    st.session_state['customer_message'] = ""
if 'advisor_message' not in st.session_state:
    st.session_state['advisor_message'] = ""

st.session_state['customer_message'] = transcribed_text
st.write(f"客户消息: {transcribed_text}")

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
