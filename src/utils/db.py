import os
import streamlit as st
from mysql.connector import pooling, Error
from dotenv import load_dotenv
from typing import List, Dict, Any

# --- Configuration ---
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "student_ai_notes")

class DatabaseManager:
    """A class to manage interactions with the MySQL database."""

    def __init__(self):
        """Initializes the connection pool."""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="student_ai_pool",
                pool_size=5,
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset="utf8mb4"
            )
        except Error as e:
            st.error(f"Error creating connection pool: {e}")
            self.pool = None

    def save_chat(self, user_id: str, question: str, answer: str):
        """Saves a chat interaction to the database."""
        # This query now uses 'user_email' to match your database column
        sql = "INSERT INTO chat_history (user_email, question, answer) VALUES (%s, %s, %s)"
        try:
            with self.pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (user_id, question, answer))
                conn.commit()
        except Error as e:
            st.error(f"Error saving chat: {e}")

    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the most recent chat history for a given user."""
        # This query now filters by 'user_email' to match your database column
        sql = """
        SELECT question, answer, timestamp 
        FROM chat_history 
        WHERE user_email = %s 
        ORDER BY timestamp DESC 
        LIMIT %s
        """
        try:
            with self.pool.get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(sql, (user_id, limit))
                    return cursor.fetchall()
        except Error as e:
            st.error(f"Error fetching chat history: {e}")
            return []

@st.cache_resource
def get_db_manager() -> DatabaseManager:
    """Returns a singleton instance of the DatabaseManager."""
    return DatabaseManager()