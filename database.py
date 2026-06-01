import pymysql
from dbutils.pooled_db import PooledDB
import os

class Database:
    """MySQL 连接池封装，基于 PyMySQL + DBUtils"""

    def __init__(self):
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=20,
            mincached=2,
            maxcached=5,
            maxshared=3,
            blocking=True,
            setsession=[],
            ping=0,

            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASS', 'ayaka1128'),
            database=os.getenv('DB_NAME', 'library_db'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def get_conn(self):
        return self.pool.connection()

    def execute(self, sql, args=None):
        """执行 INSERT / UPDATE / DELETE，返回影响行数"""
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, args)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            print(f"[DB Error in execute]: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def fetchall(self, sql, args=None):
        """执行 SELECT，返回全部结果"""
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, args)
            return cursor.fetchall()
        except Exception as e:
            print(f"[DB Error in fetchall]: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def fetchone(self, sql, args=None):
        """执行 SELECT，返回单条结果"""
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, args)
            return cursor.fetchone()
        except Exception as e:
            print(f"[DB Error in fetchone]: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def callproc_borrow(self, p_sno, p_bno, p_ano):
        """调用 sp_borrow_book 存储过程，返回 {status, message}"""
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("SET @p_status = 0;")
            cursor.execute("SET @p_message = '';")

            cursor.execute(
                "CALL sp_borrow_book(%s, %s, %s, @p_status, @p_message)",
                (p_sno, p_bno, p_ano)
            )

            cursor.execute("SELECT @p_status AS status, @p_message AS message;")
            result = cursor.fetchone()
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            print(f"[DB Error in procedure]: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

# 全局单例
db = Database()
