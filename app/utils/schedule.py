import asyncio
import schedule
import logging
from app.database.requests import populate_database_from_parsing
from app.utils.logger import log_user_action
from app.utils.statistics import export_users_to_excel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",)


async def job():
    """
    Функция для выполнения задачи по заполнению базы данных из данных парсинга.
    Логирует начало и завершение задачи, а также ошибки, если они возникли.
    
    :return: None
    :raises Exception: Если произошла ошибка в процессе выполнения задачи.
    """
    
    try:
        logging.info("Populate database task started")
        await log_user_action(None, "task_start", "Populate database task started")
        
        await populate_database_from_parsing()

        logging.info("Populate database task completed successfully")
        await log_user_action(None, "task_end", "Populate database task completed successfully")
    except Exception as e:
        logging.error(f"Error in populate database task: {str(e)}")
        await log_user_action(None, "task_error", f"Error in populate database task: {str(e)}")

async def weekly_export():
    """
    Функция для выполнения задачи экспорта статистики пользователей в Excel.
    Логирует начало и завершение задачи, а также ошибки, если они возникли.

    :return: None
    :raises Exception: Если произошла ошибка в процессе выполнения задачи.
    """
    
    try:
        logging.info("User statistics export started")
        await log_user_action(None, "task_start", "User statistics export started")

        await export_users_to_excel()

        logging.info("User statistics export completed successfully")
        await log_user_action(None, "task_end", "User statistics export completed successfully")
    except Exception as e:
        logging.error(f"Error in user statistics export: {str(e)}")
        await log_user_action(None, "task_error", f"Error in user statistics export: {str(e)}")

schedule.every().hour.at(':00').do(lambda: asyncio.create_task(job()))  
schedule.every().hour.at(':30').do(lambda: asyncio.create_task(job())) 
schedule.every().monday.at("00:00").do(lambda: asyncio.create_task(weekly_export())) 

async def scheduler():
    """
    Функция для асинхронного выполнения запланированных задач.
    Ожидает выполнение задач согласно расписанию.
    """
    
    while True:
        schedule.run_pending()  # Запускаем все задачи, которые подошли по времени
        await asyncio.sleep(1)  # Пауза между проверками расписания
