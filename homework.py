import os
import time
from dotenv import load_dotenv
import telegram
import requests
import logging

logger = logging.getLogger(__name__)
load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
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


def send_message(bot, message):
    """Отправляем сообщение пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение успешно отправлено')
    except Exception as error:
        logging.error('Cбой при отправке сообщения')
        raise Exception(error)


def get_api_answer(current_timestamp):
    """Делаем запрос к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != 200:
        logging.error('Запрос к API некорректный')
        raise Exception('Запрос к API некорректный')
    else:
        return homework_statuses.json()


def check_response(response):
    """Проверяем ответ API на корректность."""
    if ('homeworks' or 'current_date') not in response:
        logger.error('Ответ API некорректный')
        raise TypeError('В ответе отсутствуют домашние работы')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        logger.error('Домашние работы не в виде списка')
        raise TypeError('Домашние работы не в виде списка')
    else:
        logger.info('Ответ API корректный')
        return response.get('homeworks')


def parse_status(homework):
    """Получаем статус домашней работы."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error('Ошибка с homework_name')
        raise KeyError('Отсутсвует название домашней работы')
    homework_status = homework.get('status')
    if homework_status is None:
        logging.debug('Ошибка с homework_status')
        raise KeyError('Отсутсвуют новые статусы домашней работы')
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        logging.error('Недокументированный статус домашней работы')
        raise KeyError('Недокументированный статус домашней работы')
    logging.info('Статус домашней работы возвращен корректно')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in tokens:
        if token is None:
            logging.error('Отсутствует переменная окружения: {token}')
            return False
    logging.info('Проверка переменных окружения успешно пройдена')
    return True


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(error)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
