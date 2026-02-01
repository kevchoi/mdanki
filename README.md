# md-anki

Sync Markdown flashcards to Anki via AnkiConnect.

## Installation

```bash
uv add mdanki
# or
pip install mdanki
```

Requires Anki with [AnkiConnect](https://ankiweb.net/shared/info/2055492159) addon.

## Usage

```bash
# Check connection to Anki
mdanki status

# Parse markdown files (preview cards)
mdanki parse ./notes

# Sync cards to Anki
mdanki sync ./notes

# Preview sync without making changes
mdanki sync ./notes --dry-run

# Verbose output
mdanki sync ./notes --verbose

# Delete cards from Anki that are no longer in markdown
mdanki sync ./notes --delete
```

## Card Format

Cards are defined by `##` headings. The heading becomes the front, everything until the next heading becomes the back:

```markdown
## What is the capital of France?

Paris

## How do you print in Python?

​```python
print("Hello, World!")
​```
```

Subdirectories become Anki decks:

```
notes/
  python/
    basics.md     → "notes::python" deck
  spanish.md      → "notes" deck
```

## Try it out

The `examples/` directory contains test cards:

```
examples/
  programming/
    python/
      basics.md     → "examples::programming::python" deck
  languages/
    spanish.md      → "examples::languages" deck
```

```bash
mdanki status               # check Anki connection
mdanki parse examples/      # preview cards
mdanki sync examples/ -n -v # dry run
mdanki sync examples/ -v    # sync to Anki
```