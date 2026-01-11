import os
import json
from typing import List, Dict
from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()


def select_and_translate(
    article_text: str, known_words: List[str], user_prompt: str, count: int
) -> List[Dict]:
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

    system_prompt = f"""You are a Spanish-French vocabulary assistant. Given a Spanish news article, select vocabulary words for a French speaker learning Spanish.

Rules:
- Return exactly {count} words as JSON array
- Exclude words already known (provided in list)
- For verbs: "word" = conjugated form found, "lemma" = infinitive
- Include 1-2 example sentences from the article for each word
- "french" should include the translation matching the context, plus infinitive for verbs
- Prioritize useful vocabulary over obscure terms
- Include a mix: verbs, nouns, adjectives, adverbs, prepositions, conjunctions
- Include pronouns and common phrases if relevant to user prompt

Output format (JSON array only, no markdown):
[
  {{
    "word": "quiere",
    "lemma": "querer",
    "pos": "verb",
    "french": "veut (vouloir)",
    "examples": ["Trump quiere imponer su ley"]
  }}
]"""

    known_words_str = ", ".join(known_words) if known_words else "none"

    user_message = f"""Article text:
{article_text}

Known words (exclude these):
{known_words_str}

User request: {user_prompt}

Select {count} vocabulary words. Return JSON array only."""

    max_tokens = int(count * 150) + 1000

    for attempt in range(3):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            response_text = response.content[0].text.strip()

            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(
                    lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                )

            words = json.loads(response_text)
            return words

        except json.JSONDecodeError as e:
            if attempt < 2:
                print(f"JSON parsing error (attempt {attempt + 1}/3): {e}")
                print("Retrying...")
            else:
                print(f"JSON parsing error: {e}")
                print(f"Raw response:\n{response_text}")
                raise RuntimeError(f"Failed to parse JSON after 3 attempts: {e}")
        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}")
