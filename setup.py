from setuptools import setup, find_packages

setup(
    name='WealthOS',  # 你的项目名称
    version='0.1',  # 版本号
    packages=find_packages(),  # 自动查找并包含项目中的所有包
    install_requires=[  # 项目所依赖的库
        'streamlit',  # 用于构建 web 应用
        'SpeechRecognition',  # 用于语音识别
        'pydub',  # 用于音频处理
        'mysql-connector-python',  # 用于连接 MySQL 数据库
        'openai',  # 用于与 OpenAI API 交互
    ],
    classifiers=[  # 项目分类
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # 可以修改为你选择的许可证
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # 设置 Python 版本要求
)
