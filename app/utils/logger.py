import logging
from app.database.models import async_session
from app.database.models import UserActionLog

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO)

async def log_user_action(user_id: int, action_type: str, action_details: str):
    """
    Функция для записи действий пользователей в лог. Это полезно для отслеживания
    активности пользователей в приложении, таких как команды или ошибки.

    :param user_id: Идентификатор пользователя, чей action логируется.
    :param action_type: Тип действия (например, "search", "error").
    :param action_details: Подробности действия, описание события.
    """
    
    try:
        async with async_session() as session:
            async with session.begin():
                log_entry = UserActionLog(
                    user_id=user_id,
                    action_type=action_type,
                    action_details=action_details,
                )
                session.add(log_entry)
        
            await session.commit()
        
        logging.info(f"Запись действия для пользователя {user_id} успешно сохранена. Тип: {action_type}, Детали: {action_details}")
        
    except Exception as e:
        logging.error(f"Ошибка при записи действия пользователя {user_id}. Ошибка: {e}")
