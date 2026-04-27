"""IMAP/SMTP email operations for warmup accounts."""
import asyncio
import imaplib
import smtplib
import ssl
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid, parseaddr
from typing import Optional
import time
import structlog

from app.core.security import decrypt_secret
from app.models.email_account import EmailAccount

logger = structlog.get_logger(__name__)

GMAIL_SMTP = ("smtp.gmail.com", 587)
GMAIL_IMAP = ("imap.gmail.com", 993)
OUTLOOK_SMTP = ("smtp.office365.com", 587)
OUTLOOK_IMAP = ("outlook.office365.com", 993)


def _detect_esp(email_addr: str) -> str:
    domain = email_addr.split("@")[-1].lower()
    google_domains = {"gmail.com", "googlemail.com", "google.com"}
    ms_domains = {"outlook.com", "hotmail.com", "live.com", "msn.com", "office365.com"}
    if domain in google_domains or domain.endswith(".google.com"):
        return "google"
    if domain in ms_domains or domain.endswith(".microsoft.com"):
        return "microsoft"
    return "others"


async def test_smtp_connection(account: EmailAccount) -> tuple[bool, Optional[str]]:
    """Test SMTP connection. Returns (success, error_message)."""
    password = decrypt_secret(account.password_encrypted)
    start = time.monotonic()
    try:
        await asyncio.get_event_loop().run_in_executor(
            None, _test_smtp_sync, account, password
        )
        latency = (time.monotonic() - start) * 1000
        return True, None
    except Exception as e:
        return False, str(e)


def _test_smtp_sync(account: EmailAccount, password: str):
    context = ssl.create_default_context()
    with smtplib.SMTP(account.smtp_host, account.smtp_port, timeout=15) as server:
        if account.smtp_use_tls:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
        server.login(account.username, password)


async def test_imap_connection(account: EmailAccount) -> tuple[bool, Optional[str]]:
    """Test IMAP connection. Returns (success, error_message)."""
    password = decrypt_secret(account.password_encrypted)
    try:
        await asyncio.get_event_loop().run_in_executor(
            None, _test_imap_sync, account, password
        )
        return True, None
    except Exception as e:
        return False, str(e)


def _test_imap_sync(account: EmailAccount, password: str):
    if account.imap_use_ssl:
        mail = imaplib.IMAP4_SSL(account.imap_host, account.imap_port, timeout=15)
    else:
        mail = imaplib.IMAP4(account.imap_host, account.imap_port)
    try:
        mail.login(account.username, password)
    finally:
        mail.logout()


async def send_warmup_email(
    sender: EmailAccount,
    recipient_email: str,
    subject: str,
    body: str,
    in_reply_to: Optional[str] = None,
) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Send a warmup email via SMTP.
    Returns (success, message_id, error).
    """
    password = decrypt_secret(sender.password_encrypted)
    msg_id = make_msgid(domain=sender.email.split("@")[1])

    try:
        message_id = await asyncio.get_event_loop().run_in_executor(
            None,
            _send_smtp_sync,
            sender,
            password,
            recipient_email,
            subject,
            body,
            msg_id,
            in_reply_to,
        )
        return True, message_id, None
    except Exception as e:
        logger.error("smtp_send_failed", account=sender.email, error=str(e))
        return False, None, str(e)


def _send_smtp_sync(
    sender: EmailAccount,
    password: str,
    recipient_email: str,
    subject: str,
    body: str,
    msg_id: str,
    in_reply_to: Optional[str],
) -> str:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender.display_name or sender.email} <{sender.email}>"
    msg["To"] = recipient_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = msg_id
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    msg.attach(MIMEText(body, "plain", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP(sender.smtp_host, sender.smtp_port, timeout=30) as server:
        if sender.smtp_use_tls:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
        server.login(sender.username, password)
        server.sendmail(sender.email, [recipient_email], msg.as_bytes())

    return msg_id


def _get_imap_connection(account: EmailAccount, password: str) -> imaplib.IMAP4:
    if account.imap_use_ssl:
        return imaplib.IMAP4_SSL(account.imap_host, account.imap_port)
    return imaplib.IMAP4(account.imap_host, account.imap_port)


async def check_inbox_for_warmup(
    account: EmailAccount,
    sender_email: str,
    message_id: str,
) -> Optional[str]:
    """
    Check if warmup email arrived in inbox or spam.
    Returns 'inbox', 'spam', 'other', or None if not found.
    """
    password = decrypt_secret(account.password_encrypted)
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            _check_imap_sync,
            account,
            password,
            sender_email,
            message_id,
        )
        return result
    except Exception as e:
        logger.error("imap_check_failed", account=account.email, error=str(e))
        return None


def _check_imap_sync(
    account: EmailAccount,
    password: str,
    sender_email: str,
    message_id: str,
) -> Optional[str]:
    mail = _get_imap_connection(account, password)
    try:
        mail.login(account.username, password)
        folders_to_check = [
            ("INBOX", "inbox"),
            ("[Gmail]/Spam", "spam"),
            ("Junk", "spam"),
            ("Junk Email", "spam"),
            ("[Gmail]/All Mail", "other"),
        ]
        clean_msg_id = message_id.strip("<>")

        for folder, label in folders_to_check:
            try:
                status, _ = mail.select(folder, readonly=False)
                if status != "OK":
                    continue
                _, data = mail.search(None, f'HEADER Message-ID "{clean_msg_id}"')
                if data and data[0]:
                    if label == "spam":
                        # Move from spam to inbox
                        uids = data[0].split()
                        for uid in uids:
                            mail.store(uid, "+FLAGS", "\\Seen")
                            try:
                                mail.copy(uid, "INBOX")
                                mail.store(uid, "+FLAGS", "\\Deleted")
                                mail.expunge()
                            except Exception:
                                pass
                        return "spam_rescued"
                    return label
            except Exception:
                continue
        return None
    finally:
        try:
            mail.logout()
        except Exception:
            pass


async def send_reply(
    account: EmailAccount,
    original_sender_email: str,
    original_subject: str,
    original_message_id: str,
    reply_body: str,
) -> tuple[bool, Optional[str], Optional[str]]:
    """Send a reply to a warmup email."""
    subject = original_subject if original_subject.startswith("Re:") else f"Re: {original_subject}"
    return await send_warmup_email(
        sender=account,
        recipient_email=original_sender_email,
        subject=subject,
        body=reply_body,
        in_reply_to=original_message_id,
    )
