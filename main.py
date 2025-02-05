import asyncio
import logging
from app.core.core import bot, dp
from app.core.handlers import router
from app.database.models import async_main
from app.utils.schedule import scheduler
from app.utils.logger import log_user_action

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",)


async def main():
    """
    Главная асинхронная функция для инициализации бота, подключения роутеров,
    запуска задач и начала polling.
    
    При старте выполняются следующие операции:
    - Инициализация базы данных (async_main)
    - Подключение роутеров
    - Запуск планировщика (scheduler)
    - Старт polling для получения обновлений от бота
    """
    
    try:
        await async_main()  # Инициализация базы данных
        logging.info("Database initialized successfully.") 
        
        dp.include_router(router)  # Подключение роутера с обработчиками
        
        asyncio.create_task(scheduler())  # Запуск планировщика асинхронных задач
        
        logging.info("Bot is starting polling.")
        await dp.start_polling(bot)  # Запуск polling для получения обновлений от бота

    except Exception as e:
        await log_user_action(None, "bot_error", f"Error during bot startup: {str(e)}")
        logging.error(f"Error during bot startup: {str(e)}")  

if __name__ == "__main__":
    """
    Основной блок запуска бота. При завершении работы бота через KeyboardInterrupt
    выполняется логирование события остановки бота.
    """
    
    try:
        logging.info("Starting the bot.") 
        asyncio.run(main()) 
    except KeyboardInterrupt:
        print("Бот выключен!")
        logging.info("Bot has been stopped.") 
