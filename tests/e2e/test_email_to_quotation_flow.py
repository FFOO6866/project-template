"""
End-to-End Integration Test: Email to Quotation Flow
Tests complete pipeline from email detection to quotation generation
NO MOCK - Tests with real IMAP, real database, real OpenAI API
"""

import os
import sys
import time
import asyncio
import asyncpg
from datetime import datetime
from typing import Optional

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class E2ETestResult:
    """Track test results"""
    def __init__(self):
        self.email_detected = False
        self.email_saved = False
        self.processing_triggered = False
        self.requirements_extracted = False
        self.products_matched = False
        self.quotation_created = False
        self.pdf_generated = False
        self.frontend_displayed = False

        self.email_request_id: Optional[int] = None
        self.quotation_id: Optional[int] = None
        self.errors: list = []


async def wait_for_email_detection(
    db_pool: asyncpg.Pool,
    test_email: str,
    max_wait_seconds: int = 360  # 6 minutes (1 poll + buffer)
) -> Optional[int]:
    """Wait for email to be detected and saved to database"""
    print(f"Waiting up to {max_wait_seconds}s for email detection...")
    print(f"Looking for: {test_email}")

    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        async with db_pool.acquire() as conn:
            email_id = await conn.fetchval("""
                SELECT id FROM email_quotation_requests
                WHERE sender_email = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, test_email)

            if email_id:
                return email_id

        # Wait 10 seconds before checking again
        await asyncio.sleep(10)
        elapsed = int(time.time() - start_time)
        print(f"  ... waiting ({elapsed}s elapsed)")

    return None


async def check_processing_complete(
    db_pool: asyncpg.Pool,
    email_request_id: int,
    max_wait_seconds: int = 120
) -> bool:
    """Wait for AI processing to complete"""
    print(f"Waiting up to {max_wait_seconds}s for AI processing...")

    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT status, extracted_requirements, ai_confidence_score
                FROM email_quotation_requests
                WHERE id = $1
            """, email_request_id)

            if not row:
                return False

            status = row['status']

            if status == 'completed':
                print(f"{GREEN}✓ AI processing completed{RESET}")
                if row['extracted_requirements']:
                    print(f"{GREEN}✓ Requirements extracted{RESET}")
                if row['ai_confidence_score']:
                    print(f"{GREEN}✓ Confidence score: {float(row['ai_confidence_score']):.2f}{RESET}")
                return True

            if status == 'failed':
                print(f"{RED}✗ Processing failed{RESET}")
                return False

        await asyncio.sleep(5)
        elapsed = int(time.time() - start_time)
        print(f"  ... processing ({elapsed}s elapsed, status: {status})")

    return False


async def check_quotation_created(
    db_pool: asyncpg.Pool,
    email_request_id: int,
    max_wait_seconds: int = 180
) -> Optional[int]:
    """Wait for quotation to be created"""
    print(f"Waiting up to {max_wait_seconds}s for quotation generation...")

    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        async with db_pool.acquire() as conn:
            quotation_id = await conn.fetchval("""
                SELECT quotation_id FROM email_quotation_requests
                WHERE id = $1 AND quotation_id IS NOT NULL
            """, email_request_id)

            if quotation_id:
                # Check quotation details
                quote = await conn.fetchrow("""
                    SELECT quote_number, total_amount, pdf_path, status
                    FROM quotes
                    WHERE id = $1
                """, quotation_id)

                if quote:
                    print(f"{GREEN}✓ Quotation created: {quote['quote_number']}{RESET}")
                    print(f"  Total: SGD {float(quote['total_amount']):.2f}")
                    print(f"  Status: {quote['status']}")
                    if quote['pdf_path']:
                        print(f"  PDF: {quote['pdf_path']}")

                return quotation_id

        await asyncio.sleep(5)
        elapsed = int(time.time() - start_time)
        print(f"  ... waiting for quotation ({elapsed}s elapsed)")

    return None


