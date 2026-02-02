import time
from pathlib import Path
from typing import List, Optional
from gtts import gTTS


# Language name to gTTS language code mapping
LANGUAGE_CODES = {
    "spanish": "es",
    "french": "fr",
    "dutch": "nl",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "english": "en",
    "russian": "ru",
    "japanese": "ja",
    "chinese": "zh-CN",
    "korean": "ko",
    "arabic": "ar",
    "hindi": "hi",
    "polish": "pl",
    "turkish": "tr",
    "swedish": "sv",
    "norwegian": "no",
    "danish": "da",
    "finnish": "fi",
    "greek": "el",
    "czech": "cs",
    "romanian": "ro",
    "hungarian": "hu",
    "thai": "th",
    "vietnamese": "vi",
    "indonesian": "id",
    "malay": "ms",
    "tagalog": "tl",
    "ukrainian": "uk",
    "catalan": "ca",
    "hebrew": "iw",
}


def get_language_code(language: str) -> str:
    """
    Convert language name to gTTS language code.

    Args:
        language: Language name (e.g., "Spanish", "Dutch")

    Returns:
        gTTS language code (e.g., "es", "nl")

    Raises:
        ValueError: If language is not supported
    """
    lang_lower = language.lower()

    # Check direct mapping
    if lang_lower in LANGUAGE_CODES:
        return LANGUAGE_CODES[lang_lower]

    # Check if it's already a valid code
    if len(lang_lower) <= 5:  # Could be a code like "zh-CN"
        return lang_lower

    raise ValueError(
        f"Unsupported language: {language}. "
        f"Supported languages: {', '.join(LANGUAGE_CODES.keys())}"
    )


def generate_audio(
    lemma: str, lang: str = "es", audio_dir: str = "audio"
) -> Optional[str]:
    """
    Generate MP3 pronunciation for a word.

    Args:
        lemma: The word to generate pronunciation for
        lang: Language code (e.g., "es", "nl") or language name (e.g., "Spanish", "Dutch")
        audio_dir: Directory to save audio files

    Returns:
        Path to the generated audio file, or None on failure
    """
    Path(audio_dir).mkdir(exist_ok=True)
    filepath = f"{audio_dir}/{lemma}.mp3"

    # Convert language name to code if needed
    try:
        lang_code = get_language_code(lang)
    except ValueError:
        lang_code = lang  # Use as-is if not in mapping

    if not Path(filepath).exists():
        try:
            tts = gTTS(text=lemma, lang=lang_code, slow=False)
            tts.save(filepath)
        except Exception as e:
            print(f"Failed to generate audio for '{lemma}' (lang={lang_code}): {e}")
            return None

    return filepath


def generate_all_audio(
    lemmas: List[str], lang: str = "es", audio_dir: str = "audio"
) -> tuple[int, int]:
    """
    Generate audio for all words, skipping existing files.

    Args:
        lemmas: List of words to generate audio for
        lang: Language code (e.g., "es", "nl") or language name (e.g., "Spanish", "Dutch")
        audio_dir: Directory to save audio files

    Returns:
        Tuple of (generated_count, skipped_count)
    """
    Path(audio_dir).mkdir(exist_ok=True)

    # Convert language name to code if needed
    try:
        lang_code = get_language_code(lang)
    except ValueError:
        lang_code = lang  # Use as-is if not in mapping

    generated = 0
    skipped = 0
    failed = 0

    for lemma in lemmas:
        filepath = f"{audio_dir}/{lemma}.mp3"

        if Path(filepath).exists():
            skipped += 1
            continue

        try:
            tts = gTTS(text=lemma, lang=lang_code, slow=False)
            tts.save(filepath)
            generated += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"Failed to generate audio for '{lemma}' (lang={lang_code}): {e}")
            failed += 1

    if failed > 0:
        print(f"Warning: Failed to generate audio for {failed} word(s)")

    return (generated, skipped)
