import openai

def get_llm(model_name="gpt-3.5-turbo"):
    openai.api_key = "YOUR_OPENAI_API_KEY"  # 填写你的API密钥

    def summarize_conversation(messages):
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            temperature=0.5
        )
        return response['choices'][0]['message']['content']

    return summarize_conversation
