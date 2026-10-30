"""Ingredient text normalization shared by the index builder and the API."""

import re

_WHITESPACE = re.compile(r"\s+")
_PARENTHETICAL = re.compile(r"\([^)]*\)")
_NON_WORD = re.compile(r"[^a-z0-9\s\-']")
_SEPARATORS = re.compile(r"\s*[-/]\s*")


def normalize_text(text: str) -> str:
    """Lowercase and strip punctuation while keeping word boundaries intact."""
    value = str(text).lower().replace("&amp;", " and ").replace("&quot;", '"')
    value = _PARENTHETICAL.sub(" ", value)
    value = _SEPARATORS.sub(" ", value)
    value = _NON_WORD.sub(" ", value)
    return _WHITESPACE.sub(" ", value).strip()


def word_pattern(term: str) -> re.Pattern[str]:
    """Match a whole term, so 'apple' never matches 'pineapple'."""
    return re.compile(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])")


def contains_term(term: str, text: str) -> bool:
    return word_pattern(term).search(text) is not None


def matches_any(terms: list[str], text: str) -> bool:
    return any(contains_term(term, text) for term in terms)
