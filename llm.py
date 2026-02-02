import os
import json
import re
from typing import List, Dict, Optional
from anthropic import Anthropic, transform_schema
from pydantic import BaseModel, Field
from dotenv import load_dotenv


load_dotenv()


class SelectTranslateOutput(BaseModel):
    word: str
    lemma: str = Field(description="Canonical form of word")
    pos: str = Field(
        description="Part of speech of the word: can be adjective, noun, adverb, etc."
    )
    translation: str = Field(
        description=(
            "Translation of the word, should include the translate lemma whenever relevant "
            "e.g. translated word (translated lemma)"
        )
    )
    gender: Optional[str] = Field(
        default=None, description="Gender or Pronoun, gives context as to usage"
    )
    examples: Optional[List[str]] = Field(
        default=None,
        description="1-2 example sentences where the word is used in the source language",
    )


class SelectTranslateOutputList(BaseModel):
    output_list: List[SelectTranslateOutput] = Field(
        description="List of the translation outputs"
    )


def select_and_translate(
    article_text: str,
    known_words: List[str],
    target_lang: str,
    source_lang: str,
    user_prompt: str,
    count: int,
) -> Optional[List[Dict]]:
    """
    Use Claude Haiku to select and translate Spanish vocabulary words.

    Args:
        article_text: Full text of the Spanish article
        known_words: List of lemmas already in database (to exclude)
        user_prompt: User's instructions for word selection
        count: Number of words to select

    Returns:
        List of dicts with keys: word, lemma, pos, french, examples
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    client = Anthropic(api_key=api_key)

    system_prompt = f"""
    You are a {source_lang}-{target_lang} vocabulary assistant. Given a Spanish news article,
    select vocabulary words for a French speaker learning Spanish.

    Rules:
    - Return exactly {count} words as JSON array
    - Exclude words already known (provided in list)
    - For verbs: "word" = conjugated form found, "lemma" = infinitive
    - pos is Part of Speech
    - gender is a pronoun or gender depending on context/word
    - Translation is the translated word and translated lemma (when useful) in parenthesis
    - Translation MUST BE IN {target_lang}
    - Include 1-2 example sentences for each word
    - target_lang should include the translation matching the context, plus infinitive for verbs
    - Prioritize useful vocabulary over obscure terms
    - Include a mix: verbs, nouns, adjectives, adverbs, prepositions, conjunctions
    - Include pronouns and common phrases if relevant to user prompt
    - The translated lemma helps contextualized a word, but it is of course not always necessary.
    """

    known_words_str = ", ".join(known_words) if known_words else "none"

    user_message = f"Article text:\n{article_text}\n\n"

    user_message += f"Known words (exclude these):\n{known_words_str}\n\n"

    user_message += f"User request: {user_prompt}\n\n"

    user_message += f"Select {count} vocabulary words."

    max_tokens = int(count * 150) + 1000

    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            response = client.messages.parse(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                output_format=SelectTranslateOutputList,
            )

            parsed_response = response.parsed_output

            break

        except Exception as e:
            if attempt == max_attempts - 1:
                raise ValueError(e)
            else:
                continue

    if isinstance(parsed_response, SelectTranslateOutputList):
        output = parsed_response.model_dump()
        output = output.get("output_list", None)
        if output is None:
            raise ValueError("Parsed response does not have a output_list key")
    else:
        raise ValueError("Parsed response is not in the correct format")

    return output


# ============ Themed Vocabulary Functions ============


def generate_themed_vocabulary(
    theme_prompt: str,
    source_lang: str,
    target_lang: str,
    known_words: List[str],
    count: int,
    get_all_themes_func,
    search_theme_words_func,
) -> List[Dict]:
    """
    Generate vocabulary based on a theme using Claude with tool use.

    Args:
        theme_prompt: Theme description (e.g., "cooking vocabulary")
        source_lang: Source language (e.g., "Dutch", "Spanish")
        target_lang: Target language (e.g., "English", "French")
        known_words: List of lemmas already in this theme (to exclude)
        count: Number of words to generate
        get_all_themes_func: Function to get all themes from database
        search_theme_words_func: Function to search words in a theme table

    Returns:
        List of dicts with keys: word, lemma, pos, translation, examples
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    client = Anthropic(api_key=api_key)

    system_prompt = f"""You are a vocabulary assistant. Generate {source_lang} vocabulary words for someone learning {source_lang} who speaks {target_lang}, based on the given theme.

You have access to tools to look up existing vocabulary in related themes. Use these to:
- Avoid generating words that already exist in related themes
- Ensure consistency with existing vocabulary style
- Find gaps in related themes that could be filled

Rules:
- Return exactly {count} words as JSON array
- Exclude words already known (provided list) AND words found in related themes
- For verbs: "word" = common conjugated form, "lemma" = infinitive/base form
- Create 1-2 example sentences in {source_lang} demonstrating the word in context
- Prioritize practical, commonly-used vocabulary for the theme
- "translation" should be in {target_lang}

Output format (JSON array only, no markdown):
[
  {{
    "word": "koken",
    "lemma": "koken",
    "pos": "verb",
    "translation": "to cook",
    "examples": ["Ik kook graag met mijn oma", "We gaan vanavond pasta koken"]
  }}
]"""

    tools = [
        {
            "name": "lookup_theme_words",
            "description": "Look up existing vocabulary words in a theme table to check for duplicates or find related words",
            "input_schema": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "The theme table name to query (e.g., 'vocab_cooking_vocabulary')",
                    },
                    "search_term": {
                        "type": "string",
                        "description": "Optional: filter words containing this term",
                    },
                },
                "required": ["table_name"],
            },
        },
        {
            "name": "list_themes",
            "description": "List all available theme tables with their descriptions and language pairs",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        },
    ]

    known_words_str = ", ".join(known_words) if known_words else "none"

    user_message = f"""Theme: {theme_prompt}
Source language: {source_lang}
Target language: {target_lang}

Known words in this theme (exclude these):
{known_words_str}

First, use the list_themes tool to see if there are related themes you should check for existing vocabulary. Then generate {count} vocabulary words. Return JSON array only at the end."""

    max_tokens = int(count * 150) + 2000  # Extra tokens for tool use

    messages = [{"role": "user", "content": user_message}]

    # Tool use loop
    for attempt in range(5):  # Max 5 tool use iterations
        try:
            with client.messages.stream(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                system=system_prompt,
                tools=tools,
                messages=messages,
            ) as stream:
                response = stream.get_final_message()

            # Check if we need to handle tool use
            if response.stop_reason == "tool_use":
                # Process tool calls
                tool_results = []
                assistant_content = response.content

                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        if tool_name == "list_themes":
                            themes = get_all_themes_func()
                            result = []
                            for t in themes:
                                result.append(
                                    f"- {t['table_name']}: \"{t['theme_description']}\" ({t['source_lang']} → {t['target_lang']}, {t['word_count']} words)"
                                )
                            tool_result = (
                                "\n".join(result) if result else "No themes found."
                            )
                        elif tool_name == "lookup_theme_words":
                            table_name = tool_input.get("table_name")
                            search_term = tool_input.get("search_term")
                            try:
                                words = search_theme_words_func(table_name, search_term)
                                if words:
                                    result = []
                                    for w in words[:50]:  # Limit to 50 words
                                        result.append(
                                            f"- {w['lemma']} ({w.get('pos', 'unknown')}): {w['translation']}"
                                        )
                                    tool_result = "\n".join(result)
                                else:
                                    tool_result = "No words found in this theme."
                            except Exception as e:
                                tool_result = f"Error: {str(e)}"
                        else:
                            tool_result = f"Unknown tool: {tool_name}"

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": tool_result,
                            }
                        )

                # Add assistant response and tool results to messages
                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": tool_results})
                continue

            # No more tool use, extract the final response
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            response_text = response_text.strip()

            # Handle markdown code blocks
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(
                    lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                )

            # Find JSON array in response
            json_match = re.search(r"\[[\s\S]*\]", response_text)
            if json_match:
                response_text = json_match.group()

            words = json.loads(response_text)
            return words

        except json.JSONDecodeError as e:
            if attempt < 2:
                print(f"JSON parsing error (attempt {attempt + 1}/3): {e}")
                print("Retrying...")
                # Reset messages for retry
                messages = [{"role": "user", "content": user_message}]
            else:
                print(f"JSON parsing error: {e}")
                print(f"Raw response:\n{response_text}")
                raise RuntimeError(f"Failed to parse JSON after 3 attempts: {e}")
        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}")

    raise RuntimeError("Max tool use iterations reached")