async def run_e2e_test(test_email: str) -> E2ETestResult:
    """Run complete end-to-end test"""
    result = E2ETestResult()

    print("=" * 70)
    print("END-TO-END INTEGRATION TEST")
    print("Email to Quotation Complete Flow")
    print("=" * 70)
    print()

    # Connect to database
    print("Step 1: Connecting to database...")
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print(f"{RED}✗ DATABASE_URL not set{RESET}")
        result.errors.append("DATABASE_URL not set")
        return result

    try:
        db_pool = await asyncpg.create_pool(database_url)
        print(f"{GREEN}✓ Connected to database{RESET}")
    except Exception as e:
        print(f"{RED}✗ Database connection failed: {e}{RESET}")
        result.errors.append(f"Database connection: {e}")
        return result

    print()

    try:
        # Step 2: Wait for email detection
        print("Step 2: Waiting for email to be detected by monitor...")
        print(f"{YELLOW}ACTION REQUIRED:{RESET} Send test email to integrum@horme.com.sg")
        print(f"  From: {test_email}")
        print(f"  Subject: Request for Quotation - E2E Test")
        print(f"  Body: We need 10 safety helmets and 20 safety vests")
        print()
        input(f"Press Enter after sending the email...")
        print()

        email_id = await wait_for_email_detection(db_pool, test_email, max_wait_seconds=360)

        if not email_id:
            print(f"{RED}✗ Email not detected after 6 minutes{RESET}")
            print("Check:")
            print("  1. Email monitor service is running")
            print("  2. Email was sent to correct address")
            print("  3. Email contains RFQ keywords")
            result.errors.append("Email not detected")
            return result

        print(f"{GREEN}✓ Email detected (ID: {email_id}){RESET}")
        result.email_detected = True
        result.email_saved = True
        result.email_request_id = email_id
        print()

        # Step 3: Check email was saved correctly
        print("Step 3: Verifying email data...")
        async with db_pool.acquire() as conn:
            email_data = await conn.fetchrow("""
                SELECT sender_email, subject, body_text, status, attachment_count
                FROM email_quotation_requests
                WHERE id = $1
            """, email_id)

            print(f"{GREEN}✓ Email data saved{RESET}")
            print(f"  From: {email_data['sender_email']}")
            print(f"  Subject: {email_data['subject']}")
            print(f"  Status: {email_data['status']}")
            print(f"  Attachments: {email_data['attachment_count']}")

        print()

        # Step 4: Trigger processing via API
        print("Step 4: Triggering quotation processing...")
        print(f"{YELLOW}ACTION REQUIRED:{RESET} Call API endpoint:")
        print(f"  POST http://localhost:8000/api/email-quotation-requests/{email_id}/process")
        print()
        print("You can use:")
        print(f"  curl -X POST http://localhost:8000/api/email-quotation-requests/{email_id}/process")
        print()
        input("Press Enter after triggering the API...")
        result.processing_triggered = True
        print()

        # Step 5: Wait for AI processing
        print("Step 5: Waiting for AI requirement extraction...")
        if await check_processing_complete(db_pool, email_id, max_wait_seconds=120):
            result.requirements_extracted = True
        else:
            print(f"{RED}✗ AI processing did not complete{RESET}")
            result.errors.append("AI processing timeout")
            return result

        print()

        # Step 6: Wait for quotation creation
        print("Step 6: Waiting for quotation generation...")
        quotation_id = await check_quotation_created(db_pool, email_id, max_wait_seconds=180)

        if not quotation_id:
            print(f"{RED}✗ Quotation not created{RESET}")
            result.errors.append("Quotation generation timeout")
            return result

        result.quotation_created = True
        result.quotation_id = quotation_id
        print()

        # Step 7: Verify quotation details
        print("Step 7: Verifying quotation details...")
        async with db_pool.acquire() as conn:
            # Get quotation items
            items = await conn.fetch("""
                SELECT product_name, quantity, unit_price, line_total
                FROM quote_items
                WHERE quote_id = $1
                ORDER BY line_number
            """, quotation_id)

            print(f"{GREEN}✓ Quotation has {len(items)} line items:{RESET}")
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item['product_name']}")
                print(f"     Qty: {item['quantity']}, Price: ${float(item['unit_price']):.2f}, Total: ${float(item['line_total']):.2f}")

            result.products_matched = len(items) > 0

        print()

        # Step 8: Check PDF generation
        print("Step 8: Checking PDF generation...")
        async with db_pool.acquire() as conn:
            pdf_path = await conn.fetchval("""
                SELECT pdf_path FROM quotes WHERE id = $1
            """, quotation_id)

            if pdf_path and os.path.exists(pdf_path):
                print(f"{GREEN}✓ PDF generated: {pdf_path}{RESET}")
                result.pdf_generated = True
            else:
                print(f"{YELLOW}⊘ PDF not found or not generated{RESET}")

        print()

        # Step 9: Frontend verification
        print("Step 9: Frontend verification...")
        print(f"{YELLOW}ACTION REQUIRED:{RESET} Check frontend:")
        print(f"  1. Open http://localhost:3000")
        print(f"  2. Check if email request appears in 'New Quotation Requests'")
        print(f"  3. Click on the request")
        print(f"  4. Verify 'View Quotation' button appears")
        print(f"  5. Click 'View Quotation' and verify PDF opens")
        print()
        frontend_ok = input("Did frontend work correctly? (y/n): ").lower().strip() == 'y'

        if frontend_ok:
            result.frontend_displayed = True
            print(f"{GREEN}✓ Frontend verification passed{RESET}")
        else:
            print(f"{YELLOW}⊘ Frontend verification skipped or failed{RESET}")

        print()

        # Final summary
        print("=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)

        checks = [
            ("Email Detection", result.email_detected),
            ("Email Saved to Database", result.email_saved),
            ("Processing Triggered", result.processing_triggered),
            ("AI Requirements Extracted", result.requirements_extracted),
            ("Products Matched", result.products_matched),
            ("Quotation Created", result.quotation_created),
            ("PDF Generated", result.pdf_generated),
            ("Frontend Displayed", result.frontend_displayed),
        ]

        passed_count = sum(1 for _, passed in checks if passed)
        total_count = len(checks)

        for check_name, passed in checks:
            symbol = GREEN + "✓" if passed else RED + "✗"
            print(f"{symbol} {check_name}{RESET}")

        print()
        print(f"Result: {passed_count}/{total_count} checks passed")

        if passed_count == total_count:
            print(f"{GREEN}✓ E2E TEST PASSED{RESET}")
        elif passed_count >= total_count - 1:
            print(f"{YELLOW}⊘ E2E TEST MOSTLY PASSED (minor issues){RESET}")
        else:
            print(f"{RED}✗ E2E TEST FAILED{RESET}")

        if result.errors:
            print()
            print("Errors encountered:")
            for error in result.errors:
                print(f"  - {error}")

        print("=" * 70)

        return result

    finally:
        await db_pool.close()


def main():
    """Main test runner"""
    print()
    print("This test requires manual actions:")
    print("  1. Email monitor service must be running")
    print("  2. API service must be running")
    print("  3. Frontend must be running")
    print("  4. You must send a test email when prompted")
    print("  5. You must trigger API endpoint when prompted")
    print()

    test_email = input("Enter your test email address (sender): ").strip()

    if not test_email or '@' not in test_email:
        print(f"{RED}✗ Invalid email address{RESET}")
        return 1

    try:
        result = asyncio.run(run_e2e_test(test_email))

        if result.quotation_created:
            return 0
        else:
            return 1

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{RESET}")
        return 1
    except Exception as e:
        print(f"\n{RED}✗ Test failed with exception: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
