import tempfile
from pathlib import Path

from mdanki.parser import (
    MarkdownCard,
    get_deck_from_path,
    parse_markdown_file,
    parse_all,
)


def test_compute_hash():
    hash1 = MarkdownCard.compute_hash("What is Python?")
    hash2 = MarkdownCard.compute_hash("What is Python?")
    hash3 = MarkdownCard.compute_hash("What is Java?")

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 16


def test_get_deck_from_path_root():
    base = Path("/notes")
    file = Path("/notes/test.md")
    assert get_deck_from_path(file, base) == "Default"


def test_get_deck_from_path_nested():
    base = Path("/notes")
    file = Path("/notes/python/basics/test.md")
    assert get_deck_from_path(file, base) == "python::basics"


def test_parse_markdown_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        file = base / "test.md"
        file.write_text("""# Title

## What is Python?

A programming language.

## How do you print?

```python
print("hello")
```
""")
        cards = parse_markdown_file(file, base)

        assert len(cards) == 2

        assert cards[0].front_raw == "What is Python?"
        assert cards[0].back_raw == "A programming language."
        assert cards[0].deck == "Default"

        assert cards[1].front_raw == "How do you print?"
        assert "print" in cards[1].back_raw


def test_parse_markdown_file_empty_back():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        file = base / "test.md"
        file.write_text("""## Question with no answer

## Another question

Has an answer.
""")
        cards = parse_markdown_file(file, base)

        assert len(cards) == 1
        assert cards[0].front_raw == "Another question"


def test_parse_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        (base / "topic1").mkdir()
        (base / "topic1" / "file.md").write_text("## Q1\n\nA1")

        (base / "topic2").mkdir()
        (base / "topic2" / "file.md").write_text("## Q2\n\nA2")

        cards = parse_all(base)

        assert len(cards) == 2
        decks = {c.deck for c in cards}
        assert "topic1" in decks
        assert "topic2" in decks
