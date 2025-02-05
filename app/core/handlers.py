import logging

from aiogram import F, Router
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, 
                           FSInputFile)
from aiogram.filters import CommandStart, Command

import app.core.keyboards as kb
import app.database.requests as rq
from app.utils.statistics import export_users_to_excel
from app.utils.logger import log_user_action
from app.utils.texts import (WELCOME_TEXT, SEARCH_MENU_TEXT, SEARCH_BY_TAG_TEXT, 
                             NO_VAPES_FOUND_TEXT, WRITE_TO_MANAGER_TEXT, VAPES_CATEGORY_TEXT, 
                             CANCEL_BUTTON_TEXT, VAPES_PRODUCT_SELECTION_TEXT)

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",)

router = Router()

@router.message(CommandStart())
@router.callback_query(F.data == "menu")
async def cmd_start(update: Message | CallbackQuery):
    """
    Обработчик команды /start и нажатия кнопки 'Меню'.
    
    Проверяет, существует ли пользователь в базе данных, добавляет его, если нет,
    и логирует действия пользователя. Затем отправляет приветственное сообщение с кнопками.

    :param update: Сообщение или запрос с нажатием кнопки.
    :type update: Message | CallbackQuery
    :return: None
    """
    
    try:
        user_id = update.from_user.id
        username = update.from_user.username

        if not await rq.is_exists(user_id):
            await rq.add_user(user_id, username)
            
            action_type = "add_user"
            action_details = f"User: id={user_id}, username={username} added to database"
            await log_user_action(user_id, action_type, action_details)
        
        action_type = "command_start"
        action_details = "User started the bot or pressed the menu button"
        await log_user_action(user_id, action_type, action_details)

        await rq.increment_command_count(user_id)

        if isinstance(update, Message):
            await update.answer(WELCOME_TEXT, reply_markup=kb.main_menu)
        elif isinstance(update, CallbackQuery):
            await update.message.answer(WELCOME_TEXT, reply_markup=kb.main_menu)
            await update.answer()

    except Exception as e:
        logging.error(f"Error in cmd_start: {str(e)}")
        if isinstance(update, CallbackQuery):
            await update.answer("Произошла ошибка при обработке вашего запроса.")
        else:
            await update.answer("Произошла ошибка при обработке вашего запроса.")

@router.message(Command('update_data'))
async def update_data(message: Message):
    """
    Обработчик команды /update_data.

    Выполняет обновление данных в базе данных, логирует действие пользователя,
    и отправляет сообщение об успешном обновлении данных.

    :param message: Сообщение от пользователя.
    :type message: Message
    :return: None
    """
    
    try:
        await rq.populate_database_from_parsing()

        user_id = message.from_user.id
        action_type = "update_data"
        action_details = "Data was successfully updated by the user"
        await log_user_action(user_id, action_type, action_details)
        await message.answer('Данные успешно добавлены')

    except Exception as e:
        logging.error(f"Error in update_data: {str(e)}")
        await message.answer("Произошла ошибка при обновлении данных. Пожалуйста, попробуйте снова позже.")
  
