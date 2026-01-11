import time
from pathlib import Path
from typing import List
from gtts import gTTS


def generate_audio(lemma: str, audio_dir: str = "audio") -> str:
    """
    Generate MP3 pronunciation for a Spanish word.

    Args:
        lemma: The word to generate pronunciation for
        audio_dir: Directory to save audio files

    Returns:
        Path to the generated audio file
    """
    Path(audio_dir).mkdir(exist_ok=True)
    filepath = f"{audio_dir}/{lemma}.mp3"

    if not Path(filepath).exists():
        try:
            tts = gTTS(text=lemma, lang='es', slow=False)
            tts.save(filepath)
        except Exception as e:
            print(f"Failed to generate audio for '{lemma}': {e}")
            return None

    return filepath


def generate_all_audio(lemmas: List[str], audio_dir: str = "audio") -> tuple[int, int]:
    """
    Generate audio for all words, skipping existing files.

    Args:
        lemmas: List of words to generate audio for
        audio_dir: Directory to save audio files

    Returns:
        Tuple of (generated_count, skipped_count)
    """
    Path(audio_dir).mkdir(exist_ok=True)

    generated = 0
    skipped = 0
    failed = 0

    for lemma in lemmas:
        filepath = f"{audio_dir}/{lemma}.mp3"

        if Path(filepath).exists():
            skipped += 1
            continue

        try:
            tts = gTTS(text=lemma, lang='es', slow=False)
            tts.save(filepath)
            generated += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"Failed to generate audio for '{lemma}': {e}")
            failed += 1

    if failed > 0:
        print(f"Warning: Failed to generate audio for {failed} word(s)")

    return (generated, skipped)
