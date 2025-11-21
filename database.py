import sqlite3
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='meetsburg.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # cursor.execute('DROP TABLE IF EXISTS room_participants')
                # cursor.execute('DROP TABLE IF EXISTS rooms')
                # cursor.execute('DROP TABLE IF EXISTS meets')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        date TEXT NOT NULL,
                        description TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        password TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rooms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meet_id INTEGER NOT NULL,
                        room_number INTEGER NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        max_participants INTEGER DEFAULT 1,
                        current_participants INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE,
                        FOREIGN KEY (meet_id) REFERENCES meets (id) ON DELETE CASCADE
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS room_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        room_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT NOT NULL,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE CASCADE
                    )
                ''')
                
                conn.commit()
                logger.info("База данных инициализирована с новой структурой")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")

    async def add_meet(self, user_id: int, title: str, date: str, description: str, start_time: str, password: str = None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO meets (user_id, title, date, description, start_time, password)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, title, date, description, start_time, password))
                
                conn.commit()
                meet_id = cursor.lastrowid
                logger.info(f"Встреча добавлена: ID {meet_id} для пользователя {user_id}")
                return meet_id
                
        except Exception as e:
            logger.error(f"Ошибка добавления встречи: {e}")
            return None

    async def add_rooms(self, meet_id: int, rooms_data: list, max_participants: int = 1):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for room in rooms_data:
                    cursor.execute('''
                        INSERT INTO rooms (meet_id, room_number, start_time, end_time, max_participants)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (meet_id, room['room_number'], room['start_time'], room['end_time'], max_participants))
                
                conn.commit()
                logger.info(f"Добавлено {len(rooms_data)} комнат для встречи {meet_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления комнат: {e}")
            return False

    async def get_user_meets(self, user_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, date, description, start_time, password, created_at
                    FROM meets 
                    WHERE user_id = ? AND is_active = TRUE
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                meets = cursor.fetchall()
                return meets
                
        except Exception as e:
            logger.error(f"Ошибка получения встреч: {e}")
            return []

    async def get_meet_by_id(self, meet_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, date, description, start_time, password, user_id
                    FROM meets 
                    WHERE id = ? AND is_active = TRUE
                ''', (meet_id,))
                
                meet = cursor.fetchone()
                return meet
                
        except Exception as e:
            logger.error(f"Ошибка получения встречи: {e}")
            return None

    async def get_meet_rooms(self, meet_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, room_number, start_time, end_time, max_participants, current_participants
                    FROM rooms 
                    WHERE meet_id = ? AND is_active = TRUE
                    ORDER BY room_number
                ''', (meet_id,))
                
                rooms = cursor.fetchall()
                return rooms
                
        except Exception as e:
            logger.error(f"Ошибка получения комнат: {e}")
            return []

    async def join_room(self, room_id: int, user_id: int, user_name: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id FROM room_participants 
                    WHERE room_id = ? AND user_id = ?
                ''', (room_id, user_id))
                
                if cursor.fetchone():
                    return False, "Вы уже записаны в эту комнату"
                
                cursor.execute('''
                    SELECT max_participants, current_participants 
                    FROM rooms WHERE id = ?
                ''', (room_id,))
                
                room_data = cursor.fetchone()
                if room_data and room_data[1] >= room_data[0]:
                    return False, "В комнате нет свободных мест"
                
                cursor.execute('''
                    INSERT INTO room_participants (room_id, user_id, user_name)
                    VALUES (?, ?, ?)
                ''', (room_id, user_id, user_name))
                
                cursor.execute('''
                    UPDATE rooms 
                    SET current_participants = current_participants + 1 
                    WHERE id = ?
                ''', (room_id,))
                
                conn.commit()
                return True, "Вы успешно записались в комнату"
                
        except Exception as e:
            logger.error(f"Ошибка записи в комнату: {e}")
            return False, "Произошла ошибка при записи"

    async def get_room_participants(self, room_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT user_name, joined_at 
                    FROM room_participants 
                    WHERE room_id = ? 
                    ORDER BY joined_at
                ''', (room_id,))
                
                participants = cursor.fetchall()
                return participants
                
        except Exception as e:
            logger.error(f"Ошибка получения участников: {e}")
            return []

    async def delete_meet(self, meet_id: int, user_id: int):
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