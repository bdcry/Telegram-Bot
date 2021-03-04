import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    filemode='a',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',)


logger = logging.getLogger('homework')
handler = RotatingFileHandler('logs.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework_status == 'reviewing':
        verdict = 'Работу взяли на проверку.'
    else:
        verdict = (
            f'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
        )
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {
        'from_date': current_timestamp,
    }
    try:
        homework_statuses = requests.get(
            PRAKTIKUM_URL, params=params, headers=headers)
    except requests.HTTPError:
        logging.warning("Exception occurred")
        return 'Не удалось получить статус домашней работы.'
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    # проинициализировать бота здесь
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug(msg='Запуск Telegram-бота')
    current_timestamp = 0
    # current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            homeworks = new_homework.get('homeworks', [])
            if homeworks:
                send_message(parse_homework_status(homeworks[0]), bot_client)
            current_timestamp = new_homework.get('current_date')
            # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            logger.error(f'Бот столкнулся с ошибкой: {e}')
            send_message(e, bot_client)
            time.sleep(5)


if __name__ == '__main__':
    main()
