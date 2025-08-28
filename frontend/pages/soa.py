import streamlit as st
import os
import time
from typing import List  # 类型提示增强
from models.get_llm import get_soa_generator
from utils import document_processor



def run():
    st.title("📊 个性化投资建议声明书 (SOA) 生成工具")
    st.divider()  # 分割线提升视觉体验

    # -------------------------- 1. 会话状态初始化（增强缓存与状态管理）--------------------------
    # 补充：缓存处理后的规则摘要和模板结构，避免重复计算
    if 'session_state_init' not in st.session_state:
        # 基础配置
        st.session_state['advisor_style'] = """
- 风险提示模块必须用"1. 2. 3."分点表述，每个风险点后补充1句具体场景例子（如"市场风险：若A股下跌20%，股票基金可能回撤15%"）
- 建议依据模块需包含"基于{{产品名称}}近{{X}}年历史数据，{{关键指标}}（如年化收益、最大回撤）优于同类产品{{XX}}%"的标准化表述
- 整体语言正式合规，避免"大概""可能"等模糊词汇，段落间用"### 模块名称"明确分隔
- 费用说明需拆分"申购费""管理费""赎回费"三类，每类标注计算方式（如"申购费：100万以下1.2%，100万以上0.8%"）
        """
        st.session_state['reference_examples'] = """
### 风险提示
1. 市场风险：本组合中股票基金占比35%，若市场出现系统性下跌（如2022年沪深300指数下跌21%），可能导致组合净值回撤18%-22%。
2. 产品风险：本次推荐的{{债券基金名称}}虽为中低风险，但仍存在信用风险——若持仓债券发行人（如{{发行人名称}}）违约，可能影响收益兑付。
3. 流动性风险：{{封闭式基金名称}}锁定期为1年，锁定期内无法赎回，需客户匹配长期资金规划。

### 建议依据
基于{{股票基金名称}}近5年历史数据，其年化收益达12.3%，较同类基金平均水平（8.5%）高出3.8个百分点；{{债券基金名称}}近3年最大回撤仅2.1%，符合客户"稳健增值"的投资目标，适配其C3（平衡型）风险承受能力等级。
        """
        # 新增：缓存处理后的规则和结构，避免重复计算
        st.session_state['saved_rules_summary'] = ""
        st.session_state['saved_template_structures'] = ""
        # 新增：LLM参数（用户可调节，控制生成风格）
        st.session_state['llm_temperature'] = 0.3  # 初始值：低温度=更严谨
        st.session_state['llm_max_tokens'] = 2500  # 初始值：确保生成完整模板
        # 新增：文档处理的详细反馈（错误信息、处理文件列表）
        st.session_state['doc_process_errors'] = []
        st.session_state['processed_rule_files'] = []
        st.session_state['processed_template_files'] = []
        # 标记初始化完成
        st.session_state['session_state_init'] = True

    # 保留原有核心会话状态
    if 'generated_template' not in st.session_state:
        st.session_state['generated_template'] = ""
    if 'docs_processor' not in st.session_state:
        st.session_state['docs_processor'] = None
    if 'docs_folder' not in st.session_state:
        st.session_state['docs_folder'] = ""


    # -------------------------- 2. 用户输入区域优化（增强引导与可配置性）--------------------------
    # 2.1 顾问风格设置（增加示例提示）
    st.subheader("🎯 顾问风格配置", help="描述顾问的写作习惯、格式要求，越详细越精准")
    st.session_state['advisor_style'] = st.text_area(
        label="顾问写作风格描述（示例：风险提示分点、费用说明需含计算方式）",
        value=st.session_state['advisor_style'],
        height=180,
        help="可填写：语言正式度、模块格式要求（如分点/段落）、必含表述（如监管依据引用）"
    )

    # 2.2 参考示例（增加格式引导）
    st.subheader("📑 参考示例输入", help="粘贴顾问以往的SOA片段，确保生成风格一致")
    st.session_state['reference_examples'] = st.text_area(
        label="SOA参考片段（建议包含风险提示、建议依据模块）",
        value=st.session_state['reference_examples'],
        height=220,
        help="示例需包含真实模块结构（如### 风险提示），占位符用{{变量名}}表示（如{{客户姓名}}）"
    )

    # 2.3 文档文件夹处理（增强路径验证与反馈）
    st.subheader("📂 SOA规则/模板文档管理", help="上传包含行业规则、SOA模板的PDF/DOCX文件")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.session_state['docs_folder'] = st.text_input(
            label="文件夹路径（Windows：D:\\soa_docs；Mac/Linux：/Users/soa_docs）",
            value=st.session_state['docs_folder'],
            help="文件夹需包含：规则文档（含'规则''规范'关键词）、模板文档（SOA示例）"
        )
    with col2:
        # 新增：快速清空路径按钮
        if st.button("清空路径", use_container_width=True):
            st.session_state['docs_folder'] = ""
            st.session_state['saved_rules_summary'] = ""
            st.session_state['saved_template_structures'] = ""
            st.session_state['doc_process_errors'] = []
            st.session_state['processed_rule_files'] = []
            st.session_state['processed_template_files'] = []
            st.rerun()

    # 2.4 LLM生成参数（新增：用户可调节，解决内容简略问题）
    st.subheader("⚙️ LLM生成参数", help="调节生成内容的严谨度与长度")
    col_temp, col_tokens = st.columns(2)
    with col_temp:
        st.session_state['llm_temperature'] = st.slider(
            label="温度（0=严谨固定，1=灵活多样）",
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            value=st.session_state['llm_temperature'],
            help="生成SOA建议设为0.2-0.4，避免偏离规则"
        )
    with col_tokens:
        st.session_state['llm_max_tokens'] = st.slider(
            label="最大输出长度（字符数）",
            min_value=1000,
            max_value=4000,
            step=100,
            value=st.session_state['llm_max_tokens'],
            help="建议设为2000-3000，确保完整包含5大模块"
        )


    # -------------------------- 3. 文档处理功能增强（详细反馈+错误可视化）--------------------------
    if st.button("🔍 处理文件夹中的文档", use_container_width=True):
        # 1. 基础验证：路径非空且存在
        if not st.session_state['docs_folder'].strip():
            st.warning("❌ 请先输入有效的文件夹路径！")
        elif not os.path.exists(st.session_state['docs_folder']):
            st.error(f"❌ 文件夹不存在：{st.session_state['docs_folder']}，请检查路径是否正确")
        elif not os.path.isdir(st.session_state['docs_folder']):
            st.error(f"❌ 输入的不是文件夹路径：{st.session_state['docs_folder']}")
        else:
            try:
                with st.spinner('📄 正在解析文件夹中的文档（PDF/DOCX）...'):
                    # 初始化文档处理器，并新增错误收集
                    processor = document_processor.DocumentProcessor(st.session_state['docs_folder'])
                    processor.processed_rule_files = []  # 处理成功的规则文档名
                    processor.processed_template_files = []  # 处理成功的模板文档名
                    processor.process_errors = []  # 解析错误的文档信息
                    processor.process_all_docs()

                    # 保存处理结果到会话状态
                    st.session_state['docs_processor'] = processor
                    st.session_state['saved_rules_summary'] = processor.get_rules_summary()
                    st.session_state['saved_template_structures'] = processor.get_template_structures()
                    st.session_state['doc_process_errors'] = processor.process_errors
                    st.session_state['processed_rule_files'] = processor.processed_rule_files
                    st.session_state['processed_template_files'] = processor.processed_template_files

                    # 2. 显示处理结果（详细反馈）
                    st.success(f"✅ 文档处理完成！")
                    # 显示处理的文件列表
                    with st.expander("查看处理详情", expanded=True):
                        # 规则文档
                        st.markdown(f"**📜 处理成功的规则文档（{len(processor.processed_rule_files)}个）**")
                        if processor.processed_rule_files:
                            for idx, file in enumerate(processor.processed_rule_files, 1):
                                st.markdown(f"{idx}. {file}")
                        else:
                            st.markdown("暂无规则文档（规则文档需含'规则''规范''guideline'等关键词）")

                        # 模板文档
                        st.markdown(f"**📋 处理成功的模板文档（{len(processor.processed_template_files)}个）**")
                        if processor.processed_template_files:
                            for idx, file in enumerate(processor.processed_template_files, 1):
                                st.markdown(f"{idx}. {file}")
                        else:
                            st.markdown("暂无模板文档（非规则文档默认归类为模板文档）")

                        # 错误信息
                        if processor.process_errors:
                            st.markdown(f"**⚠️ 解析失败的文档（{len(processor.process_errors)}个）**")
                            for err in processor.process_errors:
                                st.markdown(f"❌ {err}")

                    # 3. 预览提取的规则和结构（让用户确认是否正确）
                    with st.expander("预览提取的规则摘要与模板结构", expanded=False):
                        if st.session_state['saved_rules_summary']:
                            st.markdown("**📜 行业规则摘要**")
                            st.markdown(st.session_state['saved_rules_summary'])
                        else:
                            st.markdown("⚠️ 未提取到规则摘要（请确保规则文档包含有效文本）")

                        if st.session_state['saved_template_structures']:
                            st.markdown("**📋 模板结构分析**")
                            st.markdown(st.session_state['saved_template_structures'])
                        else:
                            st.markdown("⚠️ 未提取到模板结构（请确保模板文档包含有效章节）")

            except Exception as e:
                st.error(f"❌ 文档处理失败：{str(e)}（建议检查文件夹权限或文档格式）")


    # -------------------------- 4. 生成模板逻辑优化（对接增强型Prompt）--------------------------
    if st.button("🚀 生成个性化SOA模板", use_container_width=True, type="primary"):
        # 1. 前置验证
        if not st.session_state['advisor_style'].strip():
            st.warning("❌ 请先填写顾问风格配置！")
        elif not st.session_state['reference_examples'].strip():
            st.warning("❌ 请先填写SOA参考示例！")
        else:
            try:
                with st.spinner('🤖 正在调用LLM生成SOA模板（请耐心等待）...'):
                    # 2. 获取LLM实例（传入用户配置的参数）
                    soa_generator = get_soa_generator(model_name="gpt-3.5-turbo")

                    # 3. 构建增强型Prompt（调用之前优化的generate_soa_template函数）
                    st.session_state['generated_template'] = soa_generator(
                        advisor_style=st.session_state['advisor_style'],
                        reference_examples=st.session_state['reference_examples'],
                        rule_summary=st.session_state['saved_rules_summary'],
                        template_structure=st.session_state['saved_template_structures']
                    )

                    # 4. 调用LLM生成模板（处理流式输出或直接调用，根据get_soa_generator实现调整）
                    # # 假设soa_generator接受结构化Prompt（system+user），返回生成文本
                    # st.session_state['generated_template'] = soa_generator(enhanced_prompt)

                    # 5. 生成成功反馈
                    st.success("✅ 个性化SOA模板生成完成！")

            except Exception as e:
                # 细化错误类型（帮助用户排查）
                if "API key" in str(e) or "authentication" in str(e).lower():
                    st.error(f"❌ LLM调用失败：API密钥无效或未配置，请检查密钥设置")
                elif "timeout" in str(e).lower():
                    st.error(f"❌ LLM调用超时：网络不稳定或LLM响应缓慢，建议重试")
                elif "context length" in str(e).lower():
                    st.error(f"❌ 上下文长度超限：请减少参考示例字数或降低max_tokens值")
                else:
                    st.error(f"❌ 模板生成失败：{str(e)}")


    # -------------------------- 5. 结果显示与下载优化（Markdown渲染+编辑功能）--------------------------
    if st.session_state['generated_template']:
        st.subheader("📄 生成的SOA模板", help="可直接复制使用，或编辑后下载")

        # 5.1 用Markdown渲染模板（更直观，支持分级标题）
        st.markdown("### 模板预览（支持Markdown格式）")
        with st.container(border=True):
            st.markdown(st.session_state['generated_template'])

        # 5.2 提供编辑功能（用户可修改后下载）
        st.markdown("### 模板编辑（修改后点击下载）")
        edited_template = st.text_area(
            label="编辑SOA模板",
            value=st.session_state['generated_template'],
            height=300,
            help="可修改占位符、补充模块内容，保存后点击下载"
        )

        # 5.3 下载功能（支持Markdown和TXT格式）
        st.markdown("### 下载模板")
        col_md, col_txt = st.columns(2)
        with col_md:
            st.download_button(
                label="下载为Markdown文件（.md）",
                data=edited_template,
                file_name=f"soa_template_{time.strftime('%Y%m%d%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col_txt:
            st.download_button(
                label="下载为文本文件（.txt）",
                data=edited_template,
                file_name=f"soa_template_{time.strftime('%Y%m%d%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )


    # -------------------------- 6. 使用指南优化（补充文档处理和参数说明）--------------------------
    with st.expander("📖 使用指南（点击查看详细步骤）", expanded=False):
        st.markdown("""
        ### 完整操作流程
        1. **配置顾问风格**  
           - 填写顾问的写作习惯（如风险提示分点、语言正式度）  
           - 必含格式要求（如"费用说明需拆分申购费/管理费"）

        2. **上传参考示例**  
           - 粘贴顾问以往的SOA片段（至少包含1-2个核心模块，如风险提示、建议依据）  
           - 占位符用`{{变量名}}`表示（如`{{客户姓名}}`、`{{风险承受能力等级}}`）

        3. **处理规则/模板文档（可选但推荐）**  
           - 输入包含行业规则（如"金融SOA监管规范.pdf"）和SOA模板（如"SOA模板示例.docx"）的文件夹路径  
           - 点击【处理文件夹中的文档】，查看提取的规则摘要和模板结构（确保符合预期）

        4. **调节LLM参数**  
           - 温度：建议设为0.2-0.4（越低越严谨，避免偏离规则）  
           - 最大长度：建议设为2000-3000（确保完整包含5大模块：客户背景、建议内容、建议依据、风险提示、费用说明）

        5. **生成与使用模板**  
           - 点击【生成个性化SOA模板】，等待LLM处理  
           - 预览模板后可编辑（如补充占位符、调整模块顺序），最后下载使用

        ### 注意事项
        - 文档格式：仅支持PDF和DOCX，确保文档可提取文本（扫描件需先OCR处理）  
        - 规则文档：文件名或内容需含"规则""规范""guideline"等关键词，否则会被归类为模板文档  
        - LLM调用：确保API密钥配置正确（如OpenAI密钥、本地化LLM服务正常）
        """)


# 启动Streamlit应用
if __name__ == "__main__":
    run()