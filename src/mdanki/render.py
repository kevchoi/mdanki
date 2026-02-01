import mistune


def render_markdown(text: str) -> str:
    return mistune.html(text)
