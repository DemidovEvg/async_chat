"""Утилиты управления окном сообщений чата"""
from enum import Enum, auto
from dataclasses import dataclass, field


@dataclass
class ChatLine:
    message: str
    message_id: str | None = None
    source: str | None = None
    target: str | None = None
    message_chain_id: str | None = None

    def get_row(self):
        template = '{source}->{target}: {message}'
        return template.format(
            source=self.source,
            target=self.target,
            message=self.message
        )


class OutgoingChatLine(ChatLine):
    sent: bool = True
    accepted: bool = False

    def get_row(self):
        template = '{source}->{target} {sent}{accepted}: {message}'
        return template.format(
            source=self.source,
            target=self.target,
            sent='v' if self.sent else '',
            accepted='v' if self.accepted else '',
            message=self.message
        )


class IncommintChatLine(ChatLine):
    pass


@dataclass
class ChatItem:
    lines: list[ChatLine | OutgoingChatLine | IncommintChatLine] = (
        field(default_factory=list)
    )

    class MessageDirection(str, Enum):
        incoming = auto()
        outgoing = auto()
        inner = auto()

    def get_line_by_chain_id(self, chain_id: str):
        for line in self.lines:
            if chain_id == line.message_id:
                return line

    def get_plain_text(self) -> str:
        contents = [
            line.get_row()
            for line in self.lines
        ]
        return '\n'.join(contents)

    def accepted_lines(self, message_id: str):
        for line in self.lines:
            if line.message_id == message_id:
                line.accepted = True
