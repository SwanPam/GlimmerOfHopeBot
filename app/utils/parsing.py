import gspread
from oauth2client.service_account import ServiceAccountCredentials
import dotenv
import os
import re
from collections import defaultdict

dotenv.load_dotenv()

credentials_file = os.getenv('CREDENTIALS_FILE')
spreadsheet_id = os.getenv('SPREADSHEET_ID')

sheet_name = os.getenv('SHEET_NAMES').strip().split(',')
data_range = os.getenv('DATA_RANGES').strip().split(',')

def group_brands_and_lines(items: list[str]) -> dict[str, list[str]]:
    items = list(set(i.strip() for i in items if i.strip()))  # Убираем дубли и пробелы
    items_sorted = sorted(items, key=lambda x: -len(x))  # Длинные сначала
    result = defaultdict(list)

    for item in items_sorted:
        matched = False
        for potential_brand in items_sorted:
            if item == potential_brand:
                continue
            if item.upper().startswith(potential_brand.upper() + " "):
                line = item[len(potential_brand):].strip()
                result[potential_brand].append(line)
                matched = True
                break
        if not matched:
            result[item]  # Просто бренд без линеек

    return dict(result)

def split_brand_line(full_name: str, categories_brand: list[str]) -> tuple[str, str]:
    for brand in sorted(categories_brand, key=lambda x: -len(x)):  # Длинные сначала
        if full_name.upper().startswith(brand.upper()):
            line = full_name[len(brand):].strip()
            return brand, line
    return full_name, ''  # Если бренд не найден

# Авторизация
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(spreadsheet_id)

brands_db = {}
tags_db = {}
vapes_tags_db = []
vapes_db = []

vape_list = []
prefixs = []

place = ['НА РАБОТЕ - ПЛОЩАДЬ ЛЕНИНА', 'ДОМА - КОЛОДИЩИ']
stop_worlds = ['Испарители']
replace_text = [' NEW!', ' (Заводской никотин, БЕЗ бустера)', ]

for sh_name, dt_range in zip(sheet_name, data_range):
    sheet = spreadsheet.worksheet(sh_name)
    data = sheet.get(dt_range)
    type = 'preorder' if sh_name == 'Заказы - Жидкости' else 'resale'

    prefix = ''
    categories_brand = list(group_brands_and_lines(prefixs))
    for row in data:
        if not row or row[0] in place:
            prefix = ''
            continue

        if len(row) < 4:
            prefix = re.sub(r'\d{2,}ML\b', '',
                row[0]
                .replace(replace_text[0], '')
                .replace(replace_text[1], '')
                .replace('Rick And Morty', 'РИК И МОРТИ')
            ).strip()
            prefixs.append(prefix)

            if prefix in stop_worlds:
                continue

            brand, line = split_brand_line(prefix, categories_brand)

            if brand.upper() not in (v.upper() for v in brands_db.values()):
                brands_db[len(brands_db) + 1] = brand

        elif prefix != '':
            brand, line = split_brand_line(prefix, categories_brand)
            brand_id = next((k for k, v in brands_db.items() if v.upper() == brand.upper()), None)

            vape_list.append([
                row[0].split('—')[-1].strip(),  # вкус
                brand_id,
                brand,
                line,
                *(i.strip() if i == 'Есть' else '' for i in row[1:3]),  # наличие
                type,
                float(row[3].replace(',', '.'))  # цена
            ])
# Группировка по брендам и линейкам
vapes_db = []
  
unique_rows = set()
result = []

for item in vape_list:
    if len(item) > 0:
        key = tuple(item) 
        if key not in unique_rows:
            unique_rows.add(key)
            result.append(item)
                        
vape_list = result.copy()
name_brand_id_list = [[row[0], row[1]] for row in vape_list]
vape_list_resale = [row for row in vape_list if row[5] == 'resale']
indexes = []
for index, row in enumerate(vape_list_resale):
    if name_brand_id_list.count([row[0], row[1]]) > 1:
        indexes += [[index for index, value in enumerate(name_brand_id_list) if value == [row[0], row[1]]]][:2]
    
