from mdanki.render import render_markdown


def test_render_plain_text():
    result = render_markdown("Hello world")
    assert "<p>Hello world</p>" in result


def test_render_code_block():
    result = render_markdown("""```python
print("hello")
```""")
    assert "<pre>" in result
    assert "<code" in result
    assert "print" in result


def test_render_inline_code():
    result = render_markdown("Use `print()` to output text.")
    assert "<code>" in result
    assert "print()" in result


def test_render_bold():
    result = render_markdown("This is **bold** text.")
    assert "<strong>bold</strong>" in result


def test_render_list():
    result = render_markdown("""- item 1
- item 2
- item 3""")
    assert "<ul>" in result
    assert "<li>" in result