@router.message(Command('manager'))    
@router.callback_query(F.data == 'write to the manager')
async def write_to_the_manager(update: CallbackQuery | Message):
    """
    Обработчик команды /manager и кнопки 'write to the manager'.
    
    Отправляет сообщение пользователю с инструкцией по связи с менеджером.
    
    :param update: Сообщение или callback-запрос от пользователя.
    :type update: CallbackQuery | Message
    :return: None
    """
    
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=CANCEL_BUTTON_TEXT, callback_data='menu')]
        ])

        user_id = update.from_user.id
        await rq.increment_command_count(user_id)

        action_type = "write_to_manager"
        action_details = f"User with id={user_id} initiated 'write to the manager'"
        await log_user_action(user_id, action_type, action_details)

        if isinstance(update, Message):
            await update.answer(WRITE_TO_MANAGER_TEXT, reply_markup=keyboard)
        elif isinstance(update, CallbackQuery):
            await update.answer('')  # Пустой ответ на callback-запрос
            await update.message.answer(WRITE_TO_MANAGER_TEXT, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in write_to_the_manager: {str(e)}")

        await update.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")



@router.callback_query(F.data.startswith("page_"))
async def handle_pagination(callback: CallbackQuery):
    """
    Обработчик переходов по страницам пагинации.

    Логирует действия пользователя и обновляет текст и клавиатуру сообщения
    в зависимости от выбранной страницы.

    :param callback: Callback-запрос от пользователя.
    :type callback: CallbackQuery
    :return: None
    """
    
    try:
        user_id = callback.from_user.id

        action_type = "pagination"
        action_details = f"User navigated to page: {callback.data}"
        await log_user_action(user_id, action_type, action_details)

        await rq.increment_command_count(user_id)

        search_in = None
        if 'statistics' in callback.data:
            search_in = 'statistics'
        elif 'on_hand' in callback.data:
            search_in = 'on_hand'
        elif 'to_order' in callback.data:
            search_in = 'to_order'

        if not search_in:
            await callback.answer("Ошибка: неизвестный контекст для поиска!")
            return

        data_parts = callback.data.split('_')
        if len(data_parts) < 4:
            await callback.answer("Ошибка: некорректные данные для пагинации!")
            return

        page = int(data_parts[1])
        context_type = data_parts[2]
        context_value = data_parts[3]

        if context_type == "brand":
            data = await rq.get_vapes_by_brand(int(context_value), search_in)
            callback_prefix = f"brand_{context_value}"
        elif context_type == "tag":
            data = await rq.get_vapes_by_tag(int(context_value), search_in)
            callback_prefix = f"tag_{context_value}"
        elif context_type == 'flavor':
            data = await rq.get_vapes_by_flavor(context_value, search_in)
            callback_prefix = f"flavor_{context_value}"
        elif context_type == 'statistics':
            data = await rq.get_users()
            callback_prefix = 'statistics'
        else:
            await callback.answer("Ошибка: неизвестный контекст для пагинации!")
            return

        page_size = 5
        text, keyboard = await kb.generate_pagination(data, page, page_size, callback_prefix, search_in)

        await callback.message.edit_text(text=text, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in handle_pagination: {str(e)}")

        await callback.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")



@router.message(Command('vapes'))     
@router.callback_query(F.data == 'vapes')
async def all_brands(update: Message | CallbackQuery):
    """
    Обработчик команды /vapes или нажатия на кнопку "vapes". Показывает меню выбора жидкостей для вейпов.

    :param update: Сообщение или callback-запрос от пользователя.
    :type update: Message | CallbackQuery
    :return: None
    """
    
    try:
        user_id = update.from_user.id

        action_type = "view_vapes"
        action_details = "User opened the vapes menu"
        await log_user_action(user_id, action_type, action_details)

        await rq.increment_command_count(user_id)

        keyboard = kb.product_selection

        if isinstance(update, Message):
            await update.answer(VAPES_PRODUCT_SELECTION_TEXT, reply_markup=keyboard)
        elif isinstance(update, CallbackQuery):
            await update.message.answer(VAPES_PRODUCT_SELECTION_TEXT, reply_markup=keyboard)
            await update.answer()

    except Exception as e:
        logging.error(f"Error in all_brands handler: {str(e)}")

        await update.answer("Произошла ошибка при загрузке меню. Пожалуйста, попробуйте снова.")

@router.callback_query(F.data == 'vapes_on_hand')
@router.callback_query(F.data == 'vapes_to_order')
async def search_to_order(callback: CallbackQuery):
    """
    Обработчик поиска по категориям: 'vapes_on_hand' и 'vapes_to_order'. Отправляет пользователю меню поиска
    жидкостей в зависимости от выбранной категории (в наличии или под заказ).

    :param callback: Callback-запрос от пользователя.
    :type callback: CallbackQuery
    :return: None
    """
    
    try:
        user_id = callback.from_user.id

        action_type = "search_by_product_category"
        action_details = f"User searched by category: {callback.data}"
        await log_user_action(user_id, action_type, action_details)

        await rq.increment_command_count(user_id)

        product_selection = callback.data[1:]

        keyboard = await kb.get_search_menu_keyboard(product_selection)

        await callback.answer('')  # Ожидание ответа
        await callback.message.answer(SEARCH_MENU_TEXT, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in search_to_order handler: {str(e)}")

        await callback.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова.")


    
    
@router.callback_query(F.data.startswith('search_by_tag_'))
async def search(callback: CallbackQuery):
    """
    Обработчик поиска жидкостей по тегу. Когда пользователь инициирует поиск по тегу, бот отправляет 
    список всех тегов с доступными продуктами в зависимости от категории (в наличии или под заказ).
    
    :param callback: Callback-запрос от пользователя.
    :type callback: CallbackQuery
    :return: None
    """
    
    try:
        user_id = callback.from_user.id

        action_type = "search_tag"
        action_details = f"User initiated search by tag: {callback.data}"
        await log_user_action(user_id, action_type, action_details)

        await rq.increment_command_count(user_id)

        search_in = 'on_hand' if 'on_hand' in callback.data else 'to_order'

        tags = await rq.get_all_tags_with_vapes(search_in)

        keyboard = await kb.get_tags_keyboard(tags, search_in)

        await callback.answer('')
        await callback.message.answer(SEARCH_BY_TAG_TEXT, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in search handler: {str(e)}")

        await callback.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова.")

@router.callback_query(F.data.startswith('tag_'))
async def all_vapes_by_tag(callback: CallbackQuery):
    """
    Обработчик просмотра всех жидкостей по выбранному тегу. Отправляет пользователю список продуктов, 
    относящихся к выбранному тегу, с пагинацией.
    
    :param callback: Callback-запрос от пользователя.
    :type callback: CallbackQuery
    :return: None
    """
    
    try:
        user_id = callback.from_user.id

        action_type = "view_vapes_by_tag"
        action_details = f"User viewed vapes by tag: {callback.data}"
        await log_user_action(user_id, action_type, action_details)

        await rq.increment_command_count(user_id)

        search_in = 'on_hand' if 'on_hand' in callback.data else 'to_order'

        tag_id = int(callback.data.split('_')[1])

        vapes = await rq.get_vapes_by_tag(tag_id, search_in)

        page = 1
        page_size = 5
        callback_prefix = f"tag_{tag_id}"

        text, keyboard = await kb.generate_pagination(vapes, page, page_size, callback_prefix, search_in)

        await callback.answer('')
        await callback.message.answer(text=text, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in all_vapes_by_tag handler: {str(e)}")

        await callback.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова.")


@router.callback_query(F.data.startswith('search_by_brand_'))
async def search(callback: CallbackQuery):
    """
    Обработчик поиска вейпов по бренду. Когда пользователь инициирует поиск по бренду, бот отправляет 
    список всех брендов с доступными продуктами в зависимости от категории (в наличии или под заказ).
    
    :param callback: Callback-запрос от пользователя.
    :type callback: CallbackQuery
    :return: None
    """
    
    try:
        user_id = callback.from_user.id

        action_type = "search_brand"
        action_details = f"User initiated search by brand: {callback.data}"
        await log_user_action(user_id, action_type, action_details)

        await rq.increment_command_count(user_id)

        search_in = 'on_hand' if 'on_hand' in callback.data else 'to_order'

        brands = await rq.get_brands(search_in)

        keyboard = await kb.get_brands_keyboard(brands, search_in)

        await callback.answer('')
        await callback.message.answer(VAPES_CATEGORY_TEXT, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in search by brand handler: {str(e)}")

        await callback.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова.")


@router.callback_query(F.data.startswith('brand_'))
async def all_vapes_by_brand(callback: CallbackQuery):
    """
    Обработчик просмотра всех жидкостей по выбранному бренду. Отправляет пользователю список продуктов, 
    относящихся к выбранному бренду, с пагинацией.
    
    :param callback: Callback-запрос от пользователя.
    :type callback: CallbackQuery
    :return: None
    """
    
    try:
        user_id = callback.from_user.id

        action_type = "view_vapes_by_brand"
        action_details = f"User viewed vapes by brand: {callback.data}"
        await log_user_action(user_id, action_type, action_details)

        await rq.increment_command_count(user_id)

        search_in = 'on_hand' if 'on_hand' in callback.data else 'to_order'

        brand_id = int(callback.data.split('_')[1])

        vapes = await rq.get_vapes_by_brand(brand_id, search_in)

        page = 1
        page_size = 5
        callback_prefix = f"brand_{brand_id}"

        text, keyboard = await kb.generate_pagination(vapes, page, page_size, callback_prefix, search_in)

        await callback.answer('')
        await callback.message.answer(text=text, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in all_vapes_by_brand handler: {str(e)}")

        await callback.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова.")


class SearchState(StatesGroup):
    waiting_for_flavor = State()

@router.callback_query(F.data.startswith('search_by_flavor_'))
async def start_flavor_search(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик начала поиска по вкусу. Запрашивает ввод вкуса от пользователя
    и сохраняет информацию о категории поиска (в наличии или под заказ).

    :param callback: Callback-запрос от пользователя.
    :param state: Состояние машины состояний для хранения данных.
    :type callback: CallbackQuery
    :type state: FSMContext
    :return: None
    """
    
    try:
        user_id = callback.from_user.id
        action_type = "search_flavor_start"
        action_details = f"User started searching for flavor: {callback.data}"

        await log_user_action(user_id, action_type, action_details)
        await rq.increment_command_count(user_id)

        search_in = 'on_hand' if 'on_hand' in callback.data else 'to_order'

        await state.update_data(search_in=search_in)
        await state.set_state(SearchState.waiting_for_flavor)

        await callback.message.answer("Введите название вкуса для поиска:")
        await callback.answer('')

    except Exception as e:
        logging.error(f"Error in start_flavor_search handler: {str(e)}")

        await callback.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

@router.message(SearchState.waiting_for_flavor)
async def process_flavor_search(message: Message, state: FSMContext):
    """
    Обработчик, который выполняет поиск по вкусу. Показывает результаты поиска 
    и предоставляет пагинацию, если результаты есть.

    :param message: Сообщение от пользователя с названием вкуса.
    :param state: Состояние машины состояний для получения данных.
    :type message: Message
    :type state: FSMContext
    :return: None
    """
    
    try:
        user_id = message.from_user.id
        action_type = "search_flavor_result"
        action_details = f"User searched for flavor: {message.text}"

        await log_user_action(user_id, action_type, action_details)
        await rq.increment_command_count(user_id)

        flavor = message.text.strip() 
        data = await state.get_data()
        search_in = data.get("search_in", "on_hand")

        vapes = await rq.get_vapes_by_flavor(flavor, search_in)

        page = 1
        page_size = 5
        callback_prefix = f"flavor_{flavor}"

        if not vapes:
            await message.answer(NO_VAPES_FOUND_TEXT)
            return

        text, keyboard = await kb.generate_pagination(vapes, page, page_size, callback_prefix, search_in)

        await message.answer(text, reply_markup=keyboard)
        await state.clear()

    except Exception as e:
        logging.error(f"Error in process_flavor_search handler: {str(e)}")

        await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова.")



@router.message(Command('statistics'))
async def show_statistics(message: Message):
    """
    Отображает статистику пользователей с пагинацией.
    """
        
    try:
        page = 1
        page_size = 5
        search_in = "statistics"
        callback_prefix = f"statistics"
        
        users = await rq.get_users()

        text, keyboard = await kb.generate_pagination(users, page, page_size, callback_prefix, search_in)

        await message.answer(text=text, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in show_statistics handler: {str(e)}")
        
        await message.answer("Произошла ошибка при загрузке статистики.")

@router.message(Command('create_file_statistics'))
async def create_statistics_file(message: Message):
    """
    Экспортирует данные статистики в файл и отправляет его пользователю.
    """
    
    try:
        file_name = await export_users_to_excel()
        
        if file_name:
            document = FSInputFile(file_name)
            await message.answer_document(document, caption="📊 Статистика посещений пользователей за неделю")
        else:
            await message.answer("Нет данных для экспорта.")
    
    except Exception as e:
        logging.error(f"Error in create_statistics_file handler: {str(e)}")
        
        await message.answer("Произошла ошибка при экспорте данных.")
