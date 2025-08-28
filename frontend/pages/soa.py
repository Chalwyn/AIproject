import streamlit as st


def run():
    st.title("生成 Statement of Advice (SoA)")

    # 假设的资产配比计划数据
    asset_plan = st.text_area("资产配比计划", "")
    risk_analysis = st.text_area("风险分析", "")

    if st.button("生成 SoA 报告"):
        # 这里调用 AI 模型生成 SoA（空着，您可以根据需求自行实现）
        soa_report = f"资产配比计划: {asset_plan}\n风险分析: {risk_analysis}"
        st.write("SoA 报告: ", soa_report)
