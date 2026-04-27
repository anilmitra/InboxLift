"""Tests for AI email generation service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ai_service import (
    generate_warmup_email,
    generate_reply,
    _generate_template_email,
    _generate_template_reply,
    _parse_ai_response,
    AVAILABLE_MODELS,
)
from app.models.ai_settings import AIProvider


class TestTemplateGeneration:
    def test_template_email_returns_tuple(self):
        subject, body = _generate_template_email()
        assert isinstance(subject, str)
        assert isinstance(body, str)
        assert len(subject) > 0
        assert len(body) > 0

    def test_template_with_topic(self):
        subject, body = _generate_template_email("quarterly review")
        assert isinstance(subject, str)
        assert isinstance(body, str)

    def test_template_reply(self):
        reply = _generate_template_reply("some email body")
        assert isinstance(reply, str)
        assert len(reply) > 0

    def test_parse_ai_response_with_subject(self):
        response = "SUBJECT: Test Subject\n\nThis is the email body."
        subject, body = _parse_ai_response(response, "test")
        assert subject == "Test Subject"
        assert body == "This is the email body."

    def test_parse_ai_response_no_subject(self):
        response = "No subject line here just body text"
        subject, body = _parse_ai_response(response, "test topic")
        assert subject == "Re: Test Topic"

    def test_available_models_not_empty(self):
        assert len(AVAILABLE_MODELS) > 0
        assert AIProvider.OPENAI in AVAILABLE_MODELS
        assert AIProvider.ANTHROPIC in AVAILABLE_MODELS
        for models in AVAILABLE_MODELS.values():
            assert len(models) > 0


@pytest.mark.asyncio
async def test_generate_email_no_api_key():
    """Without API key, should return template email."""
    subject, body = await generate_warmup_email(api_key=None)
    assert isinstance(subject, str)
    assert isinstance(body, str)
    assert len(subject) > 0
    assert len(body) > 0


@pytest.mark.asyncio
async def test_generate_email_with_openai():
    """Test OpenAI generation with mocked client."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "SUBJECT: Test Email\n\nThis is the test body."

    with patch("app.services.ai_service._generate_openai", new_callable=AsyncMock) as mock:
        mock.return_value = ("Test Email", "This is the test body.")
        subject, body = await generate_warmup_email(
            api_key="sk-test",
            provider=AIProvider.OPENAI,
            model="gpt-4o-mini",
        )
        assert subject == "Test Email"
        assert body == "This is the test body."


@pytest.mark.asyncio
async def test_generate_reply_no_api_key():
    """Without API key, should return template reply."""
    reply = await generate_reply(
        original_subject="Test Subject",
        original_body="Original body",
        api_key=None,
    )
    assert isinstance(reply, str)
    assert len(reply) > 0


@pytest.mark.asyncio
async def test_generate_email_ai_failure_fallback():
    """On AI failure, should fall back to template."""
    with patch("app.services.ai_service._generate_openai", new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("API error")
        subject, body = await generate_warmup_email(
            api_key="sk-test",
            provider=AIProvider.OPENAI,
        )
        assert isinstance(subject, str)
        assert isinstance(body, str)
