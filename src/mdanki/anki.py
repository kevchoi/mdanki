from typing import Any

import httpx

ANKI_CONNECT_URL = "http://localhost:8765"
ANKI_CONNECT_VERSION = 6
NOTE_TYPE_NAME = "mdanki"


class AnkiConnectError(Exception):
    pass


class AnkiClient:
    def __init__(self, url: str = ANKI_CONNECT_URL) -> None:
        self.url = url
        self._client = httpx.Client(timeout=30.0)

    def get_version(self) -> str:
        return str(self._request("version"))

    def _request(self, action: str, **params: Any) -> Any:
        payload = {"action": action, "version": ANKI_CONNECT_VERSION}
        if params:
            payload["params"] = params
        response = self._client.post(self.url, json=payload)
        response.raise_for_status()
        result = response.json()
        if error := result.get("error"):
            raise AnkiConnectError(error)
        return result.get("result")

    def create_note_type_if_not_exists(self) -> None:
        if NOTE_TYPE_NAME in self._request("modelNames"):
            return
        self._request(
            "createModel",
            modelName=NOTE_TYPE_NAME,
            inOrderFields=["Front", "Back", "SourceHash", "SourceFile"],
            cardTemplates=[
                {
                    "Name": "Card",
                    "Front": "{{Front}}",
                    "Back": "{{FrontSide}}\n<hr id=answer>\n{{Back}}",
                }
            ],
        )

    def get_deck_names(self) -> list[str]:
        return self._request("deckNames")

    def create_deck(self, name: str) -> int:
        return self._request("createDeck", deck=name)

    def find_notes(self, query: str) -> list[int]:
        return self._request("findNotes", query=query)

    def get_notes_info(self, note_ids: list[int]) -> list[dict[str, Any]]:
        return self._request("notesInfo", notes=note_ids) if note_ids else []

    def get_cards_info(self, card_ids: list[int]) -> list[dict[str, Any]]:
        return self._request("cardsInfo", cards=card_ids) if card_ids else []

    def add_note(
        self, deck: str, front: str, back: str, source_hash: str, source_file: str
    ) -> int:
        return self._request(
            "addNote",
            note={
                "deckName": deck,
                "modelName": NOTE_TYPE_NAME,
                "fields": {
                    "Front": front,
                    "Back": back,
                    "SourceHash": source_hash,
                    "SourceFile": source_file,
                },
            },
        )

    def update_note(
        self, note_id: int, front: str, back: str, source_file: str
    ) -> None:
        self._request(
            "updateNoteFields",
            note={
                "id": note_id,
                "fields": {"Front": front, "Back": back, "SourceFile": source_file},
            },
        )

    def change_deck(self, card_ids: list[int], deck: str) -> None:
        if card_ids:
            self._request("changeDeck", cards=card_ids, deck=deck)

    def delete_notes(self, note_ids: list[int]) -> None:
        if note_ids:
            self._request("deleteNotes", notes=note_ids)

    def delete_empty_decks(self, prefix: str) -> list[str]:
        deck_names = self.get_deck_names()
        deleted = []
        # Delete sub-decks deepest-first so parents cascade to empty
        matching = sorted(
            [d for d in deck_names if d.startswith(prefix + "::")],
            key=lambda d: d.count("::"),
            reverse=True,
        )
        for deck in matching:
            note_ids = self.find_notes(f'deck:"{deck}"')
            if not note_ids:
                self._request("deleteDecks", decks=[deck], cardsToo=True)
                deleted.append(deck)
        # Also check the root deck itself
        deck_names = self.get_deck_names()
        if prefix in deck_names:
            note_ids = self.find_notes(f'deck:"{prefix}"')
            if not note_ids:
                self._request("deleteDecks", decks=[prefix], cardsToo=True)
                deleted.append(prefix)
        return deleted
