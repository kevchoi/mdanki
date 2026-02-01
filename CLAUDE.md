# Project: mdanki

Sync Markdown files to Anki via AnkiConnect.

## Commands

- `uv run pytest` - run tests
- `uv run pytest tests/test_sync.py -v` - run specific test file
- `uv run mdanki sync <path> -v --dry-run` - preview sync
- `uv run mdanki sync <path>` - sync to Anki

## Code Style

- Use dataclasses for data structures
- Type hints on all functions
- Keep functions focused and small
- Tests go in `tests/` mirroring `src/mdanki/` structure
- Integration tests use `pytest.skip()` when Anki isn't running

## Architecture

- `parser.py` - parse markdown into cards
- `render.py` - convert markdown to HTML
- `anki.py` - AnkiConnect client
- `sync.py` - orchestrates sync logic
- `cli.py` - command-line interface

## Testing

- Use `TEST_DECK_PREFIX = "mdanki-test"` for test decks
- Always clean up test decks in fixtures
- Test both actual operations and dry-run behavior

## Preferences

- No unnecessary inline documentation (docstrings, comments, type annotations) on code that wasn't changed
- Only add comments where logic isn't self-evident
- Keep README updated with user-facing features
