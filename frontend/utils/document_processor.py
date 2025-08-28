import PyPDF2
from docx import Document
import os
from models.get_llm import get_llm


class DocumentProcessor:
    def __init__(self, docs_folder):
        self.docs_folder = docs_folder
        self.rules = []
        self.templates = []
        # 缓存LLM实例
        self._llm = None
        # 缓存已处理的内容
        self._summaries_cache = {}
        self._structures_cache = {}
        # 新增：记录处理的文件列表与错误信息（用于Streamlit反馈）
        self.processed_rule_files = []  # 处理成功的规则文档名
        self.processed_template_files = []  # 处理成功的模板文档名
        self.process_errors = []  # 解析错误的文档信息（格式："文件名：错误原因"）

    def _get_llm_instance(self):
        """获取LLM实例（单例模式）"""
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    def _process_pdf(self, file_path):
        """解析PDF文件内容"""
        content = ""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted_text = page.extract_text() or ""
                    content += extracted_text
        except Exception as e:
            # 记录PDF解析错误
            err_msg = f"解析PDF文件 {os.path.basename(file_path)} 时出错: {str(e)}"
            print(err_msg)
            self.process_errors.append(err_msg)
        return content

    def _process_docx(self, file_path):
        """解析Word文档内容"""
        content = ""
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                content += para.text + "\n"
        except Exception as e:
            # 记录Word解析错误
            err_msg = f"解析Word文件 {os.path.basename(file_path)} 时出错: {str(e)}"
            print(err_msg)
            self.process_errors.append(err_msg)
        return content

    def _is_rule_document(self, file_name, content):
        """判断文档是否为规则文档（优化关键词匹配逻辑，降低误判）"""
        rule_keywords = ['规则', '规范', '指引', '要求', '监管', '条例', 'regulation', 'rule', 'guideline', 'requirement']
        file_name_lower = file_name.lower()
        content_lower = content.lower() if content else ""

        # 文件名包含2个及以上关键词，直接判定为规则文档
        file_keyword_count = sum(1 for kw in rule_keywords if kw.lower() in file_name_lower)
        if file_keyword_count >= 2:
            return True
        # 文件名含1个关键词 + 内容含1个关键词，判定为规则文档
        elif file_keyword_count == 1:
            content_keyword_count = sum(1 for kw in rule_keywords if kw.lower() in content_lower)
            return content_keyword_count >= 1
        # 文件名无关键词，但内容含2个及以上关键词，判定为规则文档
        else:
            content_keyword_count = sum(1 for kw in rule_keywords if kw.lower() in content_lower)
            return content_keyword_count >= 2

    def _summarize_content(self, content):
        """使用LLM生成文档摘要（优化长文档处理逻辑，保留核心章节）"""
        # 检查缓存（改用内容哈希作为键，避免长内容缓存键过长）
        cache_key = hash(content)
        if cache_key in self._summaries_cache:
            return self._summaries_cache[cache_key]

        try:
            llm = self._get_llm_instance()
            # 短文档（<2000字符）直接生成摘要（原逻辑为返回原文，优化为生成摘要更精准）
            if len(content) <= 2000:
                prompt = [
                    {"role": "user", "content": f"请总结以下金融SOA相关文档的核心内容，重点提取：1.规则要求 2.模板结构 3.必填模块，摘要需简洁完整：{content}"}
                ]
                result = llm(prompt)
            # 中长文档（2001-10000字符）按章节分段（基于标题关键词拆分）
            elif 2001 <= len(content) <= 10000:
                # 按常见章节标题拆分（如"1. ""一、""### "）
                import re
                # 匹配中文/英文章节标题的正则
                chapter_pattern = re.compile(r'(\d+\.\s+|一、\s+|二、\s+|###\s+)')
                chunks = chapter_pattern.split(content)
                # 重组拆分后的内容，确保每个片段包含完整章节
                full_chunks = []
                current_chunk = ""
                for part in chunks:
                    if chapter_pattern.match(part):
                        if current_chunk:
                            full_chunks.append(current_chunk)
                        current_chunk = part
                    else:
                        current_chunk += part
                if current_chunk:
                    full_chunks.append(current_chunk)
                # 对每个章节片段生成摘要
                summaries = []
                for idx, chunk in enumerate(full_chunks, 1):
                    if len(chunk.strip()) < 100:
                        continue  # 跳过过短片段
                    prompt = [
                        {"role": "user", "content": f"请总结以下文档第{idx}章节的核心内容，重点关注金融SOA相关的规则或结构：{chunk[:2000]}"}
                    ]
                    summaries.append(f"第{idx}章节摘要：{llm(prompt)}")
                result = "\n\n".join(summaries)
            # 超长文档（>10000字符）优先提取标题+首尾核心内容
            else:
                # 提取所有章节标题
                import re
                chapter_pattern = re.compile(r'(\d+\.\s+[^\n]+|一、\s+[^\n]+|二、\s+[^\n]+|###\s+[^\n]+)')
                chapters = chapter_pattern.findall(content)
                chapter_str = "文档包含章节：\n" + "\n".join(chapters) if chapters else "文档未识别到明确章节"
                # 提取前3000字符（开头核心规则）+ 后2000字符（结尾补充说明）
                key_content = content[:3000] + "\n[文档中间部分省略]\n" + content[-2000:]
                prompt = [
                    {"role": "user", "content": f"以下是超长金融SOA文档的关键信息（含章节列表和核心片段），请总结：1.核心规则要求 2.必填模块 3.文档结构：\n{chapter_str}\n\n核心片段：{key_content}"}
                ]
                result = llm(prompt)

            # 缓存结果（用哈希键存储）
            self._summaries_cache[cache_key] = result
            return result
        except Exception as e:
            err_msg = f"生成摘要时出错: {str(e)}"
            print(err_msg)
            self.process_errors.append(err_msg)
            return content  # 出错时返回原文

    def get_rules_summary(self):
        """生成规则文档的摘要（优化格式，增加规则分类标签）"""
        if not self.rules:
            return "未检测到有效规则文档，将使用默认SOA规则（包含客户背景、建议内容、建议依据、风险提示、费用说明5大模块）"

        rule_summaries = []
        for idx, rule_content in enumerate(self.rules, 1):
            summary = self._summarize_content(rule_content)
            rule_summaries.append(f"### 规则文档{idx}摘要\n{summary}")

        # 增加规则汇总说明
        return f"## 行业规则总览\n以下是从{len(self.rules)}个规则文档中提取的核心要求（生成SOA需100%遵守）：\n\n" + "\n\n".join(rule_summaries)

    def get_template_structures(self):
        """提取模板文档的结构（优化结构分析Prompt，增加SOA专属要求）"""
        if not self.templates:
            return "未检测到有效模板文档，默认SOA结构参考：\n1. 客户背景（姓名、年龄、风险承受能力）\n2. 投资建议内容（产品组合、配置比例）\n3. 建议依据（历史业绩、客户适配性）\n4. 风险提示（市场/产品/流动性风险）\n5. 费用说明（申购费、管理费）"

        template_structures = []
        llm = self._get_llm_instance()

        for idx, template_content in enumerate(self.templates, 1):
            # 优化缓存键：用文档前1000字符哈希+索引，避免重复
            cache_key = hash(template_content[:1000]) + idx
            if cache_key in self._structures_cache:
                template_structures.append(f"### 模板文档{idx}结构\n{self._structures_cache[cache_key]}")
                continue

            try:
                # 优化Prompt：明确要求提取SOA专属结构（含层级、必填模块）
                prompt = [
                    {
                        "role": "user",
                        "content": f"请分析以下金融SOA模板文档的结构，输出要求：1. 按「一级章节→二级子模块」格式列出 2. 标注每个模块是否为必填 3. 说明模块间的逻辑顺序：\n{template_content[:1500]}..."  # 增加提取字符数，提升准确性
                    }
                ]
                structure = llm(prompt)
                # 缓存结果
                self._structures_cache[cache_key] = structure
                template_structures.append(f"### 模板文档{idx}结构\n{structure}")
            except Exception as e:
                err_msg = f"提取模板文档{idx}结构时出错: {str(e)}"
                print(err_msg)
                self.process_errors.append(err_msg)
                fallback = f"模板文档{idx}结构（部分提取）：\n{template_content[:800]}..."  # 增加 fallback 字符数，保留更多信息
                self._structures_cache[cache_key] = fallback
                template_structures.append(fallback)

        # 增加结构汇总说明
        return f"## SOA模板结构总览\n以下是从{len(self.templates)}个模板文档中提取的结构框架（生成SOA需严格对齐）：\n\n" + "\n\n".join(template_structures)

    def process_all_docs(self):
        """处理文件夹中的所有文档（优化流程，增加文件类型过滤与结果记录）"""
        # 清空历史数据（含处理记录和错误）
        self.rules = []
        self.templates = []
        self.processed_rule_files = []
        self.processed_template_files = []
        self.process_errors = []

        if not os.path.exists(self.docs_folder):
            err_msg = f"文件夹不存在: {self.docs_folder}"
            print(err_msg)
            self.process_errors.append(err_msg)
            return

        # 遍历文件夹处理所有文件（仅支持PDF/DOCX）
        supported_extensions = ('.pdf', '.docx')
        for file_name in os.listdir(self.docs_folder):
            file_path = os.path.join(self.docs_folder, file_name)
            # 跳过子文件夹，仅处理支持格式的文件
            if os.path.isdir(file_path):
                print(f"跳过子文件夹: {file_name}")
                continue
            if not file_name.lower().endswith(supported_extensions):
                err_msg = f"跳过不支持的文件格式: {file_name}（仅支持PDF/DOCX）"
                print(err_msg)
                self.process_errors.append(err_msg)
                continue

            # 解析文件内容
            content = ""
            if file_name.lower().endswith('.pdf'):
                content = self._process_pdf(file_path)
            elif file_name.lower().endswith('.docx'):
                content = self._process_docx(file_path)

            # 分析内容并分类存储（记录处理结果）
            if not content.strip():
                err_msg = f"文件无有效文本: {file_name}（可能是扫描件或空白文档）"
                print(err_msg)
                self.process_errors.append(err_msg)
                continue

            if self._is_rule_document(file_name, content):
                self.rules.append(content)
                self.processed_rule_files.append(file_name)
            else:
                self.templates.append(content)
                self.processed_template_files.append(file_name)

            print(f"已处理文件: {file_name}")

        # 输出处理汇总
        print(f"\n处理完成 - 规则文档：{len(self.processed_rule_files)}个，模板文档：{len(self.processed_template_files)}个，错误：{len(self.process_errors)}个")
