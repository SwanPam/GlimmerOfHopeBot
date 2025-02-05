# Vape Store Bot

## Описание
Этот проект представляет собой Telegram-бота для магазина вейпов, который парсит данные из Google Таблиц и отображает их пользователям. Бот позволяет просматривать товары в наличии и на заказ, связываться с менеджером и оформлять заказ.

## Установка и запуск
### 1. Клонирование репозитория
```sh
git clone git@github.com:USERNAME/REPOSITORY.git
cd REPOSITORY
```

### 2. Настройка виртуального окружения
```sh
setup_venv.bat
```
Этот скрипт создаст виртуальное окружение и установит все необходимые зависимости.

### 3. Запуск проекта
```sh
start_project.bat
```

## Конфигурация
Перед запуском убедитесь, что в корневой директории находятся два файла: `.env` и `credentials.json`.

### Файл `.env`
Создайте файл `.env` и заполните его следующими данными (убедитесь, что секретная информация удалена):
```ini
TOKEN = <TELEGRAM_BOT_TOKEN>
SQLALCHEMY_URL = 'sqlite+aiosqlite:///db.sqlite3'

CREDENTIALS_FILE = credentials.json
SPREADSHEET_ID = <ВАШ_SPREADSHEET_ID>

SHEET_NAMES = Заказы - Жидкости,Сейчас в наличии - Жидкости
DATA_RANGES = A3:D1079,A3:D100

SHEET_NAME_VAPORIZERS = Сейчас в наличии - Испарители
DATA_RANGE_VAPORIZERS = A1:B100
```

### Файл `credentials.json`
Создайте файл `credentials.json` и заполните его данными сервисного аккаунта Google (без приватного ключа):
```json
{
  "type": "service_account",
  "project_id": "parsingvape",
  "private_key_id": "<PRIVATE_KEY_ID>",
  "private_key": "<HIDDEN>",
  "client_email": "<CLIENT_EMAIL>",
  "client_id": "<CLIENT_ID>",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/<CLIENT_EMAIL>",
  "universe_domain": "googleapis.com"
}
```

## Используемые технологии
- Python
- Aiogram (для работы с Telegram API)
- Google Sheets API (для парсинга данных)
- SQLAlchemy + SQLite (для хранения данных)

## Контакты
Если у вас возникли вопросы или предложения, свяжитесь с разработчиком проекта.

