import logging
import sys
import time
from http import HTTPStatus

import requests
import telegram

from config import (ENDPOINT, HEADERS, HOMEWORK_STATUSES, PRACTICUM_TOKEN,
                    RETRY_TIME, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)
from exceptions import (ResponseKeyError, ResponseStatusIsNotOk,
                        TelegramUnavailable)


def send_message(bot, message):
    """Отправляем сообщение пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение успешно отправлено')
    except telegram.TelegramError as error:
        logging.error('Cбой при отправке сообщения')
        raise telegram.TelegramError(error)
    except TelegramUnavailable as error:
        logging.error('Telegram недоступен')
        raise TelegramUnavailable(error)


def get_api_answer(current_timestamp):
    """Делаем запрос к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != HTTPStatus.OK:
        logging.error('Запрос к API некорректный')
        raise ResponseStatusIsNotOk('Запрос к API некорректный')
    return homework_statuses.json()


def check_response(response):
    """Проверяем ответ API на корректность."""
    if not isinstance(response, dict):
        logging.error('Ответ не является словарем')
        raise TypeError('Ответ не в виде словаря')
    if ('homeworks' or 'current_date') not in response:
        logging.error('Ответ API некорректный')
        raise ResponseKeyError('В ответе отсутствуют домашние работы')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        logging.error('Домашние работы не в виде списка')
        raise TypeError('Домашние работы не в виде списка')
    logging.info('Ответ API корректный')
    return homeworks


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
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:
        logging.error('Недокументированный статус домашней работы')
        raise KeyError('Недокументированный статус домашней работы')
    logging.info('Статус домашней работы возвращен корректно')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        logging.critical('Отсутствует переменная окружения: {token}')
        sys.exit('Отсутсвует один из токенов')
    else:
        logging.info('Проверка переменных окружения успешно пройдена')
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
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(error)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(message)s',
    )
    main()
