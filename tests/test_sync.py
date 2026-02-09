import tempfile
from pathlib import Path

import pytest

from mdanki.anki import AnkiClient
from mdanki.parser import format_deck_part
from mdanki.sync import sync

TEST_DECK_PREFIX = "mdanki-test"
TEST_DECK = format_deck_part(TEST_DECK_PREFIX)


@pytest.fixture
def client():
    try:
        client = AnkiClient()
        client.get_version()
        return client
    except Exception:
        pytest.skip("Anki is not running or AnkiConnect is not available")


@pytest.fixture
def cleanup_test_deck(client):
    # Clean up before test to ensure a clean state
    deck_names = client.get_deck_names()
    for deck in deck_names:
        if deck.startswith(TEST_DECK):
            client._request("deleteDecks", decks=[deck], cardsToo=True)

    yield

    note_ids = client.find_notes(f'"deck:{TEST_DECK}*"')
    if note_ids:
        client.delete_notes(note_ids)

    deck_names = client.get_deck_names()
    for deck in deck_names:
        if deck.startswith(TEST_DECK):
            client._request("deleteDecks", decks=[deck], cardsToo=True)


def test_sync_creates_new_cards(client, cleanup_test_deck):
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / TEST_DECK_PREFIX).mkdir()

        (base / TEST_DECK_PREFIX / "test.md").write_text("""## Test Question 1

Test answer 1.

## Test Question 2

Test answer 2.
""")

        stats = sync(base, client, dry_run=False, verbose=False)

        assert stats.created == 2
        assert stats.updated == 0
        assert stats.moved == 0
        assert len(stats.errors) == 0

        note_ids = client.find_notes(f'"deck:{TEST_DECK}"')
        assert len(note_ids) == 2


def test_sync_dry_run(client, cleanup_test_deck):
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / TEST_DECK_PREFIX).mkdir()

        (base / TEST_DECK_PREFIX / "test.md").write_text("""## Dry Run Question

Dry run answer.
""")

        stats = sync(base, client, dry_run=True, verbose=False)

        assert stats.created == 1

        note_ids = client.find_notes(f'"deck:{TEST_DECK}"')
        assert len(note_ids) == 0


def test_sync_updates_changed_cards(client, cleanup_test_deck):
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / TEST_DECK_PREFIX).mkdir()

        test_file = base / TEST_DECK_PREFIX / "test.md"
        test_file.write_text("""## Update Test Question

Original answer.
""")
        sync(base, client, dry_run=False, verbose=False)

        test_file.write_text("""## Update Test Question

Updated answer with new content.
""")
        stats = sync(base, client, dry_run=False, verbose=False)

        assert stats.created == 0
        assert stats.updated == 1
        assert stats.moved == 0


def test_sync_moves_cards_between_decks(client, cleanup_test_deck):
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / TEST_DECK_PREFIX).mkdir()
        (base / TEST_DECK_PREFIX / "subdir").mkdir()

        test_file = base / TEST_DECK_PREFIX / "test.md"
        test_file.write_text("""## Move Test Question

Answer.
""")
        sync(base, client, dry_run=False, verbose=False)

        new_file = base / TEST_DECK_PREFIX / "subdir" / "test.md"
        test_file.rename(new_file)

        stats = sync(base, client, dry_run=False, verbose=False)

        assert stats.moved == 1


def test_sync_deletes_orphaned_notes(client, cleanup_test_deck):
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / TEST_DECK_PREFIX).mkdir()

        test_file = base / TEST_DECK_PREFIX / "test.md"
        test_file.write_text("""## Question to Delete

Answer.

## Question to Keep

Answer.
""")
        sync(base, client, dry_run=False, verbose=False)

        note_ids = client.find_notes(f'"deck:{TEST_DECK}"')
        assert len(note_ids) == 2

        test_file.write_text("""## Question to Keep

Answer.
""")
        stats = sync(base, client, dry_run=False, verbose=False, delete=True)

        assert stats.deleted == 1
        note_ids = client.find_notes(f'"deck:{TEST_DECK}"')
        assert len(note_ids) == 1


def test_sync_delete_dry_run(client, cleanup_test_deck):
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / TEST_DECK_PREFIX).mkdir()

        test_file = base / TEST_DECK_PREFIX / "test.md"
        test_file.write_text("""## Question to Delete

Answer.
""")
        sync(base, client, dry_run=False, verbose=False)

        note_ids = client.find_notes(f'"deck:{TEST_DECK}"')
        assert len(note_ids) == 1

        test_file.write_text("")
        stats = sync(base, client, dry_run=True, verbose=False, delete=True)

        assert stats.deleted == 1
        note_ids = client.find_notes(f'"deck:{TEST_DECK}"')
        assert len(note_ids) == 1


def test_sync_removes_empty_deck_after_move(client, cleanup_test_deck):
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / TEST_DECK_PREFIX).mkdir()
        (base / TEST_DECK_PREFIX / "subdir").mkdir()

        test_file = base / TEST_DECK_PREFIX / "subdir" / "test.md"
        test_file.write_text("""## Question

Answer.
""")
        sync(base, client, dry_run=False, verbose=False)

        subdir_deck = f"{TEST_DECK}::{format_deck_part('subdir')}"
        deck_names = client.get_deck_names()
        assert subdir_deck in deck_names

        new_file = base / TEST_DECK_PREFIX / "test.md"
        test_file.rename(new_file)
        (base / TEST_DECK_PREFIX / "subdir").rmdir()

        sync(base, client, dry_run=False, verbose=False)

        deck_names = client.get_deck_names()
        assert subdir_deck not in deck_names


def test_sync_keeps_non_empty_deck_after_move(client, cleanup_test_deck):
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / TEST_DECK_PREFIX).mkdir()
        (base / TEST_DECK_PREFIX / "subdir").mkdir()

        (base / TEST_DECK_PREFIX / "subdir" / "test1.md").write_text("""## Question 1

Answer 1.
""")
        (base / TEST_DECK_PREFIX / "subdir" / "test2.md").write_text("""## Question 2

Answer 2.
""")
        sync(base, client, dry_run=False, verbose=False)

        (base / TEST_DECK_PREFIX / "subdir" / "test1.md").rename(
            base / TEST_DECK_PREFIX / "test1.md"
        )

        sync(base, client, dry_run=False, verbose=False)

        subdir_deck = f"{TEST_DECK}::{format_deck_part('subdir')}"
        deck_names = client.get_deck_names()
        assert subdir_deck in deck_names


def test_sync_removes_empty_deck_after_delete(client, cleanup_test_deck):
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / TEST_DECK_PREFIX).mkdir()
        (base / TEST_DECK_PREFIX / "subdir").mkdir()

        test_file = base / TEST_DECK_PREFIX / "subdir" / "test.md"
        test_file.write_text("""## Question

Answer.
""")
        sync(base, client, dry_run=False, verbose=False)

        subdir_deck = f"{TEST_DECK}::{format_deck_part('subdir')}"
        deck_names = client.get_deck_names()
        assert subdir_deck in deck_names

        test_file.unlink()
        (base / TEST_DECK_PREFIX / "subdir").rmdir()

        sync(base, client, dry_run=False, verbose=False, delete=True)

        deck_names = client.get_deck_names()
        assert subdir_deck not in deck_names
