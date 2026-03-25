"""
Tests for text normalization functions in add_streaming_links.py.
Covers _normalize(), _strip_diacritics(), _to_search_query(), and _word_overlap().
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "scripts"))

from add_streaming_links import _normalize, _strip_diacritics, _to_search_query, _word_overlap


# ---------------------------------------------------------------------------
# _strip_diacritics
# ---------------------------------------------------------------------------

class TestStripDiacritics:
    """Test accent/diacritic removal."""

    def test_french_accents(self):
        assert _strip_diacritics("cafe\u0301") == "cafe"

    def test_precomposed_accents(self):
        assert _strip_diacritics("\u00e9\u00e8\u00ea\u00eb") == "eeee"

    def test_german_umlauts(self):
        assert _strip_diacritics("\u00fc\u00f6\u00e4") == "uoa"

    def test_spanish_tilde(self):
        assert _strip_diacritics("\u00f1") == "n"

    def test_no_diacritics(self):
        assert _strip_diacritics("hello world") == "hello world"

    def test_empty_string(self):
        assert _strip_diacritics("") == ""

    def test_mixed_ascii_and_accents(self):
        assert _strip_diacritics("Ren\u00e9 Thomas") == "Rene Thomas"

    def test_cedilla(self):
        assert _strip_diacritics("\u00e7") == "c"

    def test_scandinavian_characters(self):
        assert _strip_diacritics("\u00e5") == "a"


# ---------------------------------------------------------------------------
# _normalize
# ---------------------------------------------------------------------------

class TestNormalize:
    """Test full normalization: diacritics, punctuation, case, ampersand, apostrophes."""

    def test_lowercase(self):
        assert _normalize("HELLO WORLD") == "hello world"

    def test_diacritics_removed(self):
        result = _normalize("Caf\u00e9 Bl\u00fc")
        assert result == "cafe blu"

    def test_ampersand_replaced(self):
        result = _normalize("Tom & Jerry")
        assert result == "tom and jerry"

    def test_curly_apostrophe_normalized(self):
        """Curly apostrophes should be converted to straight apostrophes then removed."""
        result = _normalize("it\u2019s a test")
        # After apostrophe normalization: "it's a test"
        # After punctuation removal: "it s a test"
        assert result == "it s a test"

    def test_backtick_apostrophe(self):
        result = _normalize("rock`n`roll")
        assert result == "rock n roll"

    def test_punctuation_removed(self):
        result = _normalize("hello, world! how's it?")
        assert result == "hello world how s it"

    def test_whitespace_collapsed(self):
        result = _normalize("  too   many   spaces  ")
        assert result == "too many spaces"

    def test_unicode_normalization(self):
        """Pre-composed and decomposed forms should produce the same result."""
        # e + combining acute vs precomposed e-acute
        assert _normalize("e\u0301") == _normalize("\u00e9")

    def test_complex_example(self):
        """A realistic album title with mixed issues."""
        result = _normalize("Somethin' Else & Caf\u00e9 (Deluxe)")
        assert result == "somethin else and cafe deluxe"

    def test_empty_string(self):
        assert _normalize("") == ""


# ---------------------------------------------------------------------------
# _to_search_query
# ---------------------------------------------------------------------------

class TestToSearchQuery:
    """Test search query preparation: diacritics stripped, whitespace trimmed."""

    def test_strips_accents(self):
        assert _to_search_query("Caf\u00e9") == "Cafe"

    def test_strips_leading_trailing_whitespace(self):
        assert _to_search_query("  hello  ") == "hello"

    def test_preserves_internal_spaces(self):
        assert _to_search_query("Kind of Blue") == "Kind of Blue"

    def test_preserves_case(self):
        """Unlike _normalize, _to_search_query should preserve original case."""
        assert _to_search_query("Miles Davis") == "Miles Davis"

    def test_preserves_punctuation(self):
        """Unlike _normalize, _to_search_query only strips accents and trims."""
        assert _to_search_query("Somethin' Else!") == "Somethin' Else!"

    def test_empty_string(self):
        assert _to_search_query("") == ""

    def test_combined_diacritics_and_whitespace(self):
        assert _to_search_query("  R\u00e9n\u00e9 Thomas  ") == "Rene Thomas"


# ---------------------------------------------------------------------------
# _word_overlap
# ---------------------------------------------------------------------------

class TestWordOverlap:
    """Test word overlap fraction calculation."""

    def test_full_overlap(self):
        """When all words in a appear in b, overlap should be 1.0."""
        assert _word_overlap("kind of blue", "kind of blue") == 1.0

    def test_full_overlap_b_superset(self):
        """When b contains all words of a plus extras, overlap should be 1.0."""
        assert _word_overlap("kind of blue", "kind of blue remastered edition") == 1.0

    def test_partial_overlap(self):
        """When some words match, return the fraction."""
        result = _word_overlap("kind of blue", "kind of red")
        # 2 out of 3 words match
        assert abs(result - 2 / 3) < 1e-9

    def test_no_overlap(self):
        """When no words match, overlap should be 0.0."""
        assert _word_overlap("hello world", "foo bar") == 0.0

    def test_empty_a(self):
        """When a is empty, overlap should be 0.0."""
        assert _word_overlap("", "some words") == 0.0

    def test_empty_b(self):
        """When b is empty but a is not, overlap should be 0.0."""
        assert _word_overlap("some words", "") == 0.0

    def test_both_empty(self):
        """When both are empty, overlap should be 0.0."""
        assert _word_overlap("", "") == 0.0

    def test_single_word_match(self):
        assert _word_overlap("blue", "blue note records") == 1.0

    def test_single_word_no_match(self):
        assert _word_overlap("red", "blue note records") == 0.0

    def test_duplicate_words_in_a(self):
        """Duplicate words in a should be collapsed (set behavior)."""
        # "blue blue" has set {"blue"}, which is fully in "blue note"
        assert _word_overlap("blue blue", "blue note") == 1.0

    def test_overlap_is_asymmetric(self):
        """Overlap measures fraction of a's words in b, not vice versa."""
        # a has 1 word "blue", which is in b → 1.0
        assert _word_overlap("blue", "blue note records") == 1.0
        # a has 3 words, only 1 ("blue") is in b → 1/3
        result = _word_overlap("blue note records", "blue")
        assert abs(result - 1 / 3) < 1e-9
