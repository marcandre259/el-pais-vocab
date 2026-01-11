import csv
import json
from pathlib import Path
from typing import List, Dict
import db


def export_csv(output_path: str = "vocab.csv", db_path: str = "vocab.db", audio_dir: str = "audio") -> int:
    """
    Export vocabulary to Anki-compatible CSV file.

    Format: lemma;french;examples;word_as_found;pos;audio

    Args:
        output_path: Path to output CSV file
        db_path: Path to SQLite database
        audio_dir: Directory containing audio files

    Returns:
        Number of words exported
    """
    words = db.get_all_words(db_path)

    if not words:
        print("No words to export")
        return 0

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')

        writer.writerow(['lemma', 'french', 'examples', 'word_as_found', 'pos', 'audio'])

        for word in words:
            lemma = word['lemma']
            french = word['french']

            examples = word.get('examples', [])
            if isinstance(examples, str):
                examples = json.loads(examples)
            examples_str = " | ".join(examples) if examples else ""

            word_as_found = word['word']
            pos = word.get('pos', '')

            audio_file = f"{audio_dir}/{lemma}.mp3"
            if Path(audio_file).exists():
                audio = f"[sound:{lemma}.mp3]"
            else:
                audio = ""

            writer.writerow([lemma, french, examples_str, word_as_found, pos, audio])

    print(f"\nExported {len(words)} words to {output_path}")
    print(f"Audio files in: {audio_dir}/")
    print(f"\nTo import into Anki:")
    print(f"1. Copy the entire '{audio_dir}/' folder contents to your Anki media folder:")
    print(f"   - Linux: ~/.local/share/Anki2/<profile>/collection.media/")
    print(f"   - macOS: ~/Library/Application Support/Anki2/<profile>/collection.media/")
    print(f"   - Windows: %APPDATA%\\Anki2\\<profile>\\collection.media\\")
    print(f"2. Import {output_path} in Anki: File → Import")
    print(f"3. Select semicolon (;) as field separator")
    print(f"4. Map fields to your card template")

    return len(words)
