"""Integration tests -- require OPENAI_API_KEY to be set.

Run with: pytest tests/test_feedback_integration.py -v
"""

import os
import pytest
from app.feedback import get_feedback
from app.models import FeedbackRequest

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set -- skipping integration tests",
)

VALID_ERROR_TYPES = {
    "grammar", "spelling", "word_choice", "punctuation", "word_order",
    "missing_word", "extra_word", "conjugation", "gender_agreement",
    "number_agreement", "tone_register", "other",
}
VALID_DIFFICULTIES = {"A1", "A2", "B1", "B2", "C1", "C2"}


def assert_valid_response(result):
    """Helper to check every response is valid."""
    assert result.corrected_sentence is not None
    assert isinstance(result.is_correct, bool)
    assert isinstance(result.errors, list)
    assert result.difficulty in VALID_DIFFICULTIES
    for error in result.errors:
        assert error.error_type in VALID_ERROR_TYPES
        assert len(error.original) > 0
        assert len(error.correction) > 0
        assert len(error.explanation) > 0


@pytest.mark.asyncio
async def test_spanish_conjugation_error():
    """Spanish sentence with conjugation error."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="Yo soy fue al mercado ayer.",
            target_language="Spanish",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 1
    assert_valid_response(result)


@pytest.mark.asyncio
async def test_correct_german_sentence():
    """Correct German sentence should return no errors."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="Ich habe gestern einen interessanten Film gesehen.",
            target_language="German",
            native_language="English",
        )
    )
    assert result.is_correct is True
    assert result.errors == []
    assert result.corrected_sentence == "Ich habe gestern einen interessanten Film gesehen."
    assert_valid_response(result)


@pytest.mark.asyncio
async def test_french_gender_agreement_error():
    """French sentence with gender agreement errors."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="La chat noir est sur le table.",
            target_language="French",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 1
    assert_valid_response(result)


@pytest.mark.asyncio
async def test_japanese_particle_error():
    """Japanese sentence with wrong particle (non-Latin script)."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="私は東京を住んでいます。",
            target_language="Japanese",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 1
    assert_valid_response(result)


@pytest.mark.asyncio
async def test_correct_french_sentence():
    """Correct French sentence should return no errors."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="Je mange une pomme.",
            target_language="French",
            native_language="English",
        )
    )
    assert result.is_correct is True
    assert result.errors == []
    assert_valid_response(result)


@pytest.mark.asyncio
async def test_portuguese_multiple_errors():
    """Portuguese sentence with multiple errors."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="Eu gosto muito de the Brasil.",
            target_language="Portuguese",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 1
    assert_valid_response(result)


@pytest.mark.asyncio
async def test_hindi_error():
    """Hindi sentence with grammatical error (non-Latin script)."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="मैं कल बाजार जाता हूँ।",
            target_language="Hindi",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 1
    assert_valid_response(result)


@pytest.mark.asyncio
async def test_tamil_correct_sentence():
    """Correct Tamil sentence should return no errors (non-Latin script)."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="நான் தமிழ் படிக்கிறேன்.",
            target_language="Tamil",
            native_language="English",
        )
    )
    assert isinstance(result.is_correct, bool)
    assert_valid_response(result)


@pytest.mark.asyncio
async def test_chinese_error():
    """Chinese sentence with error (non-Latin script)."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="我昨天去了学校明天。",
            target_language="Chinese",
            native_language="English",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 1
    assert_valid_response(result)


@pytest.mark.asyncio
async def test_explanation_in_native_language():
    """Explanation should be in the native language (Spanish)."""
    result = await get_feedback(
        FeedbackRequest(
            sentence="I goes to school every day.",
            target_language="English",
            native_language="Spanish",
        )
    )
    assert result.is_correct is False
    assert len(result.errors) >= 1
    assert_valid_response(result)