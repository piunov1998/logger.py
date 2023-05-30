import dataclasses as dc
import enum
import io
import json
import sys
import typing as t
from abc import ABC, abstractmethod


__all__ = [
    "Logger", "create_logger", "LoggerConfig", "LogLevel",
    "TRACE", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"
]


TRACE = 0
DEBUG = 10
INFO = 20
WARN = 30
ERROR = 40
CRITICAL = 50


class LogLevel(enum.IntEnum):
    """Уровни логирования"""

    TRACE = 0
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    CRITICAL = 50


@dc.dataclass
class Message:
    """Модель сообщения"""

    msg: str = dc.field()
    level: LogLevel = dc.field()
    issuer: str = dc.field(default="root")
    data: dict[str, t.Any] = dc.field(default_factory=dict)


class Logger(ABC):
    """Логгер"""

    def __init__(
        self,
        level: LogLevel,
        issuer: t.Any,
        stream: io.TextIOWrapper = sys.stdout
    ):
        self._level = level
        self._stream = stream

        if type(issuer) != str:
            issuer = issuer.__class__.__name__
        self._issuer = issuer

    @property
    def log_level(self) -> LogLevel:
        return self._level

    @log_level.setter
    def log_level(self, level: int):
        if not isinstance(level, int) or level < 0:
            raise ValueError
        self._level = level

    def __log(self, msg: Message):
        """Запись сообщения в поток"""

        formatted = self._format(msg)
        self._stream.write(f"{formatted}\n")
        self._stream.flush()

    def log(self, msg: Message):
        """Создание сообщения"""

        if msg.level < self._level:
            return

        self.__log(msg)

    @abstractmethod
    def _format(self, msg: Message) -> str:
        """Форматирование сообщений"""

    def trace(self, msg: str, data: dict[str, t.Any] = None):
        """Сообщение трассировки"""

        message = Message(msg, LogLevel.TRACE, self._issuer, data)
        self.log(message)

    def debug(self, msg: str, data: dict[str, t.Any] = None):
        """Сообщение отладки"""

        message = Message(msg, LogLevel.DEBUG, self._issuer, data)
        self.log(message)

    def info(self, msg: str, data: dict[str, t.Any] = None):
        """Информационное сообщение"""

        message = Message(msg, LogLevel.INFO, self._issuer, data)
        self.log(message)

    def warning(self, msg: str, data: dict[str, t.Any] = None):
        """Предупреждающее сообщение"""

        message = Message(msg, LogLevel.WARN, self._issuer, data)
        self.log(message)

    def error(self, msg: str, data: dict[str, t.Any] = None):
        """Сообщение об ошибке"""

        message = Message(msg, LogLevel.ERROR, self._issuer, data)
        self.log(message)

    def critical(self, msg: str, data: dict[str, t.Any] = None):
        """Критическое сообщение"""

        message = Message(msg, LogLevel.CRITICAL, self._issuer, data)
        self.log(message)


class TextLogger(Logger):
    """Текстовый логгер"""

    def _format(self, msg: Message) -> str:
        """Форматирование сообщений"""

        issuer = msg.issuer
        text = msg.msg
        data = ""
        if msg.data:
            data = json.dumps(msg.data)

        result = f"({msg.level.name})[{issuer}] {text}"
        if data:
            result += f" -> {data}"

        return result


class ColorfulLogger(Logger):
    _CLEAR = "\u001b[0m"

    def _color_picker(self, level: int) -> str:
        """Выбор цвета в зависимости от уровня логов"""

        if level == LogLevel.TRACE:
            return "\u001b[90m"
        elif LogLevel.TRACE < level <= LogLevel.DEBUG:
            return "\u001b[37m"
        elif LogLevel.DEBUG < level <= LogLevel.INFO:
            return "\u001b[34m"
        elif LogLevel.INFO < level <= LogLevel.WARN:
            return "\u001b[33m"
        elif LogLevel.WARN < level <= LogLevel.ERROR:
            return "\u001b[31;1m"
        elif LogLevel.ERROR < level <= LogLevel.CRITICAL:
            return "\u001b[1;38;5;99m"
        else:
            return "\u001b[1;38;5;51m"

    def _format(self, msg: Message) -> str:
        """Форматирование сообщений"""

        issuer = msg.issuer
        text = msg.msg
        data = ""
        if msg.data:
            data = json.dumps(msg.data)

        result = f"{self._color_picker(msg.level)}[{issuer}] {text}"
        if data:
            result += f" -> {data}"
        result += self._CLEAR

        return result


@dc.dataclass
class LoggerConfig:
    """Конфигурация логгера"""

    level: LogLevel = dc.field(default=LogLevel.INFO)
    colors: bool = dc.field(default=False)
    stream: io.TextIOWrapper = dc.field(default=sys.stdout)


def create_logger(
    config: LoggerConfig = None, issuer: t.Any = None
) -> Logger:
    """Создание логгера"""

    if issuer is None:
        issuer = "root"

    if config is None:
        config = LoggerConfig()

    if config.colors:
        return ColorfulLogger(config.level, issuer, config.stream)
    return TextLogger(config.level, issuer, config.stream)
