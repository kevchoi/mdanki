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


def test_render_inline_math():
    result = render_markdown("Energy is $E=mc^2$ right?")
    assert r"\(E=mc^2\)" in result


def test_render_block_math():
    result = render_markdown("$$\n\\int_0^1 x\\,dx\n$$")
    assert r"\[\int_0^1 x\,dx\]" in result


def test_render_math_with_underscores():
    result = render_markdown("$a_1 + a_2$")
    assert r"\(a_1 + a_2\)" in result
    assert "<em>" not in result


def test_render_mixed_math_and_markdown():
    result = render_markdown("The formula $E=mc^2$ is **important** in `physics`.")
    assert r"\(E=mc^2\)" in result
    assert "<strong>important</strong>" in result
    assert "<code>physics</code>" in result
