import streamlit as st


def run():
    st.title("生成资产配比计划")

    # 假设的客户需求输入框
    risk_preference = st.selectbox("风险偏好", ["低", "中", "高"])
    investment_amount = st.number_input("投资金额", min_value=0)
    financial_goals = st.text_area("财务目标", "")

    if st.button("生成资产配比计划"):
        # 这里调用 AI 模型生成资产配比计划（空着，您可以根据需求自行实现）
        asset_plan = "生成的资产配比计划"
        st.write("资产配比计划: ", asset_plan)
