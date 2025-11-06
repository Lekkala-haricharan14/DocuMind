import os
import streamlit as st
from mysql.connector import pooling, Error
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_SSL_CA = os.getenv("DB_SSL_CA")   # ✅ new


class DatabaseManager:
    """A class to manage MySQL database interactions using a connection pool."""

    def __init__(self):
        """Initialize connection pool with SSL support."""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="student_ai_cloud_pool",
                pool_size=5,
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset="utf8mb4",
                autocommit=True,
                ssl_ca=DB_SSL_CA      # ✅ required for Aiven SSL connection
            )
        except Error as e:
            st.error(f"❌ Error creating MySQL connection pool: {e}")
            self.pool = None

    # ✅ Helper: Get connection safely
    def _get_connection(self):
        if not self.pool:
            st.error("❌ Database connection pool is not initialized.")
            return None
        try:
            return self.pool.get_connection()
        except Error as e:
            st.error(f"❌ Error obtaining DB connection: {e}")
            return None

    # ✅ Insert chat history
    def save_chat(self, user_id: str, question: str, answer: str):
        sql = """
            INSERT INTO chat_history (user_email, question, answer)
            VALUES (%s, %s, %s)
        """
        conn = self._get_connection()
        if not conn:
            return
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_id, question, answer))
        except Error as e:
            st.error(f"❌ Error saving chat: {e}")
        finally:
            conn.close()

    # ✅ Retrieve chat history
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        sql = """
            SELECT question, answer, timestamp 
            FROM chat_history 
            WHERE user_email = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
        """
        conn = self._get_connection()
        if not conn:
            return []

        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(sql, (user_id, limit))
                return cursor.fetchall()
        except Error as e:
            st.error(f"❌ Error fetching history: {e}")
            return []
        finally:
            conn.close()


@st.cache_resource
def get_db_manager() -> DatabaseManager:
    """Returns a cached instance of the DatabaseManager."""
    return DatabaseManager()