def pick_word_by_prompt(words: List[Dict], prompt: str) -> Dict:
    """
    Use LLM to pick a word from the vocabulary based on a semantic prompt.

    Args:
        words: List of vocabulary dictionaries
        prompt: User's semantic search query

    Returns:
        The selected word dictionary

    Raises:
        ValueError: If no word is selected or API error occurs
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    client = Anthropic(api_key=api_key)

    # Create a simplified list of words for the LLM
    word_list = []
    for i, w in enumerate(words):
        translation = w.get("translation", w.get("french", ""))
        word_list.append(f"{i}: {w['lemma']} ({w.get('pos', '?')}) - {translation}")

    words_str = "\n".join(word_list)

    system_prompt = """You are a vocabulary assistant. Given a list of vocabulary words and a semantic query, select the single best matching word.

Return ONLY the index number (0, 1, 2, etc.) of the best matching word. No explanation, just the number."""

    user_message = f"""Words:
{words_str}

Query: {prompt}

Return only the index number of the best match."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        result = response.content[0].text.strip()

        # Extract the number from the response
        index = int(re.search(r"\d+", result).group())

        if 0 <= index < len(words):
            return words[index]
        else:
            raise ValueError(f"Invalid index returned: {index}")

    except Exception as e:
        raise ValueError(f"Error selecting word: {e}")


