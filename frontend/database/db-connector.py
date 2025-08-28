import mysql.connector
from mysql.connector import Error
import sys

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError as e:
    print(f"导入错误: {e}")
    import sys
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")

def connect_db():
    try:
        print("尝试连接数据库...")
        connection = mysql.connector.connect(
            host="1.tcp.au.cpolar.io",
            port="13156",
            database="project",  # 替换为你的数据库名
            user="tao",  # 替换为你的数据库用户名
            password="initium123!"  # 替换为你的数据库密码
        )
        if connection.is_connected():
            print("数据库连接成功")
            return connection
        else:
            print("数据库连接失败: 无法建立连接")
            return None
    except Error as e:
        print(f"数据库连接错误: {e}")
        # 返回一个模拟的连接对象，以便应用可以继续运行
        class MockConnection:
            def cursor(self, dictionary=False):
                class MockCursor:
                    def execute(self, query, params=None):
                        print(f"模拟执行SQL: {query}")
                        print(f"参数: {params}")
                    def fetchall(self):
                        return []
                    def close(self):
                        pass
                return MockCursor()
            def commit(self):
                print("模拟提交事务")
            def close(self):
                print("模拟关闭连接")
        return MockConnection()
    except Exception as e:
        print(f"未知错误: {e}")
        return None

def save_chat_record(customer_message, advisor_message, summary):
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        query = """
            INSERT INTO chat_records (customer_message, advisor_message, summary)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (customer_message, advisor_message, summary))
        connection.commit()
        cursor.close()
        connection.close()

def get_chat_records():
    connection = connect_db()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM chat_records")
        records = cursor.fetchall()
        cursor.close()
        connection.close()
        return records