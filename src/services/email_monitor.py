"""
Email Monitoring Service
Polls IMAP server for new RFQ emails and processes them
NO MOCK DATA - All real email connections to webmail.horme.com.sg
"""

import os
import logging
import asyncio
import time
import ssl
from datetime import datetime
from typing import List, Dict, Any, Optional
import email
from email.header import decode_header
from email.message import Message as EmailMessage
import asyncpg
from imapclient import IMAPClient
import structlog

# Configure structured logging
logger = structlog.get_logger()


class EmailMonitor:
    """
    IMAP email monitoring service for quotation requests
    Connects to integrum@horme.com.sg and detects RFQ emails
    """

    # RFQ detection keywords (comprehensive list)
    RFQ_KEYWORDS = [
        "quotation", "quote", "rfq", "rfp",
        "request for quotation", "request for proposal",
        "pricing", "price list", "price quote",
        "estimate", "proposal", "bid", "tender",
        "quotation request", "quote request",
        "need quotation", "need quote", "pls quote"
    ]

    def __init__(self):
        # Email configuration from environment variables (NO HARDCODING)
        self.imap_server = os.getenv("EMAIL_IMAP_SERVER")
        self.imap_port = int(os.getenv("EMAIL_IMAP_PORT", 993))
        self.username = os.getenv("EMAIL_USERNAME")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.use_ssl = os.getenv("EMAIL_USE_SSL", "true").lower() == "true"

        # Validate required configuration
        if not all([self.imap_server, self.username, self.password]):
            raise ValueError(
                "Email configuration incomplete. Required environment variables: "
                "EMAIL_IMAP_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD"
            )

        # Database configuration
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable required")

        self.db_pool: Optional[asyncpg.Pool] = None
        self.imap_client: Optional[IMAPClient] = None

        # Polling configuration
        self.poll_interval = int(os.getenv("EMAIL_POLL_INTERVAL_SECONDS", 300))  # Default 5 minutes
        self.attachment_dir = os.getenv("EMAIL_ATTACHMENT_DIR", "/app/email-attachments")
        self.max_attachment_size = int(os.getenv("EMAIL_MAX_ATTACHMENT_SIZE_MB", 10)) * 1024 * 1024  # 10MB default

        # Ensure attachment directory exists with secure permissions
        os.makedirs(self.attachment_dir, exist_ok=True)
        os.chmod(self.attachment_dir, 0o700)  # Owner read/write/execute only

        logger.info(
            "email_monitor_initialized",
            server=self.imap_server,
            username=self.username,
            poll_interval_seconds=self.poll_interval,
            attachment_dir=self.attachment_dir
        )

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(
                self.db_url,
                min_size=2,
                max_size=5,
                command_timeout=60
            )
            logger.info("database_pool_initialized")
        except Exception as e:
            logger.error("database_initialization_failed", error=str(e))
            raise

    async def cleanup(self):
        """Cleanup resources on shutdown"""
        if self.imap_client:
            try:
                self.imap_client.logout()
                logger.info("imap_client_logged_out")
            except:
                pass

        if self.db_pool:
            await self.db_pool.close()
            logger.info("database_pool_closed")

        logger.info("email_monitor_cleanup_complete")

    def connect_imap(self) -> IMAPClient:
        """
        Connect to IMAP server

        Returns:
            IMAPClient instance

        Raises:
            Exception: If connection fails
        """
        try:
            logger.info(
                "imap_connecting",
                server=self.imap_server,
                port=self.imap_port,
                ssl=self.use_ssl
            )

            # Create SSL context that accepts self-signed certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            client = IMAPClient(
                self.imap_server,
                port=self.imap_port,
                use_uid=True,
                ssl=self.use_ssl,
                ssl_context=ssl_context,
                timeout=30
            )

            client.login(self.username, self.password)
            logger.info("imap_login_successful", username=self.username)

            return client

        except Exception as e:
            logger.error("imap_connection_failed", error=str(e))
            raise

    def is_rfq_email(self, subject: str, body: str) -> bool:
        """
        Check if email is RFQ-related based on keywords

        Args:
            subject: Email subject line
            body: Email body text

        Returns:
            True if email matches RFQ keywords
        """
        text = f"{subject} {body}".lower()
        matched = any(keyword in text for keyword in self.RFQ_KEYWORDS)

        if matched:
            logger.info("rfq_email_detected", subject=subject[:100])
        else:
            logger.debug("non_rfq_email_skipped", subject=subject[:100])

        return matched

    def extract_email_text(self, msg: EmailMessage) -> tuple[str, str]:
        """
        Extract text and HTML body from email message

        Args:
            msg: Email message object

        Returns:
            Tuple of (text_body, html_body)
        """
        text_body = ""
        html_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                try:
                    if content_type == "text/plain":
                        text_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    elif content_type == "text/html":
                        html_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                except:
                    continue
        else:
            try:
                text_body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except:
                pass

        return text_body, html_body

    def decode_email_header(self, header: str) -> str:
        """
        Decode email header (handles encoded subjects, names, etc.)

        Args:
            header: Raw email header string

        Returns:
            Decoded header string
        """
        if not header:
            return ""

        try:
            decoded = decode_header(header)
            result = []
            for text, encoding in decoded:
                if isinstance(text, bytes):
                    result.append(text.decode(encoding or "utf-8", errors="ignore"))
                else:
                    result.append(str(text))
            return " ".join(result)
        except:
            return str(header)

    async def save_attachment(
        self,
        part: EmailMessage,
        email_request_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Save email attachment to disk and database

        Args:
            part: Email message part containing attachment
            email_request_id: ID of email quotation request

        Returns:
            Attachment metadata dict or None if failed
        """
        filename = part.get_filename()
        if not filename:
            return None

        # Sanitize filename (security: prevent directory traversal)
        filename = os.path.basename(filename)
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")

        if not filename:
            filename = "attachment"

        # Generate unique filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(self.attachment_dir, safe_filename)

        try:
            # Get attachment content
            payload = part.get_payload(decode=True)
            if not payload:
                logger.warning("attachment_empty", filename=filename)
                return None

            file_size = len(payload)

            # Check size limit
            if file_size > self.max_attachment_size:
                logger.warning(
                    "attachment_too_large",
                    filename=filename,
                    size_mb=file_size / (1024 * 1024),
                    max_mb=self.max_attachment_size / (1024 * 1024)
                )
                return None

            # Save file with secure permissions
            with open(file_path, "wb") as f:
                f.write(payload)
            os.chmod(file_path, 0o600)  # Owner read/write only

            mime_type = part.get_content_type()

            # Insert into database
            async with self.db_pool.acquire() as conn:
                attachment_id = await conn.fetchval("""
                    INSERT INTO email_attachments (
                        email_request_id, filename, file_path, file_size, mime_type
                    ) VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                """, email_request_id, filename, file_path, file_size, mime_type)

            logger.info(
                "attachment_saved",
                attachment_id=attachment_id,
                filename=filename,
                size_bytes=file_size,
                mime_type=mime_type
            )

            return {
                "id": attachment_id,
                "filename": filename,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": mime_type
            }

        except Exception as e:
            logger.error("attachment_save_failed", filename=filename, error=str(e))
            # Clean up file if created
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            return None

    async def process_email(
        self,
        msg_id: int,
        msg: EmailMessage
    ) -> Optional[int]:
        """
        Process a single email message

        Args:
            msg_id: IMAP message ID
            msg: Email message object

        Returns:
            Created email_quotation_requests ID or None if skipped
        """
        try:
            # Extract headers
            message_id = msg.get("Message-ID", f"<generated-{msg_id}-{int(time.time())}>")
            subject = self.decode_email_header(msg.get("Subject", ""))
            from_header = self.decode_email_header(msg.get("From", ""))
            date_str = msg.get("Date", "")

            # Parse sender
            sender_email = email.utils.parseaddr(from_header)[1]
            sender_name = email.utils.parseaddr(from_header)[0]

            # Parse date
            try:
                received_date = email.utils.parsedate_to_datetime(date_str)
            except:
                received_date = datetime.utcnow()

            # Extract body
            text_body, html_body = self.extract_email_text(msg)

            # Check if RFQ email
            if not self.is_rfq_email(subject, text_body):
                logger.info(
                    "email_skipped_not_rfq",
                    subject=subject[:100],
                    sender=sender_email
                )
                return None

            logger.info(
                "processing_rfq_email",
                subject=subject[:100],
                sender=sender_email,
                received_date=received_date.isoformat()
            )

            # Check for duplicate (by Message-ID)
            async with self.db_pool.acquire() as conn:
                existing = await conn.fetchval("""
                    SELECT id FROM email_quotation_requests WHERE message_id = $1
                """, message_id)

                if existing:
                    logger.info(
                        "duplicate_email_skipped",
                        message_id=message_id,
                        existing_id=existing
                    )
                    return None

                # Count attachments
                attachment_count = 0
                has_attachments = False
                for part in msg.walk():
                    if part.get_filename():
                        attachment_count += 1
                        has_attachments = True

                # Insert email request
                email_request_id = await conn.fetchval("""
                    INSERT INTO email_quotation_requests (
                        message_id, sender_email, sender_name, subject, received_date,
                        body_text, body_html, has_attachments, attachment_count, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                """, message_id, sender_email, sender_name, subject, received_date,
                    text_body, html_body, has_attachments, attachment_count, "pending")

            logger.info(
                "email_request_created",
                email_request_id=email_request_id,
                sender=sender_email,
                attachments=attachment_count
            )

            # Save attachments
            saved_attachments = 0
            for part in msg.walk():
                if part.get_filename():
                    attachment = await self.save_attachment(part, email_request_id)
                    if attachment:
                        saved_attachments += 1

            logger.info(
                "attachments_saved",
                email_request_id=email_request_id,
                total=attachment_count,
                saved=saved_attachments
            )

            # Trigger background processing
            from src.services.email_processor import EmailProcessor
            email_processor = EmailProcessor()

            # Create async task (don't await - run in background)
            asyncio.create_task(
                email_processor.process_email_request(email_request_id, self.db_pool)
            )

            logger.info(
                "email_processing_started",
                email_request_id=email_request_id
            )

            return email_request_id

        except Exception as e:
            logger.error(
                "email_processing_failed",
                msg_id=msg_id,
                error=str(e),
                exc_info=True
            )
            return None

    async def poll_emails(self):
        """
        Poll IMAP server for new emails
        Main polling logic - runs every poll_interval seconds
        """
        try:
            # Connect to IMAP if not connected
            if not self.imap_client:
                self.imap_client = self.connect_imap()
            else:
                # Check connection health
                try:
                    self.imap_client.noop()
                except:
                    logger.warning("imap_reconnecting")
                    self.imap_client = self.connect_imap()

            # Select INBOX
            self.imap_client.select_folder("INBOX")

            # Search for UNSEEN emails
            messages = self.imap_client.search(["UNSEEN"])

            if not messages:
                logger.debug("no_new_emails")
                return

            logger.info("new_emails_found", count=len(messages))

            # Fetch emails
            email_data = self.imap_client.fetch(messages, ["RFC822"])

            processed_count = 0
            skipped_count = 0

            for msg_id, data in email_data.items():
                msg = email.message_from_bytes(data[b"RFC822"])
                result = await self.process_email(msg_id, msg)

                if result:
                    processed_count += 1
                else:
                    skipped_count += 1

            logger.info(
                "email_poll_complete",
                total=len(messages),
                processed=processed_count,
                skipped=skipped_count
            )

        except Exception as e:
            logger.error("email_poll_failed", error=str(e), exc_info=True)
            # Try to reconnect on next poll
            self.imap_client = None

    async def run(self):
        """
        Main monitoring loop
        Runs continuously until interrupted
        """
        logger.info("email_monitor_service_starting")

        await self.initialize()

        retry_count = 0
        max_retries = 5
        retry_delay = 60  # seconds

        try:
            while True:
                try:
                    start_time = time.time()

                    await self.poll_emails()

                    # Reset retry count on successful poll
                    retry_count = 0

                    elapsed = time.time() - start_time
                    sleep_time = max(0, self.poll_interval - elapsed)

                    logger.info(
                        "next_poll_scheduled",
                        sleep_seconds=int(sleep_time)
                    )
                    await asyncio.sleep(sleep_time)

                except Exception as e:
                    retry_count += 1
                    logger.error(
                        "poll_cycle_failed",
                        error=str(e),
                        retry_count=retry_count,
                        max_retries=max_retries
                    )

                    if retry_count >= max_retries:
                        logger.critical("max_retries_exceeded")
                        raise

                    logger.info(f"retrying_in_{retry_delay}_seconds")
                    await asyncio.sleep(retry_delay)

        except KeyboardInterrupt:
            logger.info("email_monitor_stopped_by_user")
        except Exception as e:
            logger.critical("email_monitor_crashed", error=str(e), exc_info=True)
            raise
        finally:
            await self.cleanup()


# Entry point for standalone execution
if __name__ == "__main__":
    import sys

    # Configure logging for standalone mode
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("/app/logs/email-monitor.log", mode="a")
        ]
    )

    # Create monitor instance and run
    monitor = EmailMonitor()

    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\nEmail monitor stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Email monitor crashed: {e}")
        sys.exit(1)
