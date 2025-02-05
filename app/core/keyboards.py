import random
import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton)
from app.utils.texts import EMOJIS


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",)

BRANDS_PER_PAGE = 3
TAGS_PER_PAGE = 3

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💨 Жидкости', callback_data='vapes')],
    [InlineKeyboardButton(text='✉️ Написать менеджеру', callback_data='write to the manager')],
])

product_selection = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⏳ На заказ', callback_data='vapes_to_order')],
    [InlineKeyboardButton(text='🚀 В наличии', callback_data='vapes_on_hand')],
    [InlineKeyboardButton(text='🏠 Главное меню', callback_data='menu')]
])

async def get_search_menu_keyboard(product_selection: str):
    """
    Создание клавиатуры для меню поиска жидкостей для вейпа.

    :param product_selection: Определяет категорию выбора продукта ('on_hand' - в наличии, 'to_order' - под заказ).
    :type product_selection: str
    :return: Объект InlineKeyboardMarkup с кнопками поиска.
    :rtype: InlineKeyboardMarkup
    """
    
    try:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔍 Поиск по тегу', callback_data=f'search_by_tag_{product_selection}')],
            [InlineKeyboardButton(text='🔍 Поиск по названию', callback_data=f'search_by_flavor_{product_selection}')],
            [InlineKeyboardButton(text='🔍 Поиск по бренду', callback_data=f'search_by_brand_{product_selection}')],
            [InlineKeyboardButton(text='🏠 Главное меню', callback_data='menu')]
        ])
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры поиска: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[])

async def get_brands_keyboard(brands, search_in):
    """
    Создание клавиатуры для выбора бренда.

    :param brands: Список брендов.
    :param search_in: Категория поиска ('on_hand' или 'to_order').
    :return: Объект InlineKeyboardMarkup с кнопками брендов.
    """
    
    try:
        builder = InlineKeyboardBuilder()

        for brand in brands:
            emoji = random.choice(EMOJIS["brand"])
            builder.button(text=f'{emoji} {brand.name}', callback_data=f"brand_{brand.id}_{search_in}")

        builder.adjust(BRANDS_PER_PAGE)

        builder.row(InlineKeyboardButton(text=EMOJIS["search_by_tag"] + "Назад к поиску", callback_data=f"vapes_{search_in}"))
        builder.row(InlineKeyboardButton(text=EMOJIS["home"] + " Главное меню", callback_data="menu"))

        return builder.as_markup()

    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры брендов: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[])

async def get_tags_keyboard(tags, search_in):
    """
    Создание клавиатуры для выбора тега.

    :param tags: Список тегов.
    :param search_in: Категория поиска ('on_hand' или 'to_order').
    :return: Объект InlineKeyboardMarkup с кнопками тегов.
    """
    
    try:
        builder = InlineKeyboardBuilder()

        for tag in tags:
            builder.button(text=f'{tag.name}', callback_data=f"tag_{tag.id}_{search_in}")

        builder.adjust(TAGS_PER_PAGE)
        builder.row(InlineKeyboardButton(text=EMOJIS["search_by_tag"] + "Назад к поиску", callback_data=f"vapes_{search_in}"))
        builder.row(InlineKeyboardButton(text=EMOJIS["home"] + " Главное меню", callback_data="menu"))

        return builder.as_markup()

    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры тегов: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[])

async def generate_pagination(data, page, page_size, callback_prefix, search_in):
    """
    Генерация текста и клавиатуры для пагинации.

    :param data: Список объектов для отображения.
    :param page: Текущая страница.
    :param page_size: Количество элементов на странице.
    :param callback_prefix: Префикс для callback-данных.
    :param search_in: Категория поиска ('on_hand', 'to_order', 'statistics').
    :return: Кортеж (текст, клавиатура).
    """
    try:
        total_pages = (len(data) + page_size - 1) // page_size
        page = max(1, min(page, total_pages))
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        current_page_data = data[start_index:end_index]
        
        text = f"📚 Страница {page} из {total_pages}\n\n"
        for item in current_page_data:
            if search_in == 'statistics':
                text += (f"🆔 User ID: {item.id}\n"
                        f"👤 Username: {item.username}\n"
                        f"📅 First seen: {item.first_seen}\n"
                        f"🕒 Last seen: {item.last_seen}\n"
                        f"📊 Command count: {item.command_count}\n"
                        "──────────────────────────\n")
            elif search_in in ('on_hand', 'to_order'):
                availability_set = set()

                availability_20_check = (-1 if search_in == 'on_hand' else 0)
                availability_45_50_60_check = (-1 if search_in == 'on_hand' else 0)

                if item.availability_20 in (1, availability_20_check):
                    availability_set.add("20 MG")
                if item.availability_45_50_60 in (1, availability_45_50_60_check):
                    availability_set.add("45, 50, 60 MG")

                availability = f"📏 {', '.join(availability_set)}" if availability_set else "📏 Нет в наличии"

                text += f"✨ {item.name}\n💰 {item.price} руб.\n {availability}\n\n"


        builder = InlineKeyboardBuilder()
        
        if total_pages > 1:
            builder.button(
                text=EMOJIS["pagination_back"] + " Назад",
                callback_data=f"page_{total_pages if page == 1 else (page - 1)}_{callback_prefix}_{search_in}",
            )
            builder.button(
                text="Вперёд " + EMOJIS["pagination_forward"],
                callback_data=f"page_{1 if page == total_pages else (page + 1)}_{callback_prefix}_{search_in}",
            )

        # Кнопки возврата
        return_buttons = {
            "brand": "🔍 Вернуться к брендам",
            "tag": "🔍 Вернуться к тегам",
            "flavor": "🔍 Вернуться к поиску",
        }

        for key, text_button in return_buttons.items():
            if key in callback_prefix:
                builder.button(text=text_button, callback_data=f"search_by_{key}_{search_in}")
                break

        builder.button(text=EMOJIS["home"] + " Главное меню", callback_data="menu")

        builder.adjust(2, 1, 1) if total_pages > 1 else builder.adjust(1, 1)
        
        return text, builder.as_markup()
    
    except Exception as e:
        logging.error(f"Ошибка при генерации пагинации: {e}")
        return "⚠ Ошибка при загрузке данных.", InlineKeyboardMarkup(inline_keyboard=[])
