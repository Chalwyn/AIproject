import os
import openai
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# 配置OpenAI连接，同时保留已设置的API密钥
def configure_openai_proxy():
    try:
        # 获取当前已设置的API密钥（如果有）
        current_api_key = openai.api_key

        # 使用已配置的代理
        proxies = {
            "http": "http://127.0.0.1:7897",
            "https": "http://127.0.0.1:7897"  # 注意这里也是http，因为代理服务器本身是http协议
        }

        session = requests.Session()
        session.proxies = proxies
        retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        openai.requestssession = session
        print(f"已配置代理: {proxies}")

        # 如果之前有设置API密钥，重新设置它
        if current_api_key:
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

    # 设置API密钥
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

    # 设置API密钥
    openai.api_key = load_api_key()

    def generate_soa_template(advisor_style, reference_examples):
        # 构建详细的Prompt，包含行业规则和顾问风格
        prompt = [
            {
                "role": "system",
                "content": "你是一名专业的金融顾问，擅长根据顾问风格和行业规则生成个性化的投资建议声明书(SOA)。"
            },
            {
                "role": "user",
                "content": f"任务：生成金融顾问专属的SOA模板，需满足以下要求：\n\n" \
                           f"1. 规则约束：\n" \
                           f"   - 必须包含模块：客户背景（姓名、年龄、风险承受能力）、建议内容（产品组合、配置比例）、" \
                           f"建议依据（产品历史业绩、适配客户目标的原因）、风险提示（分市场风险、产品风险、流动性风险3类）、" \
                           f"费用说明（申购费、管理费）。\n" \
                           f"   - 风险提示中必须包含\"本建议非保证收益，过往业绩不代表未来表现\"这句话。\n\n" \
                           f"2. 风格约束（参考顾问的写作习惯）：\n" \
                           f"{advisor_style}\n\n" \
                           f"3. 脱敏要求：所有客户个人信息用{{占位符}}代替，如{{客户姓名}}、{{资产规模}}、{{风险承受能力等级}}。\n\n" \
                           f"4. 参考示例：\n" \
                           f"{reference_examples}\n\n" \
                           f"请生成完整的SOA模板，模板中用{{占位符}}代替所有需客户填写的信息。"
            }
        ]

        response = openai.ChatCompletion.create(
            model=model_name,
            messages=prompt,
            temperature=0.7,
            max_tokens=2000
        )
        return response['choices'][0]['message']['content']

    return generate_soa_template

