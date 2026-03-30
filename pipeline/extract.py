import os
import pymysql
from dotenv import load_dotenv

load_dotenv()


def extract_orders():
    connection = pymysql.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM orders")
            rows = cursor.fetchall()
    finally:
        connection.close()
    return rows
