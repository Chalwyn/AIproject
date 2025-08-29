
import openai
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import os

# 全局变量跟踪代理是否已配置
_proxy_configured = False
_session = None


# 配置OpenAI连接，同时保留已设置的API密钥
def configure_openai_proxy():
    global _proxy_configured, _session
    try:
        # 获取当前已设置的API密钥（如果有）
        current_api_key = openai.api_key

        # 只配置一次代理
        if not _proxy_configured:
            # 使用已配置的代理
            proxies = {
                "http": "http://127.0.0.1:7897",
                "https": "http://127.0.0.1:7897"  # 注意这里也是http，因为代理服务器本身是http协议
            }

            _session = requests.Session()
            _session.proxies = proxies
            retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retry)
            _session.mount('http://', adapter)
            _session.mount('https://', adapter)

            openai.requestssession = _session
            print(f"已配置代理: {proxies}")
            _proxy_configured = True

        # 如果之前有设置API密钥，重新设置它
        if current_api_key and openai.api_key != current_api_key:
            openai.api_key = current_api_key
    except Exception as e:
        print(f"配置OpenAI连接时出错: {e}")


# 直接从环境文件中读取API密钥
def load_api_key():
    # 尝试从环境变量中获取
    api_key = os.getenv("OPENAI_API_KEY")
    # 如果环境变量中没有，尝试从文件中读取
    if not api_key:
        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'AiApi.env'), 'r',
                      encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key == 'OPENAI_API_KEY':
                            api_key = value.strip().strip('"').strip("'")
                            break
        except Exception as e:
            print(f"无法从AiApi.env文件加载API密钥: {e}")

    return api_key if api_key else "您的GPT_API_KEY"  # 提供默认值，避免运行时错误


def get_llm(model_name="gpt-3.5-turbo"):
    # 配置代理
    configure_openai_proxy()

    # 设置API密钥（如果尚未设置）
    if not openai.api_key:
        openai.api_key = load_api_key()

    def summarize_conversation(messages):
        # 添加系统提示词，明确要求总结的格式和重点
        system_prompt = """
        你是一名专业的金融顾问助理，负责总结客户与顾问的对话。请根据以下要求生成总结：
        1. 总结必须包含客户的主要问题或需求
        2. 总结必须包含顾问的核心建议或回复
        3. 保持语言简洁、准确，使用专业金融术语
        4. 不要添加原文中没有的信息
        5. 总结内容的模板大概是：在对话中，客户表达了:...顾问则表达了:...
        """

        enhanced_messages = [
                                {"role": "system", "content": system_prompt}
                            ] + messages

        response = openai.ChatCompletion.create(
            model=model_name,
            messages=enhanced_messages,
            temperature=0.3,  # 降低temperature，使输出更稳定
            max_tokens=150  # 限制输出长度
        )
        return response['choices'][0]['message']['content']

    return summarize_conversation


