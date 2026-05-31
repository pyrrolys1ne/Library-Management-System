import pymysql
from dbutils.pooled_db import PooledDB
import os

class Database:
    def __init__(self):
        """
        初始化数据库连接池
        生产环境建议将账号密码通过环境变量注入 (os.getenv)
        """
        # Element Plus + Flask 轻量化方案使用 MySQL
        self.pool = PooledDB(
            creator=pymysql,  # 使用 pymysql
            maxconnections=20, # 连接池最大连接数，这里设置为 20，可以并发支撑 Flask 线程
            mincached=2,       # 最小空闲连接
            maxcached=5,       # 最大空闲连接
            maxshared=3,       # 最大共享连接
            blocking=True,     # 等不到连接时阻塞等待
            setsession=[],
            ping=0,
            
            # 使用环境变量获取，避免硬编码密码（此处提供默认值便于快速起步）
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),             # 请替换为你的 MySQL 账号
            password=os.getenv('DB_PASS', 'ayaka1128'),       # 请替换为你的 MySQL 密码
            database=os.getenv('DB_NAME', 'library_db'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor         # 返回字典格式，方便转 JSON 送给前端
        )

    def get_conn(self):
        """从连接池获取一个连接"""
        return self.pool.connection()

    def execute(self, sql, args=None):
        """执行增删改 (INSERT/UPDATE/DELETE)"""
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
        """执行查询，获取所有记录 (SELECT)"""
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
        """执行查询，获取单条记录 (SELECT LIMIT 1)"""
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
        """
        专门封装调用 sp_borrow_book 存储过程的方法。
        PyMySQL 原生的 callproc 对于 OUT 参数检索比较麻烦，通常通过变量读取。
        """
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            # 初始化 OUT 参数用的用户变量
            cursor.execute("SET @p_status = 0;")
            cursor.execute("SET @p_message = '';")
            
            # 调用存储过程
            cursor.execute(
                "CALL sp_borrow_book(%s, %s, %s, @p_status, @p_message)", 
                (p_sno, p_bno, p_ano)
            )
            
            # 检索 OUT 参数结果
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

# 实例化全局单例对象
db = Database()
