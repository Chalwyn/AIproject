import mysql.connector
from mysql.connector import Error

def connect_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            database="wealthos",  # 替换为你的数据库名
            user="root",  # 替换为你的数据库用户名
            password="password"  # 替换为你的数据库密码
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
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
