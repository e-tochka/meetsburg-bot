from aiogram import Bot
from database import db
from datetime import datetime, timedelta
import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def get_tomorrow_rooms(self) -> List[tuple]:
        try:
            now = datetime.now()
            
            if now.hour >= 12:
                rooms = await db.get_tomorrow_rooms()
                logger.info(f"Поиск комнат на завтра: найдено {len(rooms)}")
            else:
                today_rooms = await self._get_today_rooms_after_now()
                tomorrow_rooms = await db.get_tomorrow_rooms()
                rooms = today_rooms + tomorrow_rooms
                logger.info(f"Поиск комнат: сегодня после текущего времени + завтра. Найдено: {len(rooms)}")
                
            return rooms
            
        except Exception as e:
            logger.error(f"Ошибка получения комнат на завтра: {e}")
            return []

    async def _get_today_rooms_after_now(self) -> List[tuple]:
        try:
            now = datetime.now()
            today_date = now.strftime('%d-%m-%Y')
            current_time_str = now.strftime('%H:%M')
            
            conn = db.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT r.id, r.room_number, r.start_time, r.end_time,
                       m.id, m.title, m.date, m.description, m.user_id
                FROM rooms r
                JOIN meets m ON r.meet_id = m.id
                WHERE m.date = ? AND m.is_active = TRUE AND r.is_active = TRUE
            ''', (today_date,))
            
            all_today_rooms = cursor.fetchall()
            conn.close()
            
            filtered_rooms = []
            for room in all_today_rooms:
                room_id, room_number, start_time, end_time, meet_id, title, date, description, user_id = room
                if self._is_time_after(start_time, current_time_str):
                    filtered_rooms.append(room)
                    
            return filtered_rooms
            
        except Exception as e:
            logger.error(f"Ошибка получения сегодняшних комнат: {e}")
            return []

    async def get_upcoming_rooms(self, minutes: int = 30) -> List[tuple]:
        try:
            rooms = await db.get_upcoming_rooms(minutes)
            logger.info(f"Найдено комнат в ближайшие {minutes} минут: {len(rooms)}")
            return rooms
            
        except Exception as e:
            logger.error(f"Ошибка получения предстоящих комнат: {e}")
            return []

    def _is_time_after(self, time1: str, time2: str) -> bool:
        try:
            t1 = datetime.strptime(time1, '%H:%M')
            t2 = datetime.strptime(time2, '%H:%M')
            return t1 >= t2
        except ValueError:
            return False

    async def send_tomorrow_notification(self):
        try:
            tomorrow_rooms = await self.get_tomorrow_rooms()
            
            if not tomorrow_rooms:
                logger.info("Нет комнат для уведомлений на завтра")
                return

            notification_count = 0
            for room in tomorrow_rooms:
                room_id, room_number, start_time, end_time, meet_id, title, date, description, user_id = room
                
                if await db.is_notification_sent(room_id, 'tomorrow'):
                    logger.info(f"Уведомление на завтра для комнаты {room_id} уже отправлено")
                    continue
                
                recipients = await db.get_room_participants_with_creator(room_id)
                
                message_text = (
                    "🔔 <b>Напоминание о встрече</b>\n\n"
                    f"📝 <b>{title}</b>\n"
                    f"🚪 Комната {room_number}\n"
                    f"📅 Завтра ({date})\n"
                    f"⏰ В {start_time}\n"
                    f"📋 {description}\n\n"
                    "Не забудьте подготовиться! 🎯"
                )
                
                sent_successfully = True
                for recipient_id in recipients:
                    try:
                        await self.bot.send_message(
                            chat_id=recipient_id,
                            text=message_text,
                            parse_mode="HTML"
                        )
                        logger.info(f"Отправлено уведомление пользователю {recipient_id} о комнате {room_id}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки уведомления пользователю {recipient_id}: {e}")
                        sent_successfully = False
                
                if sent_successfully:
                    await db.mark_notification_sent(room_id, 'tomorrow')
                    notification_count += 1
                        
            logger.info(f"Всего отправлено {notification_count} уведомлений о комнатах на завтра")
            
        except Exception as e:
            logger.error(f"Ошибка в send_tomorrow_notification: {e}")

    async def send_30min_notification(self):
        try:
            upcoming_rooms = await self.get_upcoming_rooms(30)
            
            if not upcoming_rooms:
                return

            notification_count = 0
            for room in upcoming_rooms:
                room_id, room_number, start_time, end_time, meet_id, title, date, description, user_id = room
                
                if await db.is_notification_sent(room_id, '30min'):
                    logger.info(f"30-минутное уведомление для комнаты {room_id} уже отправлено")
                    continue
                
                recipients = await db.get_room_participants_with_creator(room_id)
                
                now = datetime.now()
                room_date = datetime.strptime(date, '%d-%m-%Y').date()
                today_text = "Сегодня" if room_date == now.date() else "Завтра"
                
                message_text = (
                    "⏰ <b>Скоро начинается встреча!</b>\n\n"
                    f"📝 <b>{title}</b>\n"
                    f"🚪 Комната {room_number}\n"
                    f"📅 {today_text} ({date})\n"
                    f"⏰ Через 30 минут ({start_time})\n"
                    f"📋 {description}\n\n"
                    "Приготовьтесь к участию! 🚀"
                )
                
                sent_successfully = True
                for recipient_id in recipients:
                    try:
                        await self.bot.send_message(
                            chat_id=recipient_id,
                            text=message_text,
                            parse_mode="HTML"
                        )
                        logger.info(f"Отправлено 30-минутное уведомление пользователю {recipient_id} о комнате {room_id}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки 30-минутного уведомления пользователю {recipient_id}: {e}")
                        sent_successfully = False
                
                if sent_successfully:
                    await db.mark_notification_sent(room_id, '30min')
                    notification_count += 1
                        
            if notification_count > 0:
                logger.info(f"Всего отправлено {notification_count} 30-минутных уведомлений")
                
        except Exception as e:
            logger.error(f"Ошибка в send_30min_notification: {e}")

async def start_notification_scheduler(bot: Bot):
    notification_service = NotificationService(bot)
    last_tomorrow_notification = None
    
    logger.info("🚀 Планировщик уведомлений запущен (по комнатам)")
    
    while True:
        try:
            now = datetime.now()
            
            if now.hour == 12 and now.minute == 0:
                today_date = now.date()
                if last_tomorrow_notification != today_date:
                    logger.info("⏰ 12:00 - отправка уведомлений о комнатах на завтра...")
                    await notification_service.send_tomorrow_notification()
                    last_tomorrow_notification = today_date
                    await asyncio.sleep(65) 
                    continue
            
            await notification_service.send_30min_notification()
            
            await asyncio.sleep(60)  
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике уведомлений: {e}")
            await asyncio.sleep(60)