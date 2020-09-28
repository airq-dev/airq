import typing

from flask_babel import gettext

from airq.commands.base import RegexCommand
from airq.models.events import EventType


class ShowMenu(RegexCommand):
    pattern = r"^m$"

    def handle(self) -> typing.List[str]:
        self.client.log_event(EventType.MENU)
        return [
            gettext("Reply"),
            gettext("1. Details and recommendations"),
            gettext("2. Current AQI"),
            gettext("3. Hazebot info"),
            gettext("4. Give feedback"),
            "",
            gettext("Or, enter a new zipcode."),
        ]
