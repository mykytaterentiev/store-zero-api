import os
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

DATABASE_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'transaction_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Aqsw2143'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

try:
    conn_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        **DATABASE_CONFIG
    )
    if conn_pool:
        print("Connection pool created successfully")
except Exception as e:
    print(f"Error creating connection pool: {e}")
    raise e

def get_db_conn():
    try:
        conn = conn_pool.getconn()
        if conn:
            print("Successfully received connection from pool")
        return conn
    except Exception as e:
        print(f"Error getting connection from pool: {e}")
        return None

def release_db_conn(conn):
    if conn:
        conn_pool.putconn(conn)
