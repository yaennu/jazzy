"""
Tests for text normalization functions in add_streaming_links.py.
Covers _normalize(), _strip_diacritics(), _to_search_query(), and _word_overlap().
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "scripts"))

from add_streaming_links import _normalize, _strip_diacritics, _to_search_query, _word_overlap


# ---------------------------------------------------------------------------
# _strip_diacritics
# ---------------------------------------------------------------------------

class TestStripDiacritics:
    """Test accent/diacritics removal."""

    def test_basic_accents(self):
        assert _strip_diacritics("cafe") == "cafe"

    def test_french_accents(self):
        assert _strip_diacritics("r\u00e9sum\u00e9") == "resume"

    def test_acute_and_grave(self):
        assert _strip_diacritics("\u00e9\u00e8\u00ea\u00eb") == "eeee"

    def test_german_umlauts(self):
        """NFD decomposition turns u+00fc (u with diaeresis) into u + combining diaeresis."""
        assert _strip_diacritics("\u00fc\u00f6\u00e4") == "uoa"

    def test_tilde(self):
        assert _strip_diacritics("\u00f1") == "n"

    def test_cedilla(self):
        assert _strip_diacritics("\u00e7") == "c"

    def test_no_diacritics_unchanged(self):
        assert _strip_diacritics("hello world") == "hello world"

    def test_empty_string(self):
        assert _strip_diacritics("") == ""

    def test_mixed_ascii_and_accented(self):
        assert _strip_diacritics("Bj\u00f6rk") == "Bjork"

    def test_preserves_case(self):
        assert _strip_diacritics("\u00c9cole") == "Ecole"


# ---------------------------------------------------------------------------
# _normalize
# ---------------------------------------------------------------------------

class TestNormalize:
    """Test full text normalization for fuzzy comparison."""

    def test_lowercases(self):
        assert _normalize("HELLO WORLD") == "hello world"

    def test_strips_diacritics(self):
        assert _normalize("\u00c9tude") == "etude"

    def test_ampersand_replaced_with_and(self):
        assert _normalize("Tom & Jerry") == "tom and jerry"

    def test_curly_apostrophe_normalized(self):
        """Curly/smart apostrophes should be converted to straight apostrophes, then removed."""
        result = _normalize("It\u2019s a test")
        # After normalizing apostrophe to ' and then removing punctuation
        assert result == "it s a test"

    def test_backtick_apostrophe_normalized(self):
        result = _normalize("It`s here")
        assert result == "it s here"

    def test_punctuation_removed(self):
        assert _normalize("Hello, World!") == "hello world"

    def test_extra_whitespace_collapsed(self):
        assert _normalize("  multiple   spaces  ") == "multiple spaces"

    def test_complex_example(self):
        result = _normalize("Th\u00e9l\u00f4nious Monk & Sonny Rollins")
        assert result == "thelonious monk and sonny rollins"

    def test_unicode_quotes_removed(self):
        result = _normalize("\u201cBig Band\u201d")
        assert result == "big band"

    def test_parentheses_removed(self):
        result = _normalize("Album (Deluxe Edition)")
        assert result == "album deluxe edition"

    def test_hyphens_removed(self):
        result = _normalize("Bird-Land")
        assert result == "bird land"

    def test_empty_string(self):
        assert _normalize("") == ""

    def test_numbers_preserved(self):
        result = _normalize("Vol. 2")
        assert result == "vol 2"


# ---------------------------------------------------------------------------
# _to_search_query
# ---------------------------------------------------------------------------

class TestToSearchQuery:
    """Test iTunes search query preparation."""

    def test_strips_diacritics(self):
        assert _to_search_query("caf\u00e9") == "cafe"

    def test_strips_leading_trailing_whitespace(self):
        assert _to_search_query("  hello world  ") == "hello world"

    def test_preserves_case(self):
        """Unlike _normalize, _to_search_query preserves case."""
        assert _to_search_query("Miles Davis") == "Miles Davis"

    def test_preserves_punctuation(self):
        """Unlike _normalize, _to_search_query preserves punctuation."""
        assert _to_search_query("It's a Test!") == "It's a Test!"

    def test_empty_string(self):
        assert _to_search_query("") == ""

    def test_internal_whitespace_preserved(self):
        """Internal whitespace is not collapsed (only strip_diacritics + strip)."""
        result = _to_search_query("hello   world")
        assert result == "hello   world"

    def test_combined_accents_and_whitespace(self):
        result = _to_search_query("  \u00c9cole de Musique  ")
        assert result == "Ecole de Musique"


# ---------------------------------------------------------------------------
# _word_overlap
# ---------------------------------------------------------------------------

class TestWordOverlap:
    """Test fractional word overlap calculation."""

    def test_full_overlap(self):
        """When all words in a appear in b, overlap is 1.0."""
        assert _word_overlap("hello world", "hello world") == 1.0

    def test_partial_overlap(self):
        """When some words overlap, the fraction is correct."""
        result = _word_overlap("hello world", "hello there")
        assert result == pytest.approx(0.5)

    def test_no_overlap(self):
        """When no words overlap, result is 0.0."""
        assert _word_overlap("hello world", "foo bar") == 0.0

    def test_empty_first_string(self):
        """When a is empty, result is 0.0 (avoids division by zero)."""
        assert _word_overlap("", "hello world") == 0.0

    def test_empty_second_string(self):
        """When b is empty, no words from a can match."""
        assert _word_overlap("hello world", "") == 0.0

    def test_both_empty(self):
        assert _word_overlap("", "") == 0.0

    def test_superset_b(self):
        """When b contains all of a's words and more, overlap is 1.0."""
        assert _word_overlap("blue", "kind of blue") == 1.0

    def test_subset_a(self):
        """When a has more words than b, overlap reflects b's coverage of a."""
        result = _word_overlap("kind of blue", "blue")
        assert result == pytest.approx(1.0 / 3.0)

    def test_duplicate_words_counted_once(self):
        """Duplicate words in a should be deduplicated (set-based)."""
        result = _word_overlap("the the the", "the")
        assert result == 1.0

    def test_case_sensitive(self):
        """_word_overlap is case-sensitive (it operates on raw strings)."""
        result = _word_overlap("Hello", "hello")
        assert result == 0.0
