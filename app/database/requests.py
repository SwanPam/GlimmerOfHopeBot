import logging
from datetime import datetime
from sqlalchemy import or_, select, text
from app.database.models import (async_session, Tag, Brand, Vape_Tage, Vape,
                                 Vaporizer, VaporizerBrand, VaporizerResistance,
                                 User)
from app.utils.parsing import (vapes_db, tags_db, vapes_tags_db, brands_db,
                               vaporizers_db, vaporizers_brand_db, resistances_db)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",)

availability_condition = (
    Vape.availability_45_50_60.isnot(None) | Vape.availability_20.isnot(None)
)

availability_condition_on_hand = or_(
    Vape.availability_20 == 1, Vape.availability_20 == -1,
    Vape.availability_45_50_60 == 1, Vape.availability_45_50_60 == -1
)

availability_condition_to_order = or_(
    Vape.availability_20 == 0, Vape.availability_45_50_60 == 0,
    Vape.availability_20 == 1, Vape.availability_45_50_60 == 1 
)


async def populate_database_from_parsing():
    """
    Заполняет базу данных данными из парсинга, удаляя предыдущие записи.
    Ошибки при добавлении отдельных записей логируются, остальные продолжают добавляться.
    """

    try:
        logging.info(f"Начало добавления данных в базу данных. Время: {datetime.now()}")

        async with async_session() as session:
            await session.execute(text('DELETE FROM tags'))
            await session.execute(text('DELETE FROM brands'))
            await session.execute(text('DELETE FROM vapes'))
            await session.execute(text('DELETE FROM vapes_tags'))
            await session.execute(text('DELETE FROM vaporizers'))
            await session.execute(text('DELETE FROM vaporizer_brands'))
            await session.execute(text('DELETE FROM vaporizer_resistances'))
            await session.commit()

            logging.info(f"Старые записи успешно удалены. Время: {datetime.now()}")

        async with async_session() as session:
            logging.info(f"Начало добавления новых записей. Время: {datetime.now()}")

            # Добавление тегов
            for tag in tags_db.values():
                try:
                    session.add(Tag(name=tag))
                except Exception as e:
                    logging.warning(f"Ошибка при добавлении тега '{tag}': {e}")

            # Добавление брендов
            for brand in brands_db.values():
                try:
                    session.add(Brand(name=brand))
                except Exception as e:
                    logging.warning(f"Ошибка при добавлении бренда '{brand}': {e}")

            # Добавление вейпов
            for vape in vapes_db:
                try:
                    if vape[2] is None:
                        continue
                    session.add(Vape(name=vape[1],
                                     brand_id=vape[2],
                                     brand_line_up=vape[3],
                                     availability_45_50_60=vape[4],
                                     availability_20=vape[5],
                                     price=vape[6]))
                except Exception as e:
                    logging.warning(f"Ошибка при добавлении вейпа '{vape}': {e}")

            # Теги к вейпам
            for vape_tag in vapes_tags_db:
                try:
                    session.add(Vape_Tage(vape_id=vape_tag[0], tag_id=vape_tag[1]))
                except Exception as e:
                    logging.warning(f"Ошибка при добавлении vape_tag '{vape_tag}': {e}")

            # Бренды испарителей
            for brand in vaporizers_brand_db:
                try:
                    session.add(VaporizerBrand(id=brand[0], name=brand[1]))
                except Exception as e:
                    logging.warning(f"Ошибка при добавлении бренда испарителя '{brand}': {e}")

            # Сопротивления испарителей
            for resistance in resistances_db:
                try:
                    session.add(VaporizerResistance(id=resistance[0], value=resistance[1]))
                except Exception as e:
                    logging.warning(f"Ошибка при добавлении сопротивления '{resistance}': {e}")

            # Испарители
            for vaporizer in vaporizers_db:
                try:
                    session.add(Vaporizer(brand_id=vaporizer[0],
                                          resistance_id=vaporizer[1],
                                          price=vaporizer[2]))
                except Exception as e:
                    logging.warning(f"Ошибка при добавлении испарителя '{vaporizer}': {e}")

            await session.commit()

            logging.info(f"Новые данные успешно добавлены в базу данных. Время: {datetime.now()}")

    except Exception as e:
        logging.error(f"Произошла ошибка при добавлении данных: {e}")



async def get_brands(search_in: str):
    """
    Получение списка брендов, имеющихся в наличии или под заказ.

    :param search_in: Указывает, где искать бренды ('on_hand' - в наличии, 'to_order' - под заказ).
    :type search_in: str
    :return: Список объектов Brand, удовлетворяющих условиям наличия.
    :rtype: list[Brand]
    """
    
    try:
        async with async_session() as session:
            if search_in == 'on_hand':
                availability_condition = availability_condition_on_hand
            elif search_in == 'to_order':
                availability_condition = availability_condition_to_order
            result = await session.execute(
                select(Brand).join(Vape).where(availability_condition).distinct()
            )
            return result.scalars().all()
    except Exception as e:
        logging.error(f"Error in get_brands: {e}")
        return []

