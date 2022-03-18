class ResponseStatusIsNotOk(Exception):
    """Исключение для статуса ответа API != 200."""

    pass


class ResponseKeyError(Exception):
    """Исключение для некорректного ответа API."""

    pass


class TelegramUnavailable(Exception):
    """Исключение на случай недоступности telegram."""

    pass
