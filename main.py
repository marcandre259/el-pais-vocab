#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

import db
import scraper
import llm
import audio
import export
import anki_sync


def cmd_add(args):
    """Add vocabulary from an El País article."""
    print(f"Fetching article (using {args.browser} cookies)...")

    try:
        article_text = scraper.get_article_text(args.url, browser=args.browser)
    except Exception as e:
        print(f"Error fetching article: {e}")
        sys.exit(1)

    word_count = len(article_text.split())
    print(f"Found {word_count} words in article")

    known_lemmas = db.get_known_lemmas()
    print(f"Known vocabulary: {len(known_lemmas)} lemmas")

    print(f"Asking Claude to select {args.count} new words...")
    try:
        words = llm.select_and_translate(
            article_text=article_text,
            known_words=known_lemmas,
            user_prompt=args.prompt,
            count=args.count
        )
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        sys.exit(1)

    if not words:
        print("No words returned from Claude")
        sys.exit(1)

    new_count, updated_count = db.add_words(words, source_url=args.url)
    print(f"Added {new_count} words ({updated_count} updated with examples)")

    if new_count > 0:
        print("Generating audio pronunciations...")
        new_lemmas = [w['lemma'] for w in words if w['lemma'] not in known_lemmas]
        generated, skipped = audio.generate_all_audio(new_lemmas)
        print(f"Generated {generated} new audio files")


def cmd_list(args):
    """List known vocabulary words."""
    words = db.get_all_words()

    if not words:
        print("No words in vocabulary yet")
        return

    limit = args.limit if args.limit else len(words)

    print(f"\nVocabulary ({min(limit, len(words))} of {len(words)} words):\n")

    for i, word in enumerate(words[:limit]):
        examples = word.get('examples', [])
        if isinstance(examples, str):
            import json
            examples = json.loads(examples)

        example_str = f" - {examples[0]}" if examples else ""
        print(f"{word['lemma']} ({word['pos']}): {word['french']}{example_str}")


def cmd_export(args):
    """Export vocabulary to Anki CSV."""
    export.export_csv(output_path=args.output)


def cmd_audio(args):
    """Generate audio for all vocabulary words."""
    words = db.get_all_words()

    if not words:
        print("No words in vocabulary yet")
        return

    lemmas = [w['lemma'] for w in words]
    print(f"Generating audio for {len(lemmas)} words...")

    generated, skipped = audio.generate_all_audio(lemmas)
    print(f"Generated {generated} audio files ({skipped} already existed)")


def cmd_stats(args):
    """Show vocabulary statistics."""
    stats = db.get_stats()

    print(f"\nTotal vocabulary: {stats['total_words']} words")

    if stats['by_pos']:
        print("\nBy type:")
        for pos, count in stats['by_pos'].items():
            print(f"  {pos}: {count}")

    audio_dir = Path("audio")
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.mp3"))
        print(f"\nAudio files: {len(audio_files)}")


def cmd_sync(args):
    """Sync vocabulary to Anki deck via AnkiConnect."""
    try:
        stats = anki_sync.sync_to_anki(
            db_path=args.db,
            audio_dir=args.audio_dir,
            deck_name=args.deck
        )

        print(f"\nSync complete!")
        print(f"  Added: {stats['added']}")
        print(f"  Skipped (already exist): {stats['skipped']}")
        print(f"  Failed: {stats['failed']}")

    except ConnectionError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error syncing: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="El País Vocabulary Builder - Extract Spanish vocabulary from articles",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    add_parser = subparsers.add_parser('add', help='Add vocabulary from an article')
    add_parser.add_argument('url', help='El País article URL')
    add_parser.add_argument('--prompt', default='pick useful vocabulary words',
                           help='Instructions for word selection')
    add_parser.add_argument('--count', type=int, default=30,
                           help='Number of words to extract (default: 30)')
    add_parser.add_argument('--browser', default='firefox',
                           choices=['chrome', 'firefox', 'edge', 'opera'],
                           help='Browser to extract cookies from (default: firefox)')
    add_parser.set_defaults(func=cmd_add)

    list_parser = subparsers.add_parser('list', help='List known words')
    list_parser.add_argument('--limit', type=int, default=50,
                            help='Maximum words to display (default: 50)')
    list_parser.set_defaults(func=cmd_list)

    export_parser = subparsers.add_parser('export', help='Export to Anki CSV')
    export_parser.add_argument('--output', default='vocab.csv',
                              help='Output filename (default: vocab.csv)')
    export_parser.set_defaults(func=cmd_export)

    audio_parser = subparsers.add_parser('audio', help='Generate/regenerate audio for all words')
    audio_parser.set_defaults(func=cmd_audio)

    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.set_defaults(func=cmd_stats)

    sync_parser = subparsers.add_parser('sync', help='Sync vocabulary to Anki deck')
    sync_parser.add_argument('--deck', default='el-pais',
                            help='Anki deck name (default: el-pais)')
    sync_parser.add_argument('--db', default='vocab.db',
                            help='Database path (default: vocab.db)')
    sync_parser.add_argument('--audio-dir', default='audio',
                            help='Audio directory (default: audio)')
    sync_parser.set_defaults(func=cmd_sync)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
