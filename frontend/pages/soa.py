import streamlit as st
from models.get_llm import get_soa_generator
import time


def run():
    st.title("生成个性化 Statement of Advice (SoA)")

    # 初始化session_state
    if 'advisor_style' not in st.session_state:
        st.session_state['advisor_style'] = """
- 风险提示模块用"1. 2. 3."分点表述，每个风险点后需补充1句具体例子
- 建议依据模块需包含"基于XX产品近X年历史数据，XX指标优于同类产品XX%"这样的表述
- 整体语言正式，避免口语化，段落之间用"### 模块名称"分隔
"""

    if 'reference_examples' not in st.session_state:
        st.session_state['reference_examples'] = """
### 风险提示
1. 市场风险：本组合中股票基金占比30%，若市场出现系统性下跌，可能导致组合净值回撤，例如2022年沪深300指数下跌21%时，同类股票基金平均回撤18%。
2. 产品风险：本次推荐的XX债券基金虽风险较低，但仍存在信用风险，即债券发行人可能无法按时兑付本息。
"""

    if 'generated_template' not in st.session_state:
        st.session_state['generated_template'] = ""

    # 用户输入区域
    st.subheader("顾问风格设置")
    st.session_state['advisor_style'] = st.text_area("顾问写作风格描述",
                                                     st.session_state['advisor_style'],
                                                     height=150)

    st.subheader("参考示例")
    st.session_state['reference_examples'] = st.text_area("输入顾问以往的SOA片段作为参考",
                                                          st.session_state['reference_examples'],
                                                          height=200)

    # 生成模板按钮
    if st.button("生成个性化SOA模板"):
        if not st.session_state['advisor_style'].strip() or not st.session_state['reference_examples'].strip():
            st.warning("请填写顾问风格和参考示例！")
        else:
            try:
                with st.spinner('正在生成个性化SOA模板...'):
                    # 获取SOA生成器
                    soa_generator = get_soa_generator()

                    # 调用GPT API生成模板
                    st.session_state['generated_template'] = soa_generator(
                        st.session_state['advisor_style'],
                        st.session_state['reference_examples']
                    )

                    time.sleep(1)  # 模拟处理时间
                    st.success("个性化SOA模板生成成功！")
            except Exception as e:
                st.error(f"生成过程中发生错误: {e}")

    # 显示生成的模板
    if st.session_state['generated_template']:
        st.subheader("生成的个性化SOA模板")
        st.text_area("SOA模板", st.session_state['generated_template'], height=400)

        # 提供下载功能
        st.download_button(
            label="下载SOA模板",
            data=st.session_state['generated_template'],
            file_name="soa_template.txt",
            mime="text/plain"
        )

    # 使用指南
    with st.expander("使用指南"):
        st.markdown("""
        ### 如何生成个性化SOA模板

        1. **设置顾问风格**：
           - 描述顾问的写作习惯、语言特点和格式偏好
           - 越详细的描述越能生成符合顾问风格的模板

        2. **提供参考示例**：
           - 粘贴顾问以往的SOA片段作为参考
           - 示例越丰富，生成的模板越贴近顾问的真实风格

        3. **生成模板**：
           - 点击"生成个性化SOA模板"按钮
           - 系统会调用GPT API生成符合要求的模板

        4. **使用模板**：
           - 查看并编辑生成的模板
           - 下载模板以便在实际工作中使用
        """)