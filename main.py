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

    source_lang = args.source_lang
    target_lang = args.target_lang

    try:
        article_text = scraper.get_article_text(args.url, browser=args.browser)
    except Exception as e:
        print(f"Error fetching article: {e}")
        sys.exit(1)

    word_count = len(article_text.split())
    print(f"Found {word_count} words in article")

    known_lemmas = db.get_known_lemmas(theme="el_pais")
    print(f"Known vocabulary: {len(known_lemmas)} lemmas")

    print(f"Asking Claude to select {args.count} new words...")
    try:
        words = llm.select_and_translate(
            article_text=article_text,
            known_words=known_lemmas,
            target_lang=target_lang,
            source_lang=source_lang,
            user_prompt=args.prompt,
            count=args.count,
        )
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        sys.exit(1)

    if not words:
        print("No words returned from Claude")
        sys.exit(1)

    new_count, updated_count = db.add_words(
        words,
        source=args.url,
        source_lang=source_lang,
        target_lang=target_lang,
        theme="el_pais",
    )
    print(f"Added {new_count} words ({updated_count} updated with examples)")

    if new_count > 0:
        print("Generating audio pronunciations...")
        new_lemmas = [w["lemma"] for w in words if w["lemma"] not in known_lemmas]
        generated, skipped = audio.generate_all_audio(new_lemmas, lang=source_lang)
        print(f"Generated {generated} new audio files")


def cmd_list(args):
    """List known vocabulary words."""
    words = db.get_all_words(theme=args.theme if hasattr(args, "theme") else None)

    if not words:
        print("No words in vocabulary yet")
        return

    limit = args.limit if args.limit else len(words)

    print(f"\nVocabulary ({min(limit, len(words))} of {len(words)} words):\n")

    for i, word in enumerate(words[:limit]):
        examples = word.get("examples", [])
        if isinstance(examples, str):
            import json

            examples = json.loads(examples)

        example_str = f" - {examples[0]}" if examples else ""
        print(f"{word['lemma']} ({word['pos']}): {word['translation']}{example_str}")


def cmd_export(args):
    """Export vocabulary to Anki CSV."""
    export.export_csv(output_path=args.output)


def cmd_audio(args):
    """Generate audio for all vocabulary words."""
    words = db.get_all_words()

    if not words:
        print("No words in vocabulary yet")
        return

    lemmas = [w["lemma"] for w in words]
    print(f"Generating audio for {len(lemmas)} words...")

    generated, skipped = audio.generate_all_audio(lemmas)
    print(f"Generated {generated} audio files ({skipped} already existed)")


def cmd_stats(args):
    """Show vocabulary statistics."""
    stats = db.get_stats()

    print(f"\nTotal vocabulary: {stats['total_words']} words")

    if stats.get("by_theme"):
        print("\nBy theme:")
        for theme, count in stats["by_theme"].items():
            print(f"  {theme}: {count}")

    if stats["by_pos"]:
        print("\nBy type:")
        for pos, count in stats["by_pos"].items():
            print(f"  {pos}: {count}")

    audio_dir = Path("audio")
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.mp3"))
        print(f"\nAudio files: {len(audio_files)}")


def cmd_sync(args):
    """Sync vocabulary to Anki deck via AnkiConnect."""
    try:
        # Sync all themes
        if args.all:
            results = anki_sync.sync_all_themes(
                db_path=args.db, audio_dir=args.audio_dir, include_main=True
            )

            print("\n" + "=" * 50)
            print("Sync complete!")
            print("=" * 50)

            total_added = 0
            total_skipped = 0
            total_failed = 0

            for deck_name, stats in results.items():
                print(f"\n{deck_name}:")
                print(f"  Added: {stats['added']}")
                print(f"  Skipped: {stats['skipped']}")
                print(f"  Failed: {stats['failed']}")
                total_added += stats["added"]
                total_skipped += stats["skipped"]
                total_failed += stats["failed"]

            print(
                f"\nTotal: {total_added} added, {total_skipped} skipped, {total_failed} failed"
            )
            return

        # Sync specific theme
        if args.theme:
            theme_info = db.get_theme_by_table_name(args.theme)
            if not theme_info:
                print(f"Error: Theme '{args.theme}' not found")
                print("\nAvailable themes:")
                for t in db.get_all_themes():
                    print(f"  {t['table_name']}: {t['theme_description']}")
                sys.exit(1)

            stats = anki_sync.sync_theme_to_anki(
                table_name=args.theme,
                deck_name=theme_info["deck_name"],
                db_path=args.db,
                audio_dir=args.audio_dir,
            )

            print(f"\nSync complete for {theme_info['deck_name']}!")
            print(f"  Added: {stats['added']}")
            print(f"  Skipped (already exist): {stats['skipped']}")
            print(f"  Failed: {stats['failed']}")
            return

        # Default: sync main vocabulary table only
        stats = anki_sync.sync_to_anki(
            db_path=args.db, audio_dir=args.audio_dir, deck_name=args.deck
        )

        print("\nSync complete!")
        print(f"  Added: {stats['added']}")
        print(f"  Skipped (already exist): {stats['skipped']}")
        print(f"  Failed: {stats['failed']}")

    except ConnectionError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error syncing: {e}")
        sys.exit(1)


