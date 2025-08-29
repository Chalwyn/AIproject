import streamlit as st
import os
import time
import tempfile
from models.get_llm import get_soa_generator, get_llm
# 修改导入语句，使用相对导入
from utils.document_processor import DocumentProcessor
from io import BytesIO


st.title("📊 个性化投资建议声明书 (SOA) 生成工具")
st.divider()

# 会话状态初始化
if 'session_state_init' not in st.session_state:
    st.session_state['advisor_style'] = ""
    st.session_state['reference_examples'] = """
### 风险提示
1. 市场风险：本组合中股票基金占比35%，若市场出现系统性下跌（如2022年沪深300指数下跌21%），可能导致组合净值回撤18%-22%。
2. 产品风险：本次推荐的{{债券基金名称}}虽为中低风险，但仍存在信用风险——若持仓债券发行人（如{{发行人名称}}）违约，可能影响收益兑付。
3. 流动性风险：{{封闭式基金名称}}锁定期为1年，锁定期内无法赎回，需客户匹配长期资金规划。

### 建议依据
基于{{股票基金名称}}近5年历史数据，其年化收益达12.3%，较同类基金平均水平（8.5%）高出3.8个百分点；{{债券基金名称}}近3年最大回撤仅2.1%，符合客户"稳健增值"的投资目标，适配其C3（平衡型）风险承受能力等级。
    """
    st.session_state['saved_rules_summary'] = ""
    st.session_state['saved_template_structures'] = ""
    st.session_state['doc_process_errors'] = []
    st.session_state['processed_rule_files'] = []
    st.session_state['processed_template_files'] = []
    st.session_state['style_files'] = []
    st.session_state['session_state_init'] = True

if 'generated_template' not in st.session_state:
    st.session_state['generated_template'] = ""
if 'docs_processor' not in st.session_state:
    st.session_state['docs_processor'] = None
if 'docs_folder' not in st.session_state:
    st.session_state['docs_folder'] = ""

# 顾问风格文件上传
st.subheader("🎯 顾问风格文件上传", help="上传体现顾问写作风格的PDF/DOCX文件，AI自动总结")
uploaded_files = st.file_uploader(
    label="选择顾问风格文件（支持PDF、DOCX）",
    type=["pdf", "docx"],
    accept_multiple_files=True,
    help="示例：顾问以往写的SOA文档、风格规范文档等"
)

if uploaded_files:
    st.session_state['style_files'] = uploaded_files
    st.success(f"✅ 已上传 {len(uploaded_files)} 个文件：{[f.name for f in uploaded_files]}")

    if st.button("🔍 分析顾问风格", use_container_width=True, type="secondary"):
        try:
            with st.spinner('📄 正在处理文件并分析风格...'):
                # 创建临时文件夹
                with tempfile.TemporaryDirectory() as temp_dir:
                    # 保存上传文件到临时文件夹
                    for uploaded_file in uploaded_files:
                        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(temp_file_path, 'wb') as f:
                            f.write(uploaded_file.getvalue())

                    # 初始化DocumentProcessor处理临时文件夹
                    temp_processor = DocumentProcessor(docs_folder=temp_dir)
                    temp_processor.process_all_docs()

                    # 提取所有处理后的文件内容
                    style_content_list = []
                    for idx, rule_content in enumerate(temp_processor.rules, 1):
                        style_content_list.append(f"【顾问风格规则文档{idx}】\n{rule_content}")
                    for idx, template_content in enumerate(temp_processor.templates, 1):
                        style_content_list.append(f"【顾问风格模板文档{idx}】\n{template_content}")

                    if not style_content_list:
                        st.warning("⚠️ 未从上传文件中提取到有效内容（可能是扫描件或空白文档）")
                        st.stop()

                    # 关键修复：使用get_llm进行风格分析（而非get_soa_generator）
                    # 因为get_llm返回的函数接受messages参数，更适合总结任务
                    style_analyzer = get_llm(model_name="gpt-3.5-turbo")

                    # 构建风格分析的消息列表（符合get_llm返回函数的参数要求）
                    style_analysis_messages = [
                        {"role": "user",
                         "content": f"""请分析以下金融SOA文档的写作风格，总结出：
1. 语言特点（正式/通俗、长句/短句、专业术语使用频率）
2. 结构习惯（章节划分方式、标题格式、模块顺序）
3. 风险提示的表述风格（是否举例、是否用数据支撑）
4. 建议依据的呈现方式（是否引用历史数据、是否做对比分析）

文档内容：
{'\n'.join(style_content_list)}"""}
                    ]

                    # 调用LLM进行风格分析（完全匹配get_llm返回函数的参数要求）
                    st.session_state['advisor_style'] = style_analyzer(style_analysis_messages)

                    # 显示分析结果
                    st.success("🎉 顾问风格分析完成！")
                    with st.expander("查看提取的顾问风格规范（可编辑）", expanded=True):
                        st.session_state['advisor_style'] = st.text_area(
                            label="顾问风格规范",
                            value=st.session_state['advisor_style'],
                            height=200,
                            help="可手动调整风格描述，确保符合实际需求"
                        )

                    # 显示处理错误信息
                    if temp_processor.process_errors:
                        with st.expander("⚠️ 文件处理警告", expanded=False):
                            for err in temp_processor.process_errors:
                                st.markdown(f"❌ {err}")

        except Exception as e:
            st.error(f"❌ 风格分析失败：{str(e)}（建议检查函数参数是否匹配）")

