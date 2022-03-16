import logging
import os
import time
from tkinter import W
from dotenv import load_dotenv
import telegram
from telegram import bot
import requests

logger = logging.getLogger(__name__)
load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log', 
    format='%(asctime)s, %(levelname)s, %(message)s',
    filemode=W
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

# def check_tokens():
#     """Проверка токенов"""
#     tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
#     for token in tokens:
#         if token is None:
#             logging.error('Отсутствует переменная окружения: {token}')
#             return False
#     logging.info('Проверка переменных окружения успешно пройдена')
#     return True


def get_api_answer(current_timestamp):
    """Делаем запрос к API"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code == 200:
        logging.info('Запрос к API успешный')
        return homework_statuses.json()
    else:
        logging.error('Запрос к API некорректный')


def check_response(response):
    """Проверяем ответ API на корректность"""
    if ('homeworks' and 'current_date') in response:
        logger.info('Ответ API корректный')
        return response.get('homeworks')
    else:
        logger.error('Ответ API некорректный')
        raise AssertionError('В ответе отсутствуют домашние работы')


def parse_status(homework):
    """Получаем статус домашней работы"""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error('Ошибка с homework_name')
        raise Exception('Отсутсвует название домашней работы')
    homework_status = homework.get('status')
    if homework_status is None:
        logging.debug('Ошибка с homework_status')
        raise Exception('Отсутсвуют новые статусы домашней работы')
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        logging.error('Недокументированный статус домашней работы, обнаруженный в ответе API')
        raise Exception('Недокументированный статус домашней работы, обнаруженный в ответе API')
    logging.info('Статус домашней работы возвращен корректно')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправляем сообщение пользователю"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение успешно отправлено')
    except Exception as error:
        logging.error('Cбой при отправке сообщения')
        raise Exception(error)


homeworksss = check_response(get_api_answer(1549962000))
message = parse_status(homeworksss[0])
bot = telegram.Bot(token=TELEGRAM_TOKEN)
send_message(bot, message)
