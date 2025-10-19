import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='meetsburg.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица встреч
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        date TEXT NOT NULL,
                        description TEXT NOT NULL,
                        plan TEXT NOT NULL,
                        password TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                conn.commit()
                logger.info("База данных инициализирована")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")

    async def add_meet(self, user_id: int, title: str, date: str, description: str, plan: str, password: str = None):
        """Добавление новой встречи в базу данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO meets (user_id, title, date, description, plan, password)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, title, date, description, plan, password))
                
                conn.commit()
                meet_id = cursor.lastrowid
                logger.info(f"Встреча добавлена: ID {meet_id} для пользователя {user_id}")
                return meet_id
                
        except Exception as e:
            logger.error(f"Ошибка добавления встречи: {e}")
            return None

    async def get_user_meets(self, user_id: int):
        """Получение всех встреч пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, date, description, plan, password, created_at
                    FROM meets 
                    WHERE user_id = ? AND is_active = TRUE
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                meets = cursor.fetchall()
                return meets
                
        except Exception as e:
            logger.error(f"Ошибка получения встреч: {e}")
            return []

    async def delete_meet(self, meet_id: int, user_id: int):
        """Удаление встречи (мягкое удаление)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE meets 
                    SET is_active = FALSE 
                    WHERE id = ? AND user_id = ?
                ''', (meet_id, user_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Ошибка удаления встречи: {e}")
            return False

db = Database()