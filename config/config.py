import os

TOKEN = os.getenv("TOKEN")

DB = "postgres"
DB_USER = "postgres"
DB_HOST = "postgres1"
DB_PORT = 5432
DB_PASS = None

ADMIN_ID = 831232089
PATH = "tickets/"

TAGS = ["tag"]

HELP_MESSAGE = '''
Сообщение c числом (типа «билет 123», /123 или просто 123) — поиск по номеру билета
Текстовое сообщение — поиск по темам билетов

/[tag] — выводит все вопросы теормина; /rnd\_[tag] - рандомный

По поводу багов/неточностей/дополнений писать @MrAlex18
'''

WELCOME_MESSAGE = '''Привет! Я расскажу тебе c билетах по диффурам в красивых картинках. Спроси меня любой билет и я тебе отправлю картинку

[Бота](https://github.com/nsychev/tickets-bot) сделал @nsychev, адаптировал для у2021 @MrAlex18
''' + HELP_MESSAGE