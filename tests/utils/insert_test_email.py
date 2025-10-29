"""
Insert Test Email for Integration Testing
Creates a test email quotation request in the database
NO MOCK - Inserts real record into production database
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


async def insert_test_email(sender_email: str = None, body_text: str = None):
    """Insert a test email quotation request"""

    print("="*70)
    print("INSERT TEST EMAIL FOR INTEGRATION TESTING")
    print("="*70)
    print()

    # Get database connection
    DATABASE_URL = "postgresql://horme_user:96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42@localhost:5434/horme_db"

    print(f"{BLUE}Step 1: Connecting to database...{RESET}")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print(f"{GREEN}✓ Connected{RESET}")
    except Exception as e:
        print(f"{RED}✗ Database connection failed: {e}{RESET}")
        return None

    print()

    # Default test data
    if not sender_email:
        sender_email = input(f"Enter sender email (or press Enter for test@example.com): ").strip()
        if not sender_email:
            sender_email = "test@example.com"

    if not body_text:
        body_text = """Hello,

We need the following items for our construction project:

1. 50 safety helmets (hard hats)
2. 100 pairs of safety gloves
3. 25 high-visibility safety vests
4. 10 safety harnesses for working at height

Please provide a quotation with pricing and delivery timeline.

Thank you"""

    message_id = f"test-{int(datetime.now().timestamp())}@integration-test.com"

    print(f"{BLUE}Step 2: Inserting test email...{RESET}")
    print(f"  From: {sender_email}")
    print(f"  Subject: Request for Quotation - Integration Test")
    print(f"  Message ID: {message_id}")
    print()

    try:
        email_id = await conn.fetchval("""
            INSERT INTO email_quotation_requests (
                message_id,
                sender_email,
                sender_name,
                subject,
                received_date,
                body_text,
                has_attachments,
                attachment_count,
                status,
                processing_notes
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
            ) RETURNING id
        """,
            message_id,
            sender_email,
            "Integration Test User",
            "Request for Quotation - Integration Test",
            datetime.now(),
            body_text,
            False,  # has_attachments
            0,      # attachment_count
            "pending",
            "TEST RECORD - Created by insert_test_email.py for integration testing"
        )

        print(f"{GREEN}✓ Test email inserted successfully{RESET}")
        print(f"{GREEN}  Email ID: {email_id}{RESET}")
        print()

        # Verify insertion
        print(f"{BLUE}Step 3: Verifying insertion...{RESET}")
        row = await conn.fetchrow("""
            SELECT id, sender_email, subject, status, created_at
            FROM email_quotation_requests
            WHERE id = $1
        """, email_id)

        print(f"{GREEN}✓ Verification successful{RESET}")
        print(f"  ID: {row['id']}")
        print(f"  From: {row['sender_email']}")
        print(f"  Subject: {row['subject']}")
        print(f"  Status: {row['status']}")
        print(f"  Created: {row['created_at']}")
        print()

        print("="*70)
        print(f"{GREEN}NEXT STEPS:{RESET}")
        print("="*70)
        print()
        print(f"1. Trigger processing via API:")
        print(f"   {YELLOW}curl -X POST http://localhost:8002/api/email-quotation-requests/{email_id}/process{RESET}")
        print()
        print(f"2. Check processing status (wait 30-60 seconds first):")
        print(f"   {YELLOW}curl http://localhost:8002/api/email-quotation-requests/{email_id}{RESET}")
        print()
        print(f"3. If quotation created, check quotation details:")
        print(f"   {YELLOW}curl http://localhost:8002/api/quotations/{{quotation_id}}{RESET}")
        print()
        print("="*70)

        await conn.close()
        return email_id

    except Exception as e:
        print(f"{RED}✗ Failed to insert test email: {e}{RESET}")
        await conn.close()
        return None


async def list_test_emails():
    """List all test emails in database"""
    DATABASE_URL = "postgresql://horme_user:96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42@localhost:5434/horme_db"

    conn = await asyncpg.connect(DATABASE_URL)

    rows = await conn.fetch("""
        SELECT
            id,
            sender_email,
            subject,
            status,
            quotation_id,
            ai_confidence_score,
            created_at
        FROM email_quotation_requests
        ORDER BY created_at DESC
        LIMIT 10
    """)

    print("="*70)
    print("RECENT EMAIL QUOTATION REQUESTS")
    print("="*70)
    print()

    if not rows:
        print(f"{YELLOW}No email quotation requests found{RESET}")
    else:
        print(f"Found {len(rows)} recent requests:\n")
        for row in rows:
            status_color = GREEN if row['status'] == 'completed' else YELLOW if row['status'] == 'pending' else RED
            print(f"{BLUE}ID:{RESET} {row['id']}")
            print(f"  From: {row['sender_email']}")
            print(f"  Subject: {row['subject']}")
            print(f"  Status: {status_color}{row['status']}{RESET}")
            if row['quotation_id']:
                print(f"  Quotation: {GREEN}#{row['quotation_id']}{RESET}")
            if row['ai_confidence_score']:
                print(f"  AI Confidence: {float(row['ai_confidence_score']):.2f}")
            print(f"  Created: {row['created_at']}")
            print()

    await conn.close()


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        asyncio.run(list_test_emails())
    else:
        email_id = asyncio.run(insert_test_email())
        if email_id:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
