# 可以创建一个新的utils/document_processor.py文件
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
            print(f"解析PDF文件 {file_path} 时出错: {e}")
        return content

    def _process_docx(self, file_path):
        """解析Word文档内容"""
        content = ""
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                content += para.text + "\n"
        except Exception as e:
            print(f"解析Word文件 {file_path} 时出错: {e}")
        return content

    def _is_rule_document(self, file_name, content):
        """判断文档是否为规则文档"""
        # 可以根据文件名或内容中的关键词来判断
        rule_keywords = ['规则', '规范', '指引', '要求', 'regulation', 'rule', 'guideline']

        # 检查文件名
        for keyword in rule_keywords:
            if keyword.lower() in file_name.lower():
                return True

        # 检查内容
        if len(content) > 0:
            content_lower = content.lower()
            for keyword in rule_keywords:
                if keyword.lower() in content_lower:
                    return True

        return False

    def _summarize_content(self, content):
        """使用LLM生成文档摘要"""
        # 检查缓存
        if content in self._summaries_cache:
            return self._summaries_cache[content]

        try:
            # 对长文档进行分段摘要
            if len(content) > 2000:
                # 对于超长文档，只处理关键部分，提高性能
                if len(content) > 10000:
                    # 只处理前5000字符和后2000字符
                    key_content = content[:5000] + "\n[文档中间部分省略]\n" + content[-2000:]
                    chunks = [key_content[i:i + 2000] for i in range(0, len(key_content), 2000)]
                else:
                    chunks = [content[i:i + 2000] for i in range(0, len(content), 2000)]

                llm = self._get_llm_instance()
                summaries = []
                for chunk in chunks:
                    summary = llm([{"role": "user", "content": f"请总结以下文档内容，重点关注规则和模板结构：{chunk}"}])
                    summaries.append(summary)
                result = "\n".join(summaries)
            else:
                # 短文档直接返回原文
                result = content

            # 缓存结果
            self._summaries_cache[content] = result
            return result
        except Exception as e:
            print(f"生成摘要时出错: {e}")
            return content  # 出错时返回原文

    def get_rules_summary(self):
        """生成规则文档的摘要"""
        if not self.rules:
            return ""

        rule_summaries = []
        for rule_content in self.rules:
            summary = self._summarize_content(rule_content)
            rule_summaries.append(summary)

        return "\n\n".join(rule_summaries)

    def get_template_structures(self):
        """提取模板文档的结构"""
        if not self.templates:
            return ""

        template_structures = []
        # 获取LLM实例
        llm = self._get_llm_instance()

        for template_content in self.templates:
            # 检查缓存
            cache_key = template_content[:1000]  # 使用前1000字符作为缓存键
            if cache_key in self._structures_cache:
                template_structures.append(self._structures_cache[cache_key])
                continue

            try:
                structure = llm([{"role": "user",
                                  "content": f"请分析以下文档的结构，列出主要章节和内容框架：{template_content[:1000]}..."}])
                # 缓存结果
                self._structures_cache[cache_key] = structure
                template_structures.append(structure)
            except Exception as e:
                print(f"提取模板结构时出错: {e}")
                fallback = template_content[:500] + "..."
                template_structures.append(fallback)
                # 缓存失败结果
                self._structures_cache[cache_key] = fallback

        return "\n\n".join(template_structures)

    def process_all_docs(self):
        """处理文件夹中的所有文档"""
        if not os.path.exists(self.docs_folder):
            print(f"文件夹不存在: {self.docs_folder}")
            return

        # 清空现有数据
        self.rules = []
        self.templates = []

        # 遍历文件夹处理所有文档
        for file_name in os.listdir(self.docs_folder):
            file_path = os.path.join(self.docs_folder, file_name)
            # 只处理文件，跳过子文件夹
            if os.path.isfile(file_path):
                content = ""
                if file_name.endswith('.pdf'):
                    content = self._process_pdf(file_path)
                elif file_name.endswith('.docx'):
                    content = self._process_docx(file_path)

                # 分析内容并分类存储
                if content:
                    if self._is_rule_document(file_name, content):
                        self.rules.append(content)
                    else:
                        self.templates.append(content)
                    print(f"已处理文件: {file_name}")