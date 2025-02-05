import pandas as pd
import calendar
import logging
from datetime import datetime
from sqlalchemy import select
from app.database.models import async_session, User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",)


async def export_users_to_excel():
    """
    Функция для экспорта статистики пользователей в Excel файл. Она извлекает данные 
    о пользователях (ID, первое и последнее посещение, количество команд) из базы данных 
    и сохраняет их в файл с названием, включающим текущую дату и день недели.

    :return: str - имя файла, в который были сохранены данные, или None, если данных нет
             или произошла ошибка.
    """
    
    try:
        async with async_session() as session:
            result = await session.execute(select(User.id, User.first_seen, User.last_seen, User.command_count))
            users = result.all()

        if not users:
            logging.info("Нет данных для экспорта.")
            return None

        df = pd.DataFrame(users, columns=["user_id", "first_seen", "last_seen", "command_count"])

        now = datetime.now()
        month_name = calendar.month_name[now.month]  
        day = calendar.day_name[now.weekday()]  
        year = now.year

        file_name = f"Статистика посещения пользователями за неделю на {day} {month_name} {year}.xlsx"

        try:
            df.to_excel(file_name, index=False)
            logging.info(f"Файл {file_name} успешно сохранён.")
        except Exception as e:
            logging.error(f"Ошибка при сохранении файла: {e}")
            return None

        return file_name

    except Exception as e:
        logging.error(f"Произошла ошибка при экспорте данных: {e}")
        return None
