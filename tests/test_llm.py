"""Tests for LLM functions."""
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import llm


@pytest.fixture
def mock_api_key():
    """Set up mock API key for testing."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        yield


class TestSelectTranslateOutput:
    """Tests for the Pydantic output model."""

    def test_valid_output(self):
        """Test creating valid output."""
        output = llm.SelectTranslateOutput(
            word="quiero",
            lemma="querer",
            pos="verb",
            translation="vouloir (to want)",
            gender=None,
            examples=["Quiero aprender espanol"],
        )
        assert output.word == "quiero"
        assert output.lemma == "querer"
        assert output.examples == ["Quiero aprender espanol"]

    def test_optional_fields(self):
        """Test that optional fields can be None."""
        output = llm.SelectTranslateOutput(
            word="quiero",
            lemma="querer",
            pos="verb",
            translation="vouloir",
        )
        assert output.gender is None
        assert output.examples is None


class TestPickWordByPrompt:
    """Tests for pick_word_by_prompt function."""

    @patch("llm.Anthropic")
    def test_picks_correct_word(self, mock_anthropic_class, mock_api_key):
        """Test that correct word is picked based on prompt."""
        # Set up mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="1")]
        mock_client.messages.create.return_value = mock_response

        words = [
            {"lemma": "querer", "pos": "verb", "translation": "vouloir"},
            {"lemma": "casa", "pos": "noun", "translation": "maison"},
            {"lemma": "grande", "pos": "adjective", "translation": "grand"},
        ]

        result = llm.pick_word_by_prompt(words, "a word for house")

        assert result["lemma"] == "casa"

    @patch("llm.Anthropic")
    def test_handles_index_zero(self, mock_anthropic_class, mock_api_key):
        """Test that index 0 is handled correctly."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="0")]
        mock_client.messages.create.return_value = mock_response

        words = [
            {"lemma": "querer", "pos": "verb", "translation": "vouloir"},
            {"lemma": "casa", "pos": "noun", "translation": "maison"},
        ]

        result = llm.pick_word_by_prompt(words, "a verb")

        assert result["lemma"] == "querer"

    @patch("llm.Anthropic")
    def test_raises_on_missing_api_key(self, mock_anthropic_class):
        """Test that missing API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            words = [{"lemma": "test", "pos": "noun", "translation": "test"}]

            with pytest.raises(ValueError) as excinfo:
                llm.pick_word_by_prompt(words, "query")

            assert "ANTHROPIC_API_KEY" in str(excinfo.value)

    @patch("llm.Anthropic")
    def test_raises_on_invalid_index(self, mock_anthropic_class, mock_api_key):
        """Test that invalid index raises error."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="99")]  # Invalid index
        mock_client.messages.create.return_value = mock_response

        words = [
            {"lemma": "querer", "pos": "verb", "translation": "vouloir"},
        ]

        with pytest.raises(ValueError) as excinfo:
            llm.pick_word_by_prompt(words, "query")

        assert "Invalid index" in str(excinfo.value)

    @patch("llm.Anthropic")
    def test_handles_translation_field_names(self, mock_anthropic_class, mock_api_key):
        """Test that both 'translation' and 'french' field names work."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="0")]
        mock_client.messages.create.return_value = mock_response

        # Test with 'french' field name (legacy)
        words_french = [
            {"lemma": "querer", "pos": "verb", "french": "vouloir"},
        ]
        result = llm.pick_word_by_prompt(words_french, "query")
        assert result["lemma"] == "querer"

        # Test with 'translation' field name (new)
        words_translation = [
            {"lemma": "querer", "pos": "verb", "translation": "vouloir"},
        ]
        result = llm.pick_word_by_prompt(words_translation, "query")
        assert result["lemma"] == "querer"


class TestDetectRelatedTheme:
    """Tests for detect_related_theme function."""

    @patch("llm.Anthropic")
    def test_finds_related_theme(self, mock_anthropic_class, mock_api_key):
        """Test that related theme is detected."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="vocab_cooking")]
        mock_client.messages.create.return_value = mock_response

        existing_themes = [
            {
                "table_name": "vocab_cooking",
                "theme_description": "cooking vocabulary",
                "source_lang": "Dutch",
                "target_lang": "English",
            }
        ]

        result = llm.detect_related_theme(
            "kitchen words", "Dutch", "English", existing_themes
        )

        assert result is not None
        assert result["table_name"] == "vocab_cooking"

    @patch("llm.Anthropic")
    def test_returns_none_when_not_related(self, mock_anthropic_class, mock_api_key):
        """Test that None is returned when no theme is related."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="NONE")]
        mock_client.messages.create.return_value = mock_response

        existing_themes = [
            {
                "table_name": "vocab_cooking",
                "theme_description": "cooking vocabulary",
                "source_lang": "Dutch",
                "target_lang": "English",
            }
        ]

        result = llm.detect_related_theme(
            "sports vocabulary", "Dutch", "English", existing_themes
        )

        assert result is None

    def test_returns_none_when_no_matching_language_pair(self, mock_api_key):
        """Test that None is returned when no themes match language pair."""
        existing_themes = [
            {
                "table_name": "vocab_cooking",
                "theme_description": "cooking vocabulary",
                "source_lang": "Spanish",
                "target_lang": "French",
            }
        ]

        # No API call needed - should return None early
        result = llm.detect_related_theme(
            "cooking words", "Dutch", "English", existing_themes
        )

        assert result is None

    def test_returns_none_when_no_themes_exist(self, mock_api_key):
        """Test that None is returned when no themes exist."""
        result = llm.detect_related_theme("cooking words", "Dutch", "English", [])
        assert result is None


class TestSelectAndTranslate:
    """Tests for select_and_translate function."""

    @patch("llm.Anthropic")
    def test_returns_word_list(self, mock_anthropic_class, mock_api_key):
        """Test that word list is returned."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Create a SelectTranslateOutputList mock that passes isinstance check
        mock_parsed = MagicMock(spec=llm.SelectTranslateOutputList)
        mock_parsed.model_dump.return_value = {
            "output_list": [
                {
                    "word": "quiero",
                    "lemma": "querer",
                    "pos": "verb",
                    "translation": "vouloir",
                    "gender": None,
                    "examples": ["Quiero aprender"],
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.parsed_output = mock_parsed
        mock_client.messages.parse.return_value = mock_response

        result = llm.select_and_translate(
            article_text="Este es un texto de prueba.",
            known_words=["tener", "ser"],
            target_lang="French",
            source_lang="Spanish",
            user_prompt="pick useful words",
            count=1,
        )

        assert len(result) == 1
        assert result[0]["lemma"] == "querer"
        assert result[0]["translation"] == "vouloir"

    @patch("llm.Anthropic")
    def test_raises_on_missing_api_key(self, mock_anthropic_class):
        """Test that missing API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)

            with pytest.raises(ValueError) as excinfo:
                llm.select_and_translate(
                    article_text="text",
                    known_words=[],
                    target_lang="French",
                    source_lang="Spanish",
                    user_prompt="prompt",
                    count=1,
                )

            assert "ANTHROPIC_API_KEY" in str(excinfo.value)


class TestGenerateThemedVocabulary:
    """Tests for generate_themed_vocabulary function."""

    @patch("llm.Anthropic")
    def test_generates_vocabulary(self, mock_anthropic_class, mock_api_key):
        """Test that themed vocabulary is generated."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock the streaming response
        mock_message = MagicMock()
        mock_message.stop_reason = "end_turn"
        mock_message.content = [
            MagicMock(
                type="text",
                text='[{"word": "koken", "lemma": "koken", "pos": "verb", "translation": "to cook", "examples": ["Ik kook graag"]}]',
            )
        ]

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.get_final_message.return_value = mock_message

        mock_client.messages.stream.return_value = mock_stream

        # Mock functions
        def mock_get_all_themes():
            return []

        def mock_search_theme_words(table_name, search_term=None):
            return []

        result = llm.generate_themed_vocabulary(
            theme_prompt="cooking vocabulary",
            source_lang="Dutch",
            target_lang="English",
            known_words=[],
            count=1,
            get_all_themes_func=mock_get_all_themes,
            search_theme_words_func=mock_search_theme_words,
        )

        assert len(result) == 1
        assert result[0]["lemma"] == "koken"

    @patch("llm.Anthropic")
    def test_handles_tool_use(self, mock_anthropic_class, mock_api_key):
        """Test that tool use is handled correctly."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # First response: tool use
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "list_themes"
        mock_tool_block.input = {}
        mock_tool_block.id = "tool_123"

        mock_message1 = MagicMock()
        mock_message1.stop_reason = "tool_use"
        mock_message1.content = [mock_tool_block]

        # Second response: final answer
        mock_message2 = MagicMock()
        mock_message2.stop_reason = "end_turn"
        mock_message2.content = [
            MagicMock(
                type="text",
                text='[{"word": "koken", "lemma": "koken", "pos": "verb", "translation": "to cook", "examples": []}]',
            )
        ]

        mock_stream1 = MagicMock()
        mock_stream1.__enter__ = MagicMock(return_value=mock_stream1)
        mock_stream1.__exit__ = MagicMock(return_value=False)
        mock_stream1.get_final_message.return_value = mock_message1

        mock_stream2 = MagicMock()
        mock_stream2.__enter__ = MagicMock(return_value=mock_stream2)
        mock_stream2.__exit__ = MagicMock(return_value=False)
        mock_stream2.get_final_message.return_value = mock_message2

        mock_client.messages.stream.side_effect = [mock_stream1, mock_stream2]

        def mock_get_all_themes():
            return []

        def mock_search_theme_words(table_name, search_term=None):
            return []

        result = llm.generate_themed_vocabulary(
            theme_prompt="cooking vocabulary",
            source_lang="Dutch",
            target_lang="English",
            known_words=[],
            count=1,
            get_all_themes_func=mock_get_all_themes,
            search_theme_words_func=mock_search_theme_words,
        )

        assert len(result) == 1
        assert result[0]["lemma"] == "koken"