# SOA参考示例
st.subheader("📑 SOA参考示例", help="粘贴顾问以往SOA片段，确保风格一致")
st.session_state['reference_examples'] = st.text_area(
    label="参考片段（需含模块结构如### 风险提示）",
    value=st.session_state['reference_examples'],
    height=220,
    help="占位符用{{变量名}}表示，如{{客户姓名}}"
)

# 规则/模板文件夹管理
st.subheader("📂 SOA规则/模板文件夹", help="输入本地文件夹路径，批量处理行业规则/模板")
col1, col2 = st.columns([3, 1])
with col1:
    st.session_state['docs_folder'] = st.text_input(
        label="文件夹路径（Windows：D:\\soa_docs；Mac：/Users/soa_docs）",
        value=st.session_state['docs_folder']
    )
with col2:
    if st.button("清空路径", use_container_width=True):
        st.session_state['docs_folder'] = ""
        st.session_state['saved_rules_summary'] = ""
        st.session_state['saved_template_structures'] = ""
        st.session_state['doc_process_errors'] = []
        st.session_state['processed_rule_files'] = []
        st.session_state['processed_template_files'] = []
        st.rerun()

# 处理文件夹中的文档
if st.button("🔍 处理文件夹中的文档", use_container_width=True):
    if not st.session_state['docs_folder'].strip():
        st.warning("❌ 请先输入有效文件夹路径！")
    elif not os.path.exists(st.session_state['docs_folder']):
        st.error(f"❌ 文件夹不存在：{st.session_state['docs_folder']}")
    elif not os.path.isdir(st.session_state['docs_folder']):
        st.error(f"❌ 不是文件夹路径：{st.session_state['docs_folder']}")
    else:
        try:
            with st.spinner('📄 正在解析文件夹文档...'):
                processor = DocumentProcessor(st.session_state['docs_folder'])
                processor.process_all_docs()

                st.session_state['docs_processor'] = processor
                st.session_state['saved_rules_summary'] = processor.get_rules_summary()
                st.session_state['saved_template_structures'] = processor.get_template_structures()
                st.session_state['doc_process_errors'] = processor.process_errors
                st.session_state['processed_rule_files'] = processor.processed_rule_files
                st.session_state['processed_template_files'] = processor.processed_template_files

                st.success(
                    f"✅ 处理完成！规则文档：{len(processor.processed_rule_files)}个，模板文档：{len(processor.processed_template_files)}个")
                with st.expander("查看处理详情", expanded=True):
                    st.markdown(f"**📜 成功处理的规则文档**")
                    for idx, file in enumerate(processor.processed_rule_files, 1):
                        st.markdown(f"{idx}. {file}")
                    if not processor.processed_rule_files:
                        st.markdown("⚠️ 暂无规则文档")

                    st.markdown(f"**📋 成功处理的模板文档**")
                    for idx, file in enumerate(processor.processed_template_files, 1):
                        st.markdown(f"{idx}. {file}")
                    if not processor.processed_template_files:
                        st.markdown("⚠️ 暂无模板文档")

                    if processor.process_errors:
                        st.markdown(f"**❌ 解析失败的文档**")
                        for err in processor.process_errors:
                            st.markdown(f"- {err}")

        except Exception as e:
            st.error(f"❌ 文件夹处理失败：{str(e)}")

# 生成个性化SOA模板
if st.button("🚀 生成个性化SOA模板", use_container_width=True, type="primary"):
    if not st.session_state['advisor_style'].strip():
        st.warning("❌ 请先上传顾问风格文件并完成分析！")
    elif not st.session_state['reference_examples'].strip():
        st.warning("❌ 请先填写SOA参考示例！")
    else:
        try:
            with st.spinner('🤖 正在生成SOA模板...'):
                # 初始化SOA生成器（根据提供的代码，该函数不接受temperature等参数）
                soa_generator = get_soa_generator(model_name="gpt-3.5-turbo")

                # 调用生成函数，仅传递其实际接受的4个参数
                st.session_state['generated_template'] = soa_generator(
                    advisor_style=st.session_state['advisor_style'],
                    reference_examples=st.session_state['reference_examples'],
                    rule_summary=st.session_state['saved_rules_summary'] or None,
                    template_structure=st.session_state['saved_template_structures'] or None
                )

                st.success("✅ SOA模板生成完成！")

        except Exception as e:
            st.error(f"❌ 模板生成失败：{str(e)}")

# 结果显示与下载
if st.session_state['generated_template']:
    st.subheader("📄 生成的SOA模板", help="可预览、编辑后下载")

    st.markdown("### 模板预览")
    with st.container(border=True):
        st.markdown(st.session_state['generated_template'])

    st.markdown("### 模板编辑")
    edited_template = st.text_area(
        label="编辑模板内容",
        value=st.session_state['generated_template'],
        height=300
    )

    st.markdown("### 下载模板")
    col_md, col_txt = st.columns(2)
    with col_md:
        st.download_button(
            label="下载为Markdown（.md）",
            data=edited_template,
            file_name=f"soa_template_{time.strftime('%Y%m%d%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with col_txt:
        st.download_button(
            label="下载为文本（.txt）",
            data=edited_template,
            file_name=f"soa_template_{time.strftime('%Y%m%d%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