result = []
for idx1, idx2, *rest in indexes:
    row1 = vape_list[idx1]
    row2 = vape_list[idx2]

    if row1[5] == 'preorder' and row2[5] == 'resale':
        row_preorder, row_resale = row1, row2
    elif row1[5] == 'resale' and row2[5] == 'preorder':
        row_preorder, row_resale = row2, row1
    else:
        print('Не соответствие')
        continue
        
    availability_45_50_60 = (
        1 if row_resale[3] == 'Есть' and row_preorder[3] == 'Есть' else
        -1 if row_resale[3] == 'Есть' and row_preorder[3] == '' else
        0 if row_resale[3] == '' and row_preorder[3] == 'Есть' else
        None
    )

    availability_20 = (
        1 if row_resale[4] == 'Есть' and row_preorder[4] == 'Есть' else
        -1 if row_resale[4] == 'Есть' and row_preorder[4] == '' else
        0 if row_resale[5] == '' and row_preorder[4] == 'Есть' else
        None
    )

    merged_row = [
        row_preorder[0],  
        row_preorder[1],  
        row_preorder[2],  
        availability_45_50_60,
        availability_20,
        row_preorder[7] 
    ]

    result.append(merged_row)

indexes = [item for sublist in indexes for item in sublist]
vape_list = [row for index, row in enumerate(vape_list) if index not in indexes]

vapes_db += result

for index, row in enumerate(vape_list):
    if row[-2] == 'preorder':
        vape_list[index] = vape_list[index][0:3] + [0 if vape_list[index][3] == 'Есть' else None] + [0 if vape_list[index][4] == 'Есть' else None] + [vape_list[index][7]]
    elif row[-2] == 'resale':
        vape_list[index] = vape_list[index][0:3] + [-1 if vape_list[index][3] == 'Есть' else None] + [-1 if vape_list[index][4] == 'Есть' else None] + [vape_list[index][7]]
    else:
        print('Не соотв')
        
vapes_db += vape_list

vapes_db = [[index + 1] + row for index, row in enumerate(vapes_db)]
tags = {
    '❄️ Лёд': ['ЛЕД', 'ЛЁД', 'АЙС', 'ICE', 'ХОЛОД', 'МОРОЖ', 'ICED', 'ХОЛОДНАЯ', 'СВЕЖАЯ'],
    '🍭 Сладкий': ['СЛАДК', 'СГУЩ', 'ГЕМАТОГЕН', 'Скитлс', 'Ананас', 'Манго', 'Земляника', 
                'Арбуз', 'Дыня', 'Малин', 'Виногр', 'Клубника', 'Драгонфрут', 'Гуава', 
                'Мандарин', 'Сакур', 'Баблгам', 'Зефир', 'Личи', 'Нектарин', 'Мангостин',
                'Груша', 'Мультифрукт', 'Чупа чупс', 'Сладкая Мята', 'Сладкий Драгонфрут',
                'Сладкий Виноград', 'Сладкий Молочно-Карамельный Попкорн'],
    '🍋 Кислый': ['КИСЛ', 'Киви', 'Лимон', 'Лайм', 'Клюква', 'Бергамот', 'брусника', 'Кислая Малина'],
    '🍊🍋 Кисло-сладкий': ['Маракуйя', 'Гранат', 'Черника', 'Ежевика', 'Морошка', 'Помело',
                    'Крыжовн', 'Барбарис', 'Смородина кислинка', 'Персиковое желе с лимоном'],
    '🔄 Двойной': ['Двойн'],
    '🍯 Медовый': ['мед', 'мёд'], 
    '🍦 Мороженое': ['Мороженое', 'Банановое Мороженое'],
    '🍵 Чай': ['ЧАЙ', 'Зеленый Чай Лемонграсс', 'Молочный Чай'],
    '🥛 Йогурт': ['ЙОГУРТ', 'Йогуртовый десерт из манго', 'Вишневый йогурт', 'Сладкий малиновый йогурт',
                 'Йогурт с Ягодами', 'Йогурт из Кумквата и Маракуйи'],
    '🍹 Микс': ['МИКС', 'ISTERIKA MIX', 'Смесь африканских фруктов из холодильника',
               'Blackcurrant Raspberry Grape Candy\'s', 'Cherry Peach Lemonade'],
    '🧸 Мишки': ['Мишки', 'Gummy Bears Strawberry Kiwi'],
    '🥤 Газировка': ['ГАЗИР', 'АЙРЕН', 'ПУНШ', 'кола', 'Лимонад', 'Мохито', 'Тархун',
                'Сода', 'Швепс', 'Фанта', 'Лаймовая газировка', 'Вишневая газировка'],
    '🍬 Мармелад': ['МАРМЕЛ', 'Green Gummy'],
    '🍬 Жвачка': ['ЖВАЧКА', 'Crazy 8'],
    '🍬 Скитлс': ['Скитлс', 'Фруктовый Скитлс'],
    '🍹 Напитки': ['Компот', 'Коктейль', 'Пина Колада', 'Лимонад', 'Ред Булл', 'Фрэш',
                  'Смородиновый коктейль с клубникой'],
    '🥐 Выпечка': ['Чизкейк', 'Пиро', 'Заварной крем'],
    '⚡ Энергетик': ['Ред Булл', 'Энергет', 'адреналин раш', 'Лайм энергетик кола', 'Cranberry energy',
                    'Energy Berry', 'Виноградный адреналин раш'],
    '🍓 Фруктовый': ['Банан', 'Персик', 'Кокос', 'Яблоко', 'Киви', 'Манго', 'Апельсин', 'Грейпфрут',
                'Дыня', 'Лайм', 'Драгонфрут', 'Гуава', 'Мандарин', 'Кактус', 'Личи',
                'Нектарин', 'Мангостин', 'Груша', 'Мультифрукт', 'фрукт', 'Спелый Манго',
                'Спелая черника', 'Свежеспелый Банан', 'Персиковый Сок', 'Шелковица'],
    '🍓 Ягода': ['Смородин', 'Вишн', 'Земляни', 'Черни', 'Арбуз', 'Малин', 'Виногр', 
            'Клубни', 'Ягод', 'Гранат', 'Ежеви', 'Клюкв', 'Морошка', 'Крыжовн',
            'Барбарис', 'брусни', 'Красная вишня', 'Дикая вишня', 'Садовая малина'],
    '🍊 Цитрус': ['Апельсин', 'Грейпфрут', 'Лимон', 'Лайм', 'Мандарин', 'Лемонграсс',
            'Помело', 'Мультифрукт'],
    '🏝️ Тропический': ['Кокос', 'Ананас', 'Киви', 'Манго', 'Маракуйя', 'Драгонфрут', 'Гуава',
                    'Мангостин', 'Мультифрукт', 'Тропический Манго'],
    '🌿 Травянистый': ['Алоэ', 'Мят', 'Лемонграсс', 'Базилик', 'хво'],
    '🌱 Освежающий': ['Алоэ', 'Мята', 'Ментол', 'Кактус', 'Огурец', 'Холлс'],
    '🌴 Экзотический': ['Алоэ', 'Драгонфрут', 'Гуава', 'Сакура', 'Экзот'],
    '🌲 Лесной': ['Лесн', 'брусника', 'хво', 'Лесные Ягоды'],
    '🌸 Цветочный': ['Сакур','Бергам', 'Holy Grail'],
    '🍰 Десертный': ['Баблгам', 'Зефир','десерт', 'Клубничный Смузи', 'Черничный Пудинг'],
    '🌿 Мятный': ['Ментол', 'Мят', 'Холлс'],
    '🌶️ Пряный': ['Базилик', 'Бергамот', 'хво'],
    '🥒 Овощной': ['Огурец'],
    '🐍 Червячки': ['Черв', 'Червячки'],
    '🧩 Другое': ['джем', 'варенье', 'желе', 'Смесь', 'Самоубийца'],
}