def detect_related_theme(
    new_theme: str,
    source_lang: str,
    target_lang: str,
    existing_themes: List[Dict],
) -> Dict | None:
    """
    Use LLM to determine if a new theme is related to an existing one.

    Args:
        new_theme: The new theme prompt
        source_lang: Source language for the new theme
        target_lang: Target language for the new theme
        existing_themes: List of dicts with theme metadata

    Returns:
        Related theme dict if found, None otherwise
    """
    # Filter themes by matching language pair
    matching_themes = [
        t
        for t in existing_themes
        if t["source_lang"].lower() == source_lang.lower()
        and t["target_lang"].lower() == target_lang.lower()
    ]

    if not matching_themes:
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    client = Anthropic(api_key=api_key)

    system_prompt = """You are analyzing vocabulary themes for a language learning app. Given a new theme and a list of existing themes, determine if the new theme is semantically related enough to be merged with an existing one.

Rules:
- Return ONLY the table_name of the related theme, or "NONE" if no theme is related
- Themes are related if:
  - They cover the same topic area (e.g., "cooking verbs" relates to "kitchen vocabulary")
  - One is a subset of another (e.g., "tapas vocabulary" relates to "Spanish food")
  - They would logically share vocabulary (e.g., "business emails" and "office vocabulary")
- Themes are NOT related if:
  - They are distinct topics (e.g., "cooking" vs "sports")
  - The overlap would be minimal (e.g., "medical terms" vs "general conversation")

Return only the table_name or "NONE"."""

    themes_list = []
    for t in matching_themes:
        themes_list.append(f"- {t['table_name']}: \"{t['theme_description']}\"")

    user_message = f"""New theme: "{new_theme}"
Language pair: {source_lang} → {target_lang}

Existing themes with same language pair:
{chr(10).join(themes_list)}

Return only the table_name of the most related theme, or "NONE"."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        result = response.content[0].text.strip()

        if result == "NONE":
            return None

        # Find the matching theme
        for theme in matching_themes:
            if theme["table_name"] == result:
                return theme

        return None

    except Exception as e:
        print(f"Warning: Could not detect related theme: {e}")
        return None
