import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MarkdownCard:
    front_raw: str
    back_raw: str
    source_hash: str
    source_file: str
    deck: str

    @staticmethod
    def compute_hash(front_raw: str) -> str:
        return hashlib.sha256(front_raw.encode("utf-8")).hexdigest()[:16]


def get_deck_from_path(file_path: Path, base_path: Path) -> str:
    relative = file_path.parent.relative_to(base_path)
    if not relative.parts:
        return "Default"
    return "::".join(relative.parts)


def parse_markdown_file(file_path: Path, base_path: Path) -> list[MarkdownCard]:
    content = file_path.read_text(encoding="utf-8")
    deck = get_deck_from_path(file_path, base_path)
    relative_path = file_path.relative_to(base_path.parent)
    source_file = str(relative_path)

    heading_pattern = re.compile(r"^## (.+)$", re.MULTILINE)
    matches = list(heading_pattern.finditer(content))

    cards: list[MarkdownCard] = []

    for i, match in enumerate(matches):
        front_raw = match.group(1).strip()

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        back_raw = content[start:end].strip()

        if not front_raw or not back_raw:
            continue

        source_hash = MarkdownCard.compute_hash(front_raw)

        cards.append(
            MarkdownCard(
                front_raw=front_raw,
                back_raw=back_raw,
                source_hash=source_hash,
                source_file=source_file,
                deck=deck,
            )
        )

    return cards


def parse_all(base_path: Path) -> list[MarkdownCard]:
    files = sorted(base_path.rglob("*.md"))
    if not files:
        print(f"No markdown files found in {base_path}", file=sys.stderr)
        return []

    cards: list[MarkdownCard] = []
    for file_path in files:
        cards.extend(parse_markdown_file(file_path, base_path))
    return cards
