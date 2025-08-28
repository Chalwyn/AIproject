import streamlit as st


#启用宽屏模式
st.set_page_config(layout="wide")


with st.sidebar:
    language = st.selectbox("Choose your language / 选择语言", ["English", "中文"])


#中文界面
if(language == "中文"):
    st.title("金融顾问系统")

    st.subheader("本系统是一款智能金融辅助平台，"
                 "能够帮助用户快速处理和理解语音或文本信息，"
                 "通过语音转写、内容摘要和大模型问答等功能，提高信息处理效率，"
                 "为理财决策和日常工作提供智能支持。")
    col1, col2, col3, col4 = st.columns([2,2,2,2])

    with col1:
        st.page_link("pages/robot.py", label="Robot")
        with st.expander("主要功能"):
            st.write('''
                    该页面主要功能包括：
                    知识展示：系统会展示内置的理财知识库内容，让用户了解基础理财信息。
                    智能问答：用户可以在输入框中提出理财相关问题，机器人将结合知识库内容生成专业建议。
                    个性化摘要：机器人能够根据用户提供的内容或问题，生成简洁明了的总结或建议。
                    交互体验：提供即时响应，用户可以随时查看机器人对问题的回答，帮助做出理财决策。
                    导航提示：用户可通过页面链接返回主界面，方便在不同功能页面之间切换。
                ''')

    with col2:
        st.page_link("pages/record.py", label="record")
        with st.expander("主要功能"):
            st.write('''
                    页面的主要功能是让用户通过上传录音文件或直接使用麦克风录音，
                    将语音内容自动转写为文字，并通过智能文本摘要助手生成简明的摘要，
                    方便用户快速获取录音内容的核心信息，同时支持返回主页面的导航操作。
                ''')

    with col3:
        st.page_link("pages/plan.py", label="plan")
        with st.expander("主要功能"):
            st.write('''
                    该页面主要功能包括：
                    计划
                ''')

    with col4:
        st.page_link("pages/soa.py", label="soa")
        with st.expander("主要功能"):
            st.write('''
                    该页面主要功能包括：
                    soa报告生成
                ''')

    with st.sidebar:
        st.title("你好")

#选择英文
if (language == "English"):
    st.title("Financial Advisor System")

    st.subheader("This system is an intelligent financial assistant platform, "
                 "designed to help users quickly process and understand speech or text information, "
                 "through features like speech transcription, content summarization, and large model Q&A, "
                 "improving information processing efficiency, and providing intelligent support for financial decision-making and daily work.")

    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

    with col1:
        st.page_link("pages/robot.py", label="Robot")
        with st.expander("Main Features"):
            st.write('''
                    The main features of this page include:
                    Knowledge Display: The system will display content from an embedded financial knowledge base, allowing users to understand basic financial information.
                    Intelligent Q&A: Users can ask financial-related questions in the input box, and the robot will generate professional advice based on the knowledge base.
                    Personalized Summaries: The robot can generate concise summaries or advice based on the content or questions provided by the user.
                    Interactive Experience: Provides instant responses, allowing users to view the robot's answers to questions and help make financial decisions.
                    Navigation Tips: Users can return to the main interface via page links, making it easier to switch between different functional pages.
                ''')

    with col2:
        st.page_link("pages/record.py", label="Record")
        with st.expander("Main Features"):
            st.write('''
                    The main function of this page is to allow users to upload audio files or record audio directly through the microphone, 
                    automatically transcribe the speech content into text, and generate a concise summary of the text via the intelligent text summarization assistant.
                    This helps users quickly obtain the core information from the recording content. It also supports navigation back to the main page.
                ''')

    with col3:
        st.page_link("pages/plan.py", label="Plan")
        with st.expander("Main Features"):
            st.write('''
                    The main function of this page includes:
                    Planning
                ''')

    with col4:
        st.page_link("pages/soa.py", label="SoA")
        with st.expander("Main Features"):
            st.write('''
                    The main function of this page includes:
                    SoA report generation
                ''')

    with st.sidebar:
        st.title("Hello")




