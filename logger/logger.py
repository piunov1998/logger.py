import dataclasses as dc
import enum
import io
import json
import sys
import typing as t
from abc import ABC, abstractmethod


__all__ = ["Logger", "create_logger", "LoggerConfig"]


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
        issuer: str | type,
        stream: io.TextIOWrapper = sys.stdout
    ):
        self._level = level
        self._stream = stream

        if type(issuer) != str:
            issuer = issuer.__class__.__name__
        self._issuer = issuer

    def __log(self, msg: Message):
        """Запись сообщения в поток"""

        formatted = self._format(msg)
        self._stream.write(f"{formatted}\n")
        self._stream.flush()

    def log(self, msg: Message):
        """Создание сообщения"""

        if msg.level < self._level:
            return

        self.log(msg)

    @abstractmethod
    def _format(self, msg: Message) -> str:
        """Форматирование сообщений"""

    def trace(self, msg: str, data: dict[str, t.Any]):
        """Сообщение трассировки"""

        message = Message(msg, LogLevel.TRACE, self._issuer, data)
        self.log(message)

    def debug(self, msg: str, data: dict[str, t.Any]):
        """Сообщение отладки"""

        message = Message(msg, LogLevel.DEBUG, self._issuer, data)
        self.log(message)

    def info(self, msg: str, data: dict[str, t.Any]):
        """Информационное сообщение"""

        message = Message(msg, LogLevel.INFO, self._issuer, data)
        self.log(message)

    def warning(self, msg: str, data: dict[str, t.Any]):
        """Предупреждающее сообщение"""

        message = Message(msg, LogLevel.WARN, self._issuer, data)
        self.log(message)

    def critical(self, msg: str, data: dict[str, t.Any]):
        """Критическое сообщение"""

        message = Message(msg, LogLevel.TRACE, self._issuer, data)
        self.log(message)

    fatal = critical


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
    _CLEAR = "\u001b0m"

    def _color_picker(self, level: int) -> str:
        """Выбор цвета в зависимости от уровня логов"""

        if level == LogLevel.TRACE:
            return "\u001b90m"
        elif LogLevel.TRACE < level <= LogLevel.DEBUG:
            return "\u001b37m"
        elif LogLevel.DEBUG < level <= LogLevel.INFO:
            return "\u001b34m"
        elif LogLevel.INFO < level <= LogLevel.WARN:
            return "\u001b33m"
        elif LogLevel.WARN < level <= LogLevel.ERROR:
            return "\u001b31;1m"
        elif LogLevel.ERROR < level <= LogLevel.CRITICAL:
            return "\u001b38;5;99m"
        else:
            return "\u001b38;5;51m"

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
    config: LoggerConfig = None, issuer: str | type = None
) -> Logger:
    """Создание логгера"""

    if issuer is None:
        issuer = "root"

    if config is None:
        config = LoggerConfig()

    if config.colors:
        return ColorfulLogger(config.level, issuer, config.stream)
    return TextLogger(config.level, issuer, config.stream)
