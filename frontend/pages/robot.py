import streamlit as st
import openai
from getllm import get_llm
import os
from openai import OpenAI

#打开data里面的txt格式的文件并保存到file_content
with open("data/example.txt", "r", encoding="utf-8") as f:
    file_content = f.read()

st.write(file_content)

#客户端输入apikey
client = OpenAI(api_key='OPENAI_API_KEY')

#用官方的api库来完成大模型的调用
def get_ai_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业理财顾问。"},#system为系统设定
                {"role": "assistant", "content": file_content},#为传入的读取的信息
                {"role": "user", "content": prompt}#输入的用户需求，即问题
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"错误: {str(e)}"


st.page_link("main.py", label="返回主页面")


st.title("robot")


prompt = st.chat_input("Say something" , width=300)
if prompt:
    st.write(prompt)



if prompt:
    response = get_ai_response(prompt)
    st.write(f"机器人助手: {response}")
else:
    st.write("请输入问题")