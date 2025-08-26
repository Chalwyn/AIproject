import streamlit as st
import pages.record  # 导入聊天记录页面
import pages.plan  # 导入资产配比生成页面
import pages.soa  # 导入SoA生成页面

def main():
    st.title("AI 辅助平台 - 金融理财顾问")

    # 主界面导航
    menu = ["首页", "与客户互动 & 记录", "生成资产配比计划", "生成 SoA"]
    choice = st.sidebar.selectbox("选择功能", menu)

    if choice == "首页":
        st.subheader("欢迎使用 AI 辅助平台")
        st.write("在此平台中，您可以与客户互动、生成资产配比计划以及生成正式报告（SoA）。")
    elif choice == "与客户互动 & 记录":
        import pages.record  # 导入聊天记录页面
        pages.record.run()
    elif choice == "生成资产配比计划":
        import pages.plan  # 导入资产配比生成页面
        pages.plan.run()
    elif choice == "生成 SoA":
        import pages.soa  # 导入SoA生成页面
        pages.soa.run()

if __name__ == '__main__':
    main()