def get_soa_generator(model_name="gpt-3.5-turbo"):
    # 配置代理
    configure_openai_proxy()

    # 设置API密钥（如果尚未设置）
    if not openai.api_key:
        openai.api_key = load_api_key()

    def generate_soa_template(advisor_style, reference_examples, rule_summary=None, template_structure=None):
        """
        生成符合规范的SOA模板Prompt，支持注入规则摘要和模板结构（解决内容简略、偏离模板问题）

        参数:
            advisor_style: str - 顾问写作风格描述
            reference_examples: str - 参考示例文本
            rule_summary: str (可选) - 文档处理器提取的规则摘要（增强规则约束）
            template_structure: str (可选) - 文档处理器提取的模板结构（强制结构对齐）
        返回:
            list - 结构化Prompt
        """
        # 构建“规则补充说明”（若有则注入，无则用示例默认规则）
        rule_supplement = ""
        if rule_summary:
            rule_supplement = f"""
            【补充行业规则细节】
            以下是从专业文档中提取的核心规则，需100%遵守，不得遗漏：
            {rule_summary}
            """

        # 构建“模板结构强制要求”（若有则注入，无则明确示例结构优先级）
        structure_requirement = ""
        if template_structure:
            structure_requirement = f"""
            【模板结构强制对齐】
            请严格按照以下提取的模板结构生成，章节标题、顺序、子模块需完全匹配，不得自行删减或调整：
            {template_structure}
            若结构中包含“XX章节”“XX模块”等占位，需替换为SOA对应实际内容（如“客户风险评估”“产品适配分析”）。
            """
        else:
            structure_requirement = """
            【模板结构强制对齐】
            请从参考示例中提取完整模板结构（包括章节层级、子标题、内容模块），生成时需：
            1. 章节数量不少于5个（对应基础规则的5大模块）；
            2. 每个一级章节下需包含至少2个二级子模块（如“客户背景”下含“基本信息”“风险画像”）；
            3. 章节标题与示例保持一致（如示例用“投资建议依据”，不可改为“建议原因”）。
            """

        # 结构化Prompt
        prompt = [
            {
                "role": "system",
                "content": """你是资深金融SOA撰写专家，精通金融行业合规要求，能严格依据规则、模板、顾问风格生成完整文档。
                核心原则：
                1. 内容不简略：每个模块文字量不少于3行，关键模块（如建议依据、风险提示）需包含具体逻辑/数据维度（如"近3年年化收益XX%""最大回撤XX%"）；
                2. 结构不偏离：完全遵循提供的模板结构，章节顺序、标题、子模块需一一对应；
                3. 合规不遗漏：风险提示必须包含指定语句，客户信息必须用{{占位符}}脱敏；
                4. 表格数据处理：对于任何结构化数据，特别是产品组合、业绩比较、费用明细等内容，必须使用Markdown表格清晰展示，确保数据结构完整保留。
                若生成内容不符合以上原则，需自动检查并补充完整，无需用户提醒。"""
            },
            # 这里可以按需更改
            {
                "role": "user",
                "content": f"""任务：生成金融顾问专属SOA模板，需同时满足基础规则、行业规则、结构要求、风格约束四大维度，具体要求如下：

            一、基础规则（底线要求，违反则无效）
            1. 必含5大核心模块，缺一不可：
               - 客户背景：含{{客户姓名}}、{{客户年龄}}、{{风险承受能力等级}}、{{投资目标}}（新增，补充基础信息完整性）；
               - 建议内容：含{{产品组合清单}}（至少3类产品）、{{配置比例}}（精确到百分比，如“股票型基金35%”）、{{投资周期建议}}；
               - 建议依据：含{{产品历史业绩}}（近1-3年关键数据）、{{客户目标适配性分析}}（如“匹配客户5年退休规划”）、{{市场环境参考}}；
               - 风险提示：分“市场风险”“产品风险”“流动性风险”3类，每类需举例说明（如“市场风险：A股波动可能导致短期回撤”），且必须包含语句：“本建议非保证收益，过往业绩不代表未来表现”；
               - 费用说明：含{{申购费计算方式}}（如“100万以下1.2%，100万以上0.8%”）、{{管理费标准}}、{{其他费用提示}}（如赎回费、托管费）。
            2. 脱敏要求：所有客户信息、产品具体名称、费用金额用{{占位符}}表示，占位符命名需清晰（如{{客户资产规模}}，不可用{{XXX}}）。

            二、行业规则与模板结构（强制对齐，不得自定义）
            {rule_supplement}
            {structure_requirement}

            三、顾问风格约束（贯穿全文，保持一致性）
            请完全模仿以下顾问写作风格，包括语气、句式、专业术语使用习惯：
            {advisor_style}
            示例：若风格为“严谨合规型”，需多用“根据《XX监管规定》”“经风险评估确认”等表述；若为“通俗易懂型”，需避免复杂术语，用“简单来说”“举个例子”等引导。

            四、参考示例与输出要求
            1. 参考示例：
               {reference_examples}
               （示例仅作参考，若与规则/结构要求冲突，以规则/结构要求为准）
            2. 输出要求：
               - 格式：用Markdown分级标题（# 一级标题，## 二级标题），段落清晰，无杂乱排版；对于数据密集型内容（如产品组合、业绩比较、费用明细等），必须使用Markdown表格格式呈现，确保数据结构完整保留
               - 长度：完整模板文字量尽量详细且多
               - 检查：生成后需自动核对"5大模块是否齐全""风险提示语句是否包含""占位符是否规范""表格数据是否已正确转换为Markdown表格"，缺失则补充。

            请直接生成完整SOA英文模板，无需额外解释或开场白。"""
            }
        ]
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=prompt,
            temperature=0.7,
            max_tokens=1000
        )
        return response['choices'][0]['message']['content']

    return generate_soa_template

