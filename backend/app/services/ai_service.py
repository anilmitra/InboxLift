"""AI-powered email content generation."""
import random
from typing import Optional
import structlog
from app.models.ai_settings import AIProvider
from app.core.security import decrypt_secret

logger = structlog.get_logger(__name__)

EMAIL_TOPICS = [
    "quarterly business review",
    "project timeline update",
    "team collaboration tools",
    "client feedback summary",
    "product roadmap discussion",
    "budget planning",
    "marketing campaign results",
    "partnership opportunity",
    "industry conference highlights",
    "hiring updates",
    "customer success story",
    "technical architecture review",
    "sales pipeline review",
    "onboarding process improvements",
    "remote work best practices",
]

AVAILABLE_MODELS = {
    AIProvider.OPENAI: [
        {"id": "gpt-4o", "name": "GPT-4o", "context_length": 128000, "description": "Most capable OpenAI model"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_length": 128000, "description": "Fast and cost-effective"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_length": 128000, "description": "High capability GPT-4"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_length": 16385, "description": "Fast and affordable"},
    ],
    AIProvider.ANTHROPIC: [
        {"id": "claude-opus-4-7", "name": "Claude Opus 4.7", "context_length": 200000, "description": "Most capable Claude model"},
        {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "context_length": 200000, "description": "Balance of speed and intelligence"},
        {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5", "context_length": 200000, "description": "Fast and compact"},
    ],
}


async def generate_warmup_email(
    topic: Optional[str] = None,
    provider: AIProvider = AIProvider.OPENAI,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    temperature: float = 0.8,
    max_tokens: int = 500,
    encrypted_key: Optional[str] = None,
) -> tuple[str, str]:
    """
    Generate a warmup email subject and body using AI.
    Returns (subject, body).
    Falls back to template if AI unavailable.
    """
    if encrypted_key:
        try:
            api_key = decrypt_secret(encrypted_key)
        except Exception:
            pass

    if not api_key:
        return _generate_template_email(topic)

    selected_topic = topic or random.choice(EMAIL_TOPICS)

    try:
        if provider == AIProvider.OPENAI:
            return await _generate_openai(api_key, model, selected_topic, temperature, max_tokens)
        elif provider == AIProvider.ANTHROPIC:
            return await _generate_anthropic(api_key, model, selected_topic, temperature, max_tokens)
    except Exception as e:
        logger.warning("ai_generation_failed", provider=provider, error=str(e))
        return _generate_template_email(topic)

    return _generate_template_email(topic)


async def _generate_openai(
    api_key: str, model: str, topic: str, temperature: float, max_tokens: int
) -> tuple[str, str]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    prompt = _build_prompt(topic)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional business email writer. "
                    "Write natural, conversational business emails. "
                    "Always respond with SUBJECT: on first line, then blank line, then EMAIL BODY."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    content = response.choices[0].message.content or ""
    return _parse_ai_response(content, topic)


async def _generate_anthropic(
    api_key: str, model: str, topic: str, temperature: float, max_tokens: int
) -> tuple[str, str]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)
    prompt = _build_prompt(topic)

    message = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        system=(
            "You are a professional business email writer. "
            "Write natural, conversational business emails. "
            "Always respond with SUBJECT: on first line, then blank line, then EMAIL BODY."
        ),
    )

    content = message.content[0].text if message.content else ""
    return _parse_ai_response(content, topic)


def _build_prompt(topic: str) -> str:
    length = random.choice(["short (2-3 sentences)", "medium (4-5 sentences)", "detailed (6-8 sentences)"])
    tone = random.choice(["formal", "friendly professional", "casual professional"])
    return (
        f"Write a {tone} business email about: {topic}. "
        f"Length: {length}. "
        "Include a clear subject line. "
        "Make it sound like a real conversation between colleagues. "
        "Do not use placeholders like [Name] or [Company]. "
        "Start with SUBJECT: then the subject line, then a blank line, then the email body."
    )


def _parse_ai_response(content: str, topic: str) -> tuple[str, str]:
    lines = content.strip().split("\n")
    subject = ""
    body_lines = []
    found_subject = False
    in_body = False

    for line in lines:
        if line.upper().startswith("SUBJECT:") and not found_subject:
            subject = line[8:].strip()
            found_subject = True
        elif found_subject and not in_body:
            if line.strip():
                in_body = True
                body_lines.append(line)
        elif in_body:
            body_lines.append(line)

    if not subject:
        subject = f"Re: {topic.title()}"
    body = "\n".join(body_lines).strip()
    if not body:
        _, body = _generate_template_email(topic)
    return subject, body


def _generate_template_email(topic: Optional[str] = None) -> tuple[str, str]:
    """Fallback template-based email generation."""
    chosen_topic = topic or random.choice(EMAIL_TOPICS)
    templates = [
        (
            f"Quick update on {chosen_topic}",
            f"Hi,\n\nI wanted to share a quick update regarding our {chosen_topic}. "
            f"Things are progressing well and I believe we're on track to meet our objectives. "
            f"Let me know if you have any questions or need additional information.\n\nBest regards",
        ),
        (
            f"Follow-up: {chosen_topic.title()}",
            f"Hello,\n\nFollowing up on our recent discussion about {chosen_topic}. "
            f"I've reviewed the details and have a few thoughts I'd like to share with you. "
            f"Could we schedule a brief call this week to align on next steps?\n\nThanks",
        ),
        (
            f"Thoughts on {chosen_topic}",
            f"Hi there,\n\nHope you're doing well! I've been thinking about our {chosen_topic} "
            f"and wanted to get your perspective. Based on what we've discussed, "
            f"I think there might be an opportunity worth exploring. "
            f"Would love to hear your thoughts when you get a chance.\n\nCheers",
        ),
    ]
    return random.choice(templates)


async def generate_reply(
    original_subject: str,
    original_body: str,
    provider: AIProvider = AIProvider.OPENAI,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    encrypted_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 300,
) -> str:
    """Generate a reply to a warmup email."""
    if encrypted_key:
        try:
            api_key = decrypt_secret(encrypted_key)
        except Exception:
            pass

    if not api_key:
        return _generate_template_reply(original_body)

    try:
        prompt = (
            f"Write a brief, natural reply to this email.\n\n"
            f"Subject: {original_subject}\n\n"
            f"Email: {original_body[:500]}\n\n"
            f"Reply (2-4 sentences, conversational, no subject line needed):"
        )
        if provider == AIProvider.OPENAI:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Write natural, brief email replies."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or _generate_template_reply(original_body)
        elif provider == AIProvider.ANTHROPIC:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=api_key)
            message = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text if message.content else _generate_template_reply(original_body)
    except Exception as e:
        logger.warning("ai_reply_failed", error=str(e))

    return _generate_template_reply(original_body)


def _generate_template_reply(original_body: str) -> str:
    replies = [
        "Thanks for the update! This looks great. I'll review and get back to you shortly.",
        "Appreciate you reaching out. I've had a chance to look at this and think it sounds promising.",
        "Thanks for sharing this. I agree with your assessment — let's move forward with the next steps.",
        "Got it, thanks! I'll take a look and circle back with any questions.",
        "This is really helpful context. I'm aligned with the direction you're suggesting.",
    ]
    return random.choice(replies)
