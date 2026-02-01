from dataclasses import dataclass, field
from pathlib import Path

from .anki import AnkiClient, NOTE_TYPE_NAME
from .parser import parse_all
from .render import render_markdown


@dataclass
class SyncStats:
    total: int = 0
    created: int = 0
    updated: int = 0
    moved: int = 0
    deleted: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class AnkiNote:
    note_id: int
    card_ids: list[int]
    source_hash: str
    source_file: str
    deck: str
    front: str
    back: str


def _get_field(fields: dict, name: str) -> str:
    return fields.get(name, {}).get("value", "")


def get_existing_notes(client: AnkiClient) -> dict[str, AnkiNote]:
    note_ids = client.find_notes(f"note:{NOTE_TYPE_NAME}")
    notes_info = client.get_notes_info(note_ids)

    all_card_ids = [cid for info in notes_info for cid in info.get("cards", [])]

    cards_info = client.get_cards_info(all_card_ids)
    card_to_deck = {card["cardId"]: card["deckName"] for card in cards_info}

    existing: dict[str, AnkiNote] = {}

    for info in notes_info:
        fields = info.get("fields", {})
        source_hash = _get_field(fields, "SourceHash")
        source_file = _get_field(fields, "SourceFile")
        front = _get_field(fields, "Front")
        back = _get_field(fields, "Back")

        cards = info.get("cards", [])
        deck = card_to_deck.get(cards[0], "Default") if cards else "Default"

        existing[source_hash] = AnkiNote(
            note_id=info["noteId"],
            card_ids=cards,
            source_hash=source_hash,
            source_file=source_file,
            deck=deck,
            front=front,
            back=back,
        )

    return existing


def sync(
    path: Path,
    client: AnkiClient,
    dry_run: bool = False,
    verbose: bool = False,
    delete: bool = False,
) -> SyncStats:
    stats = SyncStats()

    if not dry_run:
        client.create_note_type_if_not_exists()

    cards = parse_all(path)

    if verbose:
        print(f"Found {len(cards)} cards in {path}")

    existing = get_existing_notes(client)

    if verbose:
        print(f"Found {len(existing)} existing notes in Anki")

    if not dry_run:
        for deck in {card.deck for card in cards}:
            client.create_deck(deck)

    for card in cards:
        front_html = render_markdown(card.front_raw)
        back_html = render_markdown(card.back_raw)

        if card.source_hash in existing:
            note = existing[card.source_hash]
            content_changed = note.front != front_html or note.back != back_html
            deck_changed = note.deck != card.deck

            if content_changed:
                if verbose:
                    print(f"Updating: {card.front_raw[:50]}")
                if not dry_run:
                    client.update_note(
                        note.note_id, front_html, back_html, card.source_file
                    )
                stats.updated += 1

            if deck_changed:
                if verbose:
                    print(f"Moving to {card.deck}: {card.front_raw[:50]}")
                if not dry_run and note.card_ids:
                    client.change_deck(note.card_ids, card.deck)
                stats.moved += 1

        else:
            if verbose:
                print(f"Creating: {card.front_raw[:50]}")
            if not dry_run:
                try:
                    client.add_note(
                        deck=card.deck,
                        front=front_html,
                        back=back_html,
                        source_hash=card.source_hash,
                        source_file=card.source_file,
                    )
                    stats.created += 1
                except Exception as e:
                    stats.errors.append(
                        f"Failed to create '{card.front_raw[:50]}': {e}"
                    )
            else:
                stats.created += 1

    if delete:
        base_dir = path.name
        markdown_hashes = {card.source_hash for card in cards}
        orphaned_notes = [
            note
            for note in existing.values()
            if note.source_file.startswith(base_dir + "/")
            and note.source_hash not in markdown_hashes
        ]
        if orphaned_notes:
            for note in orphaned_notes:
                if verbose:
                    print(f"Deleting: {note.front[:50]}")
            if not dry_run:
                client.delete_notes([note.note_id for note in orphaned_notes])
            stats.deleted = len(orphaned_notes)

    if not dry_run and (stats.moved > 0 or stats.deleted > 0):
        deleted_decks = client.delete_empty_decks(path.name)
        if verbose:
            for deck in deleted_decks:
                print(f"Removed empty deck: {deck}")

    stats.total = len(existing) + stats.created - stats.deleted

    return stats