async def get_vapes_by_brand(brand_id, search_in: str):
    """
    Получение списка вейпов по ID бренда.

    :param brand_id: Идентификатор бренда.
    :type brand_id: int
    :param search_in: Указывает, где искать вейпы ('on_hand' - в наличии, 'to_order' - под заказ).
    :type search_in: str
    :return: Список объектов Vape, относящихся к указанному бренду и удовлетворяющих условиям наличия.
    :rtype: list[Vape]
    """
    
    try:
        async with async_session() as session:
            if search_in == 'on_hand':
                availability_condition = availability_condition_on_hand
            elif search_in == 'to_order':
                availability_condition = availability_condition_to_order
            result = await session.execute(
                select(Vape).where(Vape.brand_id == brand_id, availability_condition)
            )
            return result.scalars().all()
    except Exception as e:
        logging.error(f"Error in get_vapes_by_brand: {e}")
        return []

async def get_all_tags_with_vapes(search_in: str):
    """
    Получение всех тегов, связанных с вейпами, в зависимости от наличия.

    :param search_in: Указывает, где искать теги ('on_hand' - в наличии, 'to_order' - под заказ).
    :type search_in: str
    :return: Список объектов Tag, которые связаны с хотя бы одним вейпом в заданной категории наличия.
    :rtype: list[Tag]
    """
    
    try:
        async with async_session() as session:
            if search_in == 'on_hand':
                availability_condition = availability_condition_on_hand
            elif search_in == 'to_order':
                availability_condition = availability_condition_to_order
                
            result = await session.execute(
                select(Tag)
                .join(Vape_Tage)
                .join(Vape)
                .where(availability_condition)
                .distinct()
            )
            return result.scalars().all()
    except Exception as e:
        logging.error(f"Error in get_all_tags_with_vapes: {e}")
        return []

async def get_vapes_by_tag(tag_id: int, search_in: str):
    """
    Поиск вейпов по ID тега.

    :param tag_id: Идентификатор тега.
    :type tag_id: int
    :param search_in: Указывает, где искать вейпы ('on_hand' - в наличии, 'to_order' - под заказ).
    :type search_in: str
    :return: Список объектов Vape, соответствующих заданному тегу и условиям наличия.
    :rtype: list[Vape]
    """
    
    try:
        async with async_session() as session:
            if search_in == 'on_hand':
                availability_condition = availability_condition_on_hand
            elif search_in == 'to_order':
                availability_condition = availability_condition_to_order
            
            result = await session.execute(
                select(Vape)
                .join(Vape_Tage)
                .where(Vape_Tage.tag_id == tag_id, availability_condition)
            )
            return result.scalars().all()
    except Exception as e:
        logging.error(f"Error in get_vapes_by_tag: {e}")
        return []

async def get_vapes_by_flavor(flavor: str, search_in: str):
    """
    Поиск вейпов по вкусу (независимо от регистра).

    :param flavor: Вкус, который нужно найти (поиск осуществляется по первым 4 символам).
    :type flavor: str
    :param search_in: Указывает, где искать вейпы ('on_hand' - в наличии, 'to_order' - под заказ).
    :type search_in: str
    :return: Список объектов Vape, содержащих указанный вкус в названии и удовлетворяющих условиям наличия.
    :rtype: list[Vape]
    """
    
    try:
        async with async_session() as session:
            if search_in == 'on_hand':
                availability_condition = availability_condition_on_hand
            elif search_in == 'to_order':
                availability_condition = availability_condition_to_order
            
            result = await session.execute(
                select(Vape)
                .where(
                    or_(Vape.name.ilike(f"%{flavor.lower()[:4]}%"), availability_condition),
                    Vape.name.ilike(f"%{flavor.capitalize()[:4]}%"), availability_condition)
                )
            return result.scalars().all()
    except Exception as e:
        logging.error(f"Error in get_vapes_by_flavor: {e}")
        return []



async def is_exists(user_id) -> bool:
    """
    Проверяет, существует ли пользователь в базе данных.
    :param user_id: ID пользователя
    :return: True, если пользователь существует, иначе False
    """
    try:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            return user is not None
    except Exception as e:
        logging.error(f"Error in is_exists: {e}")
        return False

async def add_user(user_id: int, username: str):
    """
    Добавляет нового пользователя в базу данных.
    :param user_id: ID пользователя
    :param username: Имя пользователя
    """
    try:
        async with async_session() as session:
            session.add(User(id=user_id, username=username))
            await session.commit()
    except Exception as e:
        logging.error(f"Error in add_user: {e}")

async def get_users():
    """
    Получает список всех пользователей.
    :return: Список пользователей
    """
    try:
        async with async_session() as session:
            result = await session.execute(select(User))
            return result.scalars().all()
    except Exception as e:
        logging.error(f"Error in get_users: {e}")
        return []

async def increment_command_count(user_id: int):
    """
    Увеличивает счетчик команд пользователя.
    :param user_id: ID пользователя
    """
    try:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if user:
                user.command_count += 1
                await session.commit()
    except Exception as e:
        logging.error(f"Error in increment_command_count: {e}")
