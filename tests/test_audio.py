"""Tests for audio generation."""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core import audio


class TestLanguageCodes:
    """Tests for language code mapping."""

    def test_get_language_code_spanish(self):
        """Test Spanish language code."""
        assert audio.get_language_code("Spanish") == "es"
        assert audio.get_language_code("spanish") == "es"
        assert audio.get_language_code("SPANISH") == "es"

    def test_get_language_code_dutch(self):
        """Test Dutch language code."""
        assert audio.get_language_code("Dutch") == "nl"
        assert audio.get_language_code("dutch") == "nl"

    def test_get_language_code_french(self):
        """Test French language code."""
        assert audio.get_language_code("French") == "fr"

    def test_get_language_code_german(self):
        """Test German language code."""
        assert audio.get_language_code("German") == "de"

    def test_get_language_code_already_code(self):
        """Test that short codes are returned as-is (lowercased)."""
        assert audio.get_language_code("es") == "es"
        assert audio.get_language_code("nl") == "nl"
        # Note: codes are lowercased by the function
        assert audio.get_language_code("zh-CN") == "zh-cn"

    def test_get_language_code_unsupported(self):
        """Test unsupported language raises error."""
        with pytest.raises(ValueError) as excinfo:
            audio.get_language_code("Klingon")
        assert "Unsupported language" in str(excinfo.value)

    def test_all_supported_languages(self):
        """Test all languages in LANGUAGE_CODES are valid."""
        for lang_name, lang_code in audio.LANGUAGE_CODES.items():
            assert audio.get_language_code(lang_name) == lang_code


class TestGenerateAudio:
    """Tests for generate_audio function."""

    @pytest.fixture
    def temp_audio_dir(self):
        """Create temporary directory for audio files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @patch("audio.gTTS")
    def test_generates_audio_file(self, mock_gtts, temp_audio_dir):
        """Test that audio file is generated."""
        mock_tts = MagicMock()
        mock_gtts.return_value = mock_tts

        result = audio.generate_audio("querer", lang="es", audio_dir=temp_audio_dir)

        assert result == f"{temp_audio_dir}/querer.mp3"
        mock_gtts.assert_called_once_with(text="querer", lang="es", slow=False)
        mock_tts.save.assert_called_once()

    @patch("audio.gTTS")
    def test_uses_language_name(self, mock_gtts, temp_audio_dir):
        """Test that language name is converted to code."""
        mock_tts = MagicMock()
        mock_gtts.return_value = mock_tts

        audio.generate_audio("koken", lang="Dutch", audio_dir=temp_audio_dir)

        mock_gtts.assert_called_once_with(text="koken", lang="nl", slow=False)

    @patch("audio.gTTS")
    def test_skips_existing_file(self, mock_gtts, temp_audio_dir):
        """Test that existing files are not regenerated."""
        # Create existing file
        existing_file = Path(temp_audio_dir) / "querer.mp3"
        existing_file.touch()

        result = audio.generate_audio("querer", lang="es", audio_dir=temp_audio_dir)

        assert result == str(existing_file)
        mock_gtts.assert_not_called()

    @patch("audio.gTTS")
    def test_creates_audio_directory(self, mock_gtts, temp_audio_dir):
        """Test that audio directory is created if not exists."""
        mock_tts = MagicMock()
        mock_gtts.return_value = mock_tts

        new_dir = os.path.join(temp_audio_dir, "new_audio_dir")
        audio.generate_audio("querer", lang="es", audio_dir=new_dir)

        assert os.path.exists(new_dir)

    @patch("audio.gTTS")
    def test_handles_gtts_error(self, mock_gtts, temp_audio_dir):
        """Test that gTTS errors are handled gracefully."""
        mock_gtts.side_effect = Exception("API error")

        result = audio.generate_audio("querer", lang="es", audio_dir=temp_audio_dir)

        assert result is None


class TestGenerateAllAudio:
    """Tests for generate_all_audio function."""

    @pytest.fixture
    def temp_audio_dir(self):
        """Create temporary directory for audio files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @patch("audio.gTTS")
    @patch("audio.time.sleep")
    def test_generates_multiple_files(self, mock_sleep, mock_gtts, temp_audio_dir):
        """Test generating audio for multiple words."""
        mock_tts = MagicMock()
        mock_gtts.return_value = mock_tts

        lemmas = ["querer", "casa", "grande"]
        generated, skipped = audio.generate_all_audio(
            lemmas, lang="es", audio_dir=temp_audio_dir
        )

        assert generated == 3
        assert skipped == 0
        assert mock_gtts.call_count == 3

    @patch("audio.gTTS")
    @patch("audio.time.sleep")
    def test_skips_existing_files(self, mock_sleep, mock_gtts, temp_audio_dir):
        """Test that existing files are skipped."""
        mock_tts = MagicMock()
        mock_gtts.return_value = mock_tts

        # Create existing file
        existing_file = Path(temp_audio_dir) / "querer.mp3"
        existing_file.touch()

        lemmas = ["querer", "casa"]
        generated, skipped = audio.generate_all_audio(
            lemmas, lang="es", audio_dir=temp_audio_dir
        )

        assert generated == 1
        assert skipped == 1
        assert mock_gtts.call_count == 1

    @patch("audio.gTTS")
    @patch("audio.time.sleep")
    def test_uses_language_parameter(self, mock_sleep, mock_gtts, temp_audio_dir):
        """Test that language parameter is used."""
        mock_tts = MagicMock()
        mock_gtts.return_value = mock_tts

        lemmas = ["koken"]
        audio.generate_all_audio(lemmas, lang="Dutch", audio_dir=temp_audio_dir)

        mock_gtts.assert_called_with(text="koken", lang="nl", slow=False)

    @patch("audio.gTTS")
    @patch("audio.time.sleep")
    def test_adds_delay_between_requests(self, mock_sleep, mock_gtts, temp_audio_dir):
        """Test that delay is added between TTS requests."""
        mock_tts = MagicMock()
        mock_gtts.return_value = mock_tts

        lemmas = ["querer", "casa", "grande"]
        audio.generate_all_audio(lemmas, lang="es", audio_dir=temp_audio_dir)

        # Should sleep between each word (3 words = 3 sleeps)
        assert mock_sleep.call_count == 3

    @patch("audio.gTTS")
    @patch("audio.time.sleep")
    def test_continues_on_error(self, mock_sleep, mock_gtts, temp_audio_dir):
        """Test that generation continues even if one word fails."""
        mock_tts = MagicMock()

        # Make second call fail
        def gtts_side_effect(text, lang, slow):
            if text == "casa":
                raise Exception("API error")
            return mock_tts

        mock_gtts.side_effect = gtts_side_effect

        lemmas = ["querer", "casa", "grande"]
        generated, skipped = audio.generate_all_audio(
            lemmas, lang="es", audio_dir=temp_audio_dir
        )

        assert generated == 2
        assert skipped == 0

    @patch("audio.gTTS")
    @patch("audio.time.sleep")
    def test_empty_list(self, mock_sleep, mock_gtts, temp_audio_dir):
        """Test handling empty lemma list."""
        generated, skipped = audio.generate_all_audio(
            [], lang="es", audio_dir=temp_audio_dir
        )

        assert generated == 0
        assert skipped == 0
        mock_gtts.assert_not_called()
