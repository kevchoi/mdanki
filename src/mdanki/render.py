import mistune
from mistune.plugins.math import math as math_plugin
from mistune.renderers.html import HTMLRenderer


class AnkiRenderer(HTMLRenderer):
    def math(self, text: str) -> str:
        return rf"\({text}\)"

    def block_math(self, text: str) -> str:
        return rf"\[{text}\]"


_markdown = mistune.Markdown(renderer=AnkiRenderer(), plugins=[math_plugin])


def render_markdown(text: str) -> str:
    return _markdown(text)
