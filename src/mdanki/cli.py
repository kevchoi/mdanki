import argparse
import sys
from pathlib import Path

from .parser import parse_all
from .anki import AnkiClient
from .sync import sync


def cmd_status(_args: argparse.Namespace) -> int:
    try:
        client = AnkiClient()
        print(f"Connected to Anki (version {client.get_version()})")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(
            "Cannot connect to Anki. Is it running with AnkiConnect?", file=sys.stderr
        )
        return 1


def cmd_parse(args: argparse.Namespace) -> int:
    path = args.path.resolve()
    if not path.is_dir():
        print(f"Path is not a directory: {path}", file=sys.stderr)
        return 1
    cards = parse_all(path)
    print(f"Parsed {len(cards)} cards from {path}")
    for card in cards:
        print(
            f"{card.front_raw},{card.back_raw},{card.source_hash},{card.source_file},{card.deck}"
        )
        print("-" * 80)
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    path = args.path.resolve()
    if not path.is_dir():
        print(f"Path is not a directory: {path}", file=sys.stderr)
        return 1

    client = AnkiClient()

    if args.dry_run:
        print("Dry run - no changes will be made\n")

    try:
        stats = sync(
            path=path,
            client=client,
            dry_run=args.dry_run,
            verbose=args.verbose,
            delete=args.delete,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"\nTotal: {stats.total}")
    print(f"Created: {stats.created}")
    print(f"Updated: {stats.updated}")
    print(f"Moved: {stats.moved}")
    print(f"Deleted: {stats.deleted}")
    if stats.errors:
        print(f"Errors: {len(stats.errors)}")
        for err in stats.errors:
            print(f"  - {err}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mdanki",
        description="Sync Markdown files to Anki via AnkiConnect.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser(
        "status", help="Check connection to Anki via AnkiConnect"
    )
    status_parser.set_defaults(func=cmd_status)

    parse_parser = subparsers.add_parser(
        "parse", help="Parse markdown files into cards"
    )
    parse_parser.add_argument(
        "path",
        type=Path,
        help="Path to directory with markdown files",
    )
    parse_parser.set_defaults(func=cmd_parse)

    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync markdown files to Anki",
    )
    sync_parser.add_argument(
        "path",
        type=Path,
        help="Path to directory with markdown files",
    )
    sync_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Preview changes without making them",
    )
    sync_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    sync_parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete notes in Anki that are no longer in markdown",
    )
    sync_parser.set_defaults(func=cmd_sync)

    args = parser.parse_args()
    return args.func(args)