for index, tag in enumerate(list(tags.keys())):
    tags_db[index + 1] = tag
    
for row in vapes_db:
    tags_found = []
    for index, (key, tag_list) in enumerate(tags.items()):
        for tag in tag_list:
             if re.search(f'\\b{tag.upper()}\\w*', row[1].upper()):
                tags_found.append(index)
                break
    vapes_tags_db += [[row[0]] + [index + 1] for index in tags_found]



SHEET_NAME_VAPORIZERS = 'Сейчас в наличии - Испарители'
DATA_RANGE_VAPORIZERS = 'A1:B100'

sheet = spreadsheet.worksheet(SHEET_NAME_VAPORIZERS)
data = sheet.get(DATA_RANGE_VAPORIZERS)
vaporizers = []
for row in data:
    if len(row) == 2:
        vaporizers.append([i.strip().replace(' ОМ', '') for i in row[0].split('-')] + [row[1]])

vaporizers_db = [] 
vaporizers_brand_db = []
resistances_db = []

brand_dict = {}
resistance_dict = {}
brand_id_counter = 1
resistance_id_counter = 1

for row in vaporizers:
    brand_name = row[0]  
    resistance = row[1]  
    price = row[2]       

    if brand_name not in brand_dict:
        brand_dict[brand_name] = brand_id_counter
        brand_id_counter += 1

    if resistance not in resistance_dict:
        resistance_dict[resistance] = resistance_id_counter
        resistance_id_counter += 1

    vaporizers_db.append([brand_dict[brand_name], resistance_dict[resistance], price])

vaporizers_brand_db = [[brand_id, brand_name] for brand_name, brand_id in brand_dict.items()]
resistances_db = [[resistance_id, resistance] for resistance, resistance_id in resistance_dict.items()]