def cmd_pick(args):
    """Pick a word from vocabulary based on a semantic prompt."""
    words = db.get_all_words()

    if not words:
        print("No words in vocabulary yet")
        sys.exit(1)

    print(f"Searching through {len(words)} words...")
    print(f"Query: {args.prompt}")

    try:
        selected_word = llm.pick_word_by_prompt(words, args.prompt)
    except Exception as e:
        print(f"Error selecting word: {e}")
        sys.exit(1)

    # Display the selected word
    print("\n" + "=" * 60)
    print(f"Word: {selected_word['word']}")
    print(f"Lemma: {selected_word['lemma']}")
    if selected_word.get("pos"):
        print(f"POS: {selected_word['pos']}")
    print(f"Translation: {selected_word['translation']}")

    examples = selected_word.get("examples", [])
    if isinstance(examples, str):
        import json

        examples = json.loads(examples)

    if examples:
        print("Examples:")
        for example in examples:
            print(f"   - {example}")

    if selected_word.get("source"):
        print(f"Source: {selected_word['source']}")

    if selected_word.get("added_at"):
        print(f"Added: {selected_word['added_at']}")

    print("=" * 60)

    # Check if audio exists and optionally play it
    audio_path = Path("audio") / f"{selected_word['lemma']}.mp3"
    if audio_path.exists():
        print(f"\nAudio available: {audio_path}")
        if args.play:
            print("Playing audio...")
            import subprocess

            try:
                subprocess.run(["afplay", str(audio_path)], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Could not play audio (afplay not available)")


def cmd_theme(args):
    """Create or list themed vocabulary lists."""
    # List themes mode
    if args.list:
        themes = db.get_all_themes()
        if not themes:
            print("No themes created yet.")
            print("\nCreate one with:")
            print(
                '  python main.py theme "cooking vocabulary" --source Spanish --target French'
            )
            return

        print(f"\nThemed vocabularies ({len(themes)} themes):\n")
        for theme in themes:
            print(f"  {theme['theme_description']}")
            print(f"    Table: {theme['table_name']}")
            print(f"    Languages: {theme['source_lang']} -> {theme['target_lang']}")
            print(f"    Words: {theme['word_count']}")
            print(f"    Deck: {theme['deck_name']}")
            print()
        return

    # Create/update theme mode
    if not args.theme:
        print(
            "Error: Theme description required (or use --list to see existing themes)"
        )
        sys.exit(1)

    if not args.source or not args.target:
        print("Error: --source and --target languages are required")
        print('Example: python main.py theme "cooking" --source Dutch --target English')
        sys.exit(1)

    theme_prompt = args.theme
    source_lang = args.source
    target_lang = args.target
    count = args.count

    # Check for related themes (unless --force-new)
    existing_themes = db.get_all_themes()
    target_table = None

    if not args.force_new and existing_themes:
        print(f"Checking for related themes ({source_lang} -> {target_lang})...")
        related = llm.detect_related_theme(
            theme_prompt, source_lang, target_lang, existing_themes
        )

        if related:
            print(f"\nFound related theme: \"{related['theme_description']}\"")
            print(f"  Table: {related['table_name']}")
            print(f"  Current words: {related['word_count']}")
            print()

            choice = input("Add to existing theme? [Y/n/cancel]: ").strip().lower()
            if choice == "cancel" or choice == "c":
                print("Cancelled.")
                return
            elif choice == "" or choice == "y" or choice == "yes":
                target_table = related["table_name"]
                print(f"\nAdding to existing theme: {related['theme_description']}")
            else:
                print("\nCreating new theme...")

    # Create new theme table if needed
    if target_table is None:
        table_name = db.sanitize_table_name(theme_prompt)

        # Check if table name already exists
        existing = db.get_theme_by_table_name(table_name)
        if existing:
            # Add suffix to make unique
            i = 2
            while db.get_theme_by_table_name(f"{table_name}_{i}"):
                i += 1
            table_name = f"{table_name}_{i}"

        # Generate deck name from theme
        words_in_theme = theme_prompt.split()
        significant = [w for w in words_in_theme if len(w) > 3][:3]
        deck_name = (
            "-".join(w.capitalize() for w in significant) if significant else table_name
        )

        print(f"\nCreating new theme: {table_name}")
        db.create_theme_table(
            table_name, theme_prompt, source_lang, target_lang, deck_name
        )
        target_table = table_name

    # Get known words in the theme
    known_lemmas = db.get_known_lemmas_from_theme(target_table)
    print(f"Existing words in theme: {len(known_lemmas)}")

    # Generate vocabulary
    print(f"\nGenerating {count} {source_lang} vocabulary words...")
    print(f"Theme: {theme_prompt}")

    try:
        words = llm.generate_themed_vocabulary(
            theme_prompt=theme_prompt,
            source_lang=source_lang,
            target_lang=target_lang,
            known_words=known_lemmas,
            count=count,
            get_all_themes_func=db.get_all_themes,
            search_theme_words_func=db.search_theme_words,
        )
    except Exception as e:
        print(f"Error generating vocabulary: {e}")
        sys.exit(1)

    if not words:
        print("No words generated.")
        return

    # Add words to theme table
    new_count, updated_count = db.add_words_to_theme(words, target_table)
    print(f"\nAdded {new_count} words ({updated_count} updated with examples)")

    # Show generated words
    print(f"\nGenerated words:")
    for w in words[:10]:  # Show first 10
        print(f"  - {w['lemma']} ({w.get('pos', '?')}): {w['translation']}")
    if len(words) > 10:
        print(f"  ... and {len(words) - 10} more")

    # Generate audio for new words (use source language for pronunciation)
    if new_count > 0:
        print("\nGenerating audio pronunciations...")
        new_lemmas = [w["lemma"] for w in words if w["lemma"] not in known_lemmas]
        generated, _ = audio.generate_all_audio(new_lemmas, lang=source_lang)
        print(f"Generated {generated} new audio files")

    # Show theme summary
    theme_info = db.get_theme_by_table_name(target_table)
    print("\nTheme summary:")
    print(f"  Table: {target_table}")
    if theme_info:
        print(f"  Total words: {theme_info['word_count']}")
        print(f"  Deck name: {theme_info['deck_name']}")


def main():
    parser = argparse.ArgumentParser(
        description="El País Vocabulary Builder - Extract Spanish vocabulary from articles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    add_parser = subparsers.add_parser("add", help="Add vocabulary from an article")
    add_parser.add_argument("url", help="El País article URL")
    add_parser.add_argument(
        "--prompt",
        default="pick useful vocabulary words",
        help="Instructions for word selection",
    )
    add_parser.add_argument(
        "--count", type=int, default=30, help="Number of words to extract (default: 30)"
    )
    add_parser.add_argument(
        "--source-lang",
        default="Spanish",
        help="Source language (default: Spanish)",
    )
    add_parser.add_argument(
        "--target-lang",
        default="French",
        help="Target language (default: French)",
    )
    add_parser.add_argument(
        "--browser",
        default="firefox",
        choices=["chrome", "firefox", "edge", "opera"],
        help="Browser to extract cookies from (default: firefox)",
    )
    add_parser.set_defaults(func=cmd_add)

    list_parser = subparsers.add_parser("list", help="List known words")
    list_parser.add_argument(
        "--limit", type=int, default=50, help="Maximum words to display (default: 50)"
    )
    list_parser.add_argument(
        "--theme", help="Filter by theme (e.g., 'el_pais')"
    )
    list_parser.set_defaults(func=cmd_list)

    export_parser = subparsers.add_parser("export", help="Export to Anki CSV")
    export_parser.add_argument(
        "--output", default="vocab.csv", help="Output filename (default: vocab.csv)"
    )
    export_parser.set_defaults(func=cmd_export)

    audio_parser = subparsers.add_parser(
        "audio", help="Generate/regenerate audio for all words"
    )
    audio_parser.set_defaults(func=cmd_audio)

    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.set_defaults(func=cmd_stats)

    sync_parser = subparsers.add_parser("sync", help="Sync vocabulary to Anki deck")
    sync_parser.add_argument(
        "--all", action="store_true", help="Sync all tables (main + all themes)"
    )
    sync_parser.add_argument(
        "--theme", help="Sync specific theme table only (e.g., vocab_cooking)"
    )
    sync_parser.add_argument(
        "--deck",
        default="el-pais",
        help="Anki deck name for main vocab (default: el-pais)",
    )
    sync_parser.add_argument(
        "--db", default="vocab.db", help="Database path (default: vocab.db)"
    )
    sync_parser.add_argument(
        "--audio-dir", default="audio", help="Audio directory (default: audio)"
    )
    sync_parser.set_defaults(func=cmd_sync)

    pick_parser = subparsers.add_parser(
        "pick", help="Pick a word based on a semantic prompt"
    )
    pick_parser.add_argument(
        "prompt", help="Semantic search query (e.g., 'a word related to the economy')"
    )
    pick_parser.add_argument(
        "--play", action="store_true", help="Play audio pronunciation if available"
    )
    pick_parser.set_defaults(func=cmd_pick)

    # Theme command
    theme_parser = subparsers.add_parser(
        "theme", help="Create or list themed vocabulary lists"
    )
    theme_parser.add_argument(
        "theme", nargs="?", help="Theme description (e.g., 'cooking vocabulary')"
    )
    theme_parser.add_argument("--source", help="Source language (e.g., Dutch, Spanish)")
    theme_parser.add_argument(
        "--target", help="Target language (e.g., English, French)"
    )
    theme_parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of words to generate (default: 20)",
    )
    theme_parser.add_argument(
        "--list", action="store_true", help="List all existing themes"
    )
    theme_parser.add_argument(
        "--force-new",
        action="store_true",
        help="Create new theme even if related one exists",
    )
    theme_parser.set_defaults(func=cmd_theme)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
