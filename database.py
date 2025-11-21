import sqlite3
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='meetsburg.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection_with_retry(self, max_retries=5, delay=0.1):
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                conn.execute("PRAGMA journal_mode=WAL") 
                conn.execute("PRAGMA foreign_keys=ON")
                return conn
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                raise e
        raise sqlite3.OperationalError("Не удается получить доступ к базе данных")

    def init_db(self):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
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

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meet_id INTEGER NOT NULL,
                    notification_type TEXT NOT NULL, -- '30min' или 'tomorrow'
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(meet_id, notification_type)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("База данных инициализирована")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")

    async def add_meet_with_rooms(self, user_id: int, title: str, date: str, description: str, 
                                 start_time: str, rooms_data: list, max_participants: int = 1, password: str = None):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO meets (user_id, title, date, description, start_time, password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, title, date, description, start_time, password))
            
            meet_id = cursor.lastrowid
            
            for room in rooms_data:
                cursor.execute('''
                    INSERT INTO rooms (meet_id, room_number, start_time, end_time, max_participants)
                    VALUES (?, ?, ?, ?, ?)
                ''', (meet_id, room['room_number'], room['start_time'], room['end_time'], max_participants))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Встреча {meet_id} с {len(rooms_data)} комнатами создана для пользователя {user_id}")
            return meet_id, True
                
        except Exception as e:
            logger.error(f"Ошибка создания встречи с комнатами: {e}")
            return None, False

    async def add_meet(self, user_id: int, title: str, date: str, description: str, start_time: str, password: str = None):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO meets (user_id, title, date, description, start_time, password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, title, date, description, start_time, password))
            
            conn.commit()
            meet_id = cursor.lastrowid
            conn.close()
            
            logger.info(f"Встреча добавлена: ID {meet_id} для пользователя {user_id}")
            return meet_id
                
        except Exception as e:
            logger.error(f"Ошибка добавления встречи: {e}")
            return None

    async def add_rooms(self, meet_id: int, rooms_data: list, max_participants: int = 1):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            for room in rooms_data:
                cursor.execute('''
                    INSERT INTO rooms (meet_id, room_number, start_time, end_time, max_participants)
                    VALUES (?, ?, ?, ?, ?)
                ''', (meet_id, room['room_number'], room['start_time'], room['end_time'], max_participants))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Добавлено {len(rooms_data)} комнат для встречи {meet_id}")
            return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления комнат: {e}")
            return False

    async def get_user_meets(self, user_id: int):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, date, description, start_time, password, created_at
                FROM meets 
                WHERE user_id = ? AND is_active = TRUE
                ORDER BY created_at DESC
            ''', (user_id,))
            
            meets = cursor.fetchall()
            conn.close()
            return meets
                
        except Exception as e:
            logger.error(f"Ошибка получения встреч: {e}")
            return []

    async def get_meet_by_id(self, meet_id: int):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, date, description, start_time, password, user_id
                FROM meets 
                WHERE id = ? AND is_active = TRUE
            ''', (meet_id,))
            
            meet = cursor.fetchone()
            conn.close()
            return meet
                
        except Exception as e:
            logger.error(f"Ошибка получения встречи: {e}")
            return None

    async def get_meet_rooms(self, meet_id: int):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, room_number, start_time, end_time, max_participants, current_participants
                FROM rooms 
                WHERE meet_id = ? AND is_active = TRUE
                ORDER BY room_number
            ''', (meet_id,))
            
            rooms = cursor.fetchall()
            conn.close()
            return rooms
                
        except Exception as e:
            logger.error(f"Ошибка получения комнат: {e}")
            return []

    async def join_room(self, room_id: int, user_id: int, user_name: str):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM room_participants 
                WHERE room_id = ? AND user_id = ?
            ''', (room_id, user_id))
            
            if cursor.fetchone():
                conn.close()
                return False, "Вы уже записаны в эту комнату"
            
            cursor.execute('''
                SELECT max_participants, current_participants 
                FROM rooms WHERE id = ?
            ''', (room_id,))
            
            room_data = cursor.fetchone()
            if room_data and room_data[1] >= room_data[0]:
                conn.close()
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
            conn.close()
            return True, "Вы успешно записались в комнату"
                
        except Exception as e:
            logger.error(f"Ошибка записи в комнату: {e}")
            return False, "Произошла ошибка при записи"

    async def get_room_participants(self, room_id: int):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_name, joined_at 
                FROM room_participants 
                WHERE room_id = ? 
                ORDER BY joined_at
            ''', (room_id,))
            
            participants = cursor.fetchall()
            conn.close()
            return participants
                
        except Exception as e:
            logger.error(f"Ошибка получения участников: {e}")
            return []

    async def delete_meet(self, meet_id: int, user_id: int):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE meets 
                SET is_active = FALSE 
                WHERE id = ? AND user_id = ?
            ''', (meet_id, user_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            return success
                
        except Exception as e:
            logger.error(f"Ошибка удаления встречи: {e}")
            return False

    async def get_user_bookings(self, user_id: int):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    m.id, m.title, m.date, m.start_time,
                    r.room_number, r.start_time, r.end_time,
                    rp.joined_at
                FROM room_participants rp
                JOIN rooms r ON rp.room_id = r.id
                JOIN meets m ON r.meet_id = m.id
                WHERE rp.user_id = ? AND m.is_active = TRUE AND r.is_active = TRUE
                ORDER BY rp.joined_at DESC
            ''', (user_id,))
            
            bookings = cursor.fetchall()
            conn.close()
            return bookings
                
        except Exception as e:
            logger.error(f"Ошибка получения записей пользователя: {e}")
            return []

    async def is_meet_active(self, meet_id: int):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT date FROM meets 
                WHERE id = ? AND is_active = TRUE
            ''', (meet_id,))
            
            result = cursor.fetchone()
            if not result:
                return False
                
            meet_date = datetime.strptime(result[0], '%d-%m-%Y').date()
            current_date = datetime.now().date()
            
            return meet_date >= current_date
                
        except Exception as e:
            logger.error(f"Ошибка проверки активности встречи: {e}")
            return False

    async def get_meets_by_date(self, date: str):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, date, description, start_time, password, user_id
                FROM meets 
                WHERE date = ? AND is_active = TRUE
            ''', (date,))
            
            meets = cursor.fetchall()
            conn.close()
            return meets
            
        except Exception as e:
            logger.error(f"Ошибка получения встреч по дате: {e}")
            return []

    async def get_room_participant_ids(self, room_id: int):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id FROM room_participants 
                WHERE room_id = ?
            ''', (room_id,))
            
            participants = cursor.fetchall()
            conn.close()
            return [participant[0] for participant in participants]
            
        except Exception as e:
            logger.error(f"Ошибка получения ID участников комнаты: {e}")
            return []

    async def get_upcoming_meets(self, target_datetime: str):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            date_part = target_datetime.split(' ')[0]
            time_part = target_datetime.split(' ')[1]
            
            cursor.execute('''
                SELECT id, title, date, description, start_time, password, user_id
                FROM meets 
                WHERE date = ? AND start_time = ? AND is_active = TRUE
            ''', (date_part, time_part))
            
            meets = cursor.fetchall()
            conn.close()
            return meets
            
        except Exception as e:
            logger.error(f"Ошибка получения предстоящих встреч: {e}")
            return []

    async def is_notification_sent(self, meet_id: int, notification_type: str):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM sent_notifications 
                WHERE meet_id = ? AND notification_type = ?
            ''', (meet_id, notification_type))
            
            result = cursor.fetchone()
            conn.close()
            return result is not None
            
        except Exception as e:
            logger.error(f"Ошибка проверки отправленного уведомления: {e}")
            return False

    async def mark_notification_sent(self, meet_id: int, notification_type: str):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO sent_notifications (meet_id, notification_type)
                VALUES (?, ?)
            ''', (meet_id, notification_type))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отметки отправленного уведомления: {e}")
            return False

db = Database()